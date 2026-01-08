"""Common classes and functions for Zoom."""
from __future__ import annotations

from datetime import timedelta
import hashlib
import hmac
from http import HTTPStatus
from logging import getLogger
import time
from typing import Any

from aiohttp.web import Request, Response, json_response
from homeassistant.components.http.view import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.network import NoURLAvailableError, get_url
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ZoomAPI
from .const import (
    ATTR_EVENT,
    ATTR_PAYLOAD,
    CONF_SECRET_TOKEN,
    DOMAIN,
    HA_URL,
    HA_ZOOM_EVENT,
    VALIDATION_EVENT,
    WEBHOOK_RESPONSE_SCHEMA,
)

_LOGGER = getLogger(__name__)

UNKNOWN_EVENT_MSG = "Received data that doesn't look like a Zoom webhook event"
# Maximum age for webhook timestamps (5 minutes) to prevent replay attacks
WEBHOOK_TIMESTAMP_MAX_AGE_SECONDS = 300


def valid_external_url(hass: HomeAssistant) -> bool:
    """Return whether a valid external URL for HA is available."""
    try:
        get_url(hass, allow_internal=False, prefer_cloud=True)
        return True
    except NoURLAvailableError:
        _LOGGER.error(
            "You do not have an external URL for your Home Assistant instance "
            "configured which is needed to set up the Zoom integration. "
            "You need to set the `external_url` property in the "
            "`homeassistant` section of your `configuration.yaml`, or set the "
            "`External URL` property in the Home Assistant `General "
            "Configuration` UI, before trying to setup the Zoom integration "
            "again. You can learn more about configuring this parameter at "
            "https://www.home-assistant.io/docs/configuration/basic"
        )
        return False


def get_contact_name(contact: dict) -> str:
    """Determine contact name from available first name, last naame, and email."""
    contact_name = ""
    if contact["first_name"]:
        contact_name = f"{contact['first_name']} "
    if contact["last_name"]:
        contact_name += f"{contact['last_name']} "

    if contact_name:
        return f"{contact_name}({contact['email']})"
    return contact["email"]


class ZoomOAuth2Implementation(config_entry_oauth2_flow.LocalOAuth2Implementation):
    """Oauth2 implementation that only uses the external url."""

    def __init__(
        self,
        hass: HomeAssistant,
        domain: str,
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
        secret_token: str | None,
        name: str,
    ) -> None:
        """Initialize local auth implementation."""
        self._secret_token = secret_token
        self._name = name
        super().__init__(
            hass, domain, client_id, client_secret, authorize_url, token_url
        )

    @property
    def name(self) -> str:
        """Name of the implementation."""
        return self._name

    @property
    def domain(self) -> str:
        """Domain of the implementation."""
        return self._name

    @property
    def redirect_uri(self) -> str:
        """Return the redirect uri."""
        url = get_url(self.hass, allow_internal=False, prefer_cloud=True)
        return f"{url}{config_entry_oauth2_flow.AUTH_CALLBACK_PATH}"


def _get_hashed_hex_msg(key: str, message: str) -> str:
    """Generate a HMAC hashed message in hex for a Zoom webhook request."""
    hmac_ = hmac.new(key.encode(), message.encode(), hashlib.sha256)
    return hmac_.hexdigest()


def _find_entry_with_signature(
    hass: HomeAssistant, signature: str, signature_msg: str
) -> tuple[ConfigEntry | None, str | None]:
    """Find config entry with signature if it exists."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        secret_token = entry.data.get(CONF_SECRET_TOKEN)
        if secret_token and hmac.compare_digest(
            f"v0={_get_hashed_hex_msg(str(secret_token), signature_msg)}", signature
        ):
            return entry, str(secret_token)
    return None, None


class ZoomWebhookRequestView(HomeAssistantView):
    """Provide a page for the device to call."""

    requires_auth = False
    cors_allowed = True
    url = HA_URL
    name = HA_URL[1:].replace("/", ":")

    async def post(self, request: Request) -> Response:
        """Respond to requests from the device."""
        text = await request.text()
        hass: HomeAssistant = request.app["hass"]
        headers = request.headers

        _LOGGER.debug(
            "Webhook request received: %s (Headers: %s)", text, dict(headers)
        )

        # If either Zoom header is missing, this is not a valid webhook request
        if not (
            (signature := headers.get("x-zm-signature"))
            and (timestamp := headers.get("x-zm-request-timestamp"))
        ):
            _LOGGER.info("%s: %s (Headers: %s)", UNKNOWN_EVENT_MSG, text, headers)
            return Response(status=HTTPStatus.OK)

        _LOGGER.debug("Zoom headers present, validating timestamp")

        # Validate timestamp freshness to prevent replay attacks
        try:
            request_time = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - request_time) > WEBHOOK_TIMESTAMP_MAX_AGE_SECONDS:
                _LOGGER.warning(
                    "Received Zoom webhook request with stale timestamp "
                    "(request: %s, current: %s, max_age: %s)",
                    request_time,
                    current_time,
                    WEBHOOK_TIMESTAMP_MAX_AGE_SECONDS,
                )
                return Response(status=HTTPStatus.OK)
        except ValueError:
            _LOGGER.warning(
                "Received Zoom webhook request with invalid timestamp: %s", timestamp
            )
            return Response(status=HTTPStatus.OK)

        _LOGGER.debug("Timestamp valid, parsing JSON payload")

        try:
            data = await request.json()
        except Exception as err:
            _LOGGER.info(
                "%s: %s (Headers: %s) (Error: %s)",
                UNKNOWN_EVENT_MSG,
                text,
                headers,
                err,
            )
            return Response(status=HTTPStatus.OK)

        try:
            status = WEBHOOK_RESPONSE_SCHEMA(data)
        except Exception as err:
            _LOGGER.info(
                "%s: %s (Headers: %s) (Error: %s)",
                UNKNOWN_EVENT_MSG,
                text,
                headers,
                err,
            )
            return Response(status=HTTPStatus.OK)

        event_type = status.get(ATTR_EVENT, "unknown")
        _LOGGER.debug(
            "Payload validated (event: %s), verifying signature against config entries",
            event_type,
        )

        # Find the first config entry where the secret token can be used to
        # match the signature header from the webhook validation request
        entry, secret_token = _find_entry_with_signature(
            hass, signature, f"v0:{timestamp}:{text}"
        )

        # This means that we do not have a config entry with the correct secret token
        if not entry:
            # if we get here, there was no found config entry with a matching secret
            # token and we have to fail the validation request. We still respond with
            # a 200 status code so we don't leak information about this endpoint.
            num_entries = len(hass.config_entries.async_entries(DOMAIN))
            _LOGGER.warning(
                "Received Zoom webhook request (event: %s) that doesn't match any "
                "of the %s configured secret token(s)",
                event_type,
                num_entries,
            )
            return Response(status=HTTPStatus.OK)
        assert secret_token

        _LOGGER.debug(
            "Signature verified for config entry %s (user: %s)",
            entry.entry_id,
            entry.title,
        )

        # Pass events that are not webhook validation requests on to the integration
        if event_type != VALIDATION_EVENT:
            _LOGGER.debug(
                "Firing event %s for %s: %s",
                HA_ZOOM_EVENT,
                entry.title,
                status,
            )
            hass.bus.async_fire(
                f"{HA_ZOOM_EVENT}", {**status, "ha_config_entry_id": entry.entry_id}
            )
            return Response(status=HTTPStatus.OK)

        # Handle webhook validation request
        payload = status.get(ATTR_PAYLOAD) or {}
        plain_token = payload.get("plainToken")
        if not isinstance(plain_token, str) or not plain_token:
            _LOGGER.warning(
                "Received Zoom webhook validation request with missing or invalid "
                "plainToken: %s (Headers: %s)",
                text,
                headers,
            )
            return Response(status=HTTPStatus.OK)

        _LOGGER.debug(
            "Responding to webhook validation request for %s",
            entry.title,
        )
        return json_response(
            {
                "plainToken": plain_token,
                "encryptedToken": _get_hashed_hex_msg(secret_token, plain_token),
            }
        )


class ZoomUserProfileDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to hold Zoom user profile data."""

    def __init__(self, hass: HomeAssistant, api: ZoomAPI) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(days=1),
            update_method=self._async_update_data,
        )
        self._api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            return await self._api.async_get_my_user_profile()
        except Exception as err:
            raise UpdateFailed(f"Error fetching user profile: {err}") from err


class ZoomContactListDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to hold Zoom contact list data."""

    def __init__(
        self, hass: HomeAssistant, api: ZoomAPI, contact_types: list[str] = ["external"]
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),
            update_method=self._async_update_data,
        )
        self._api = api
        self._contact_types = contact_types

    async def _async_update_data(self) -> list[dict[str, str]]:
        """Update data via library."""
        try:
            return await self._api.async_get_contacts(self._contact_types)
        except Exception as err:
            raise UpdateFailed(f"Error fetching contacts: {err}") from err
