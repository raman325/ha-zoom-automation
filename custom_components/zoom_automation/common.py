"""Common classes and functions for Zoom."""
from datetime import timedelta
import json
from logging import getLogger
from typing import Any, Dict

from aiohttp.web import Request, Response
from homeassistant.components.http.view import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, HTTP_OK
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.network import get_url
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import slugify

from .api import ZoomAPI
from .const import DEFAULT_NAME, DOMAIN, HA_URL, HA_ZOOM_EVENT, WEBHOOK_RESPONSE_SCHEMA

_LOGGER = getLogger(__name__)


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
        verification_token: str,
    ):
        """Initialize local auth implementation."""
        self._verification_token = verification_token
        super().__init__(
            hass, domain, client_id, client_secret, authorize_url, token_url
        )

    @property
    def name(self) -> str:
        """Name of the implementation."""
        return DEFAULT_NAME

    @property
    def domain(self) -> str:
        """Domain of the implementation."""
        return self._domain

    @property
    def redirect_uri(self) -> str:
        """Return the redirect uri."""
        url = get_url(self.hass, allow_internal=False, prefer_cloud=True)
        return f"{url}{config_entry_oauth2_flow.AUTH_CALLBACK_PATH}"


class ZoomBaseEntity(Entity):
    """Base class for a Zoom automation entity."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize class."""
        self._config_entry = config_entry
        self._hass = hass
        self._coordinator: ZoomDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]
        self._name: str = config_entry.data[CONF_NAME]
        self._async_unsub_listeners = []

    async def async_update(self) -> None:
        """Request coordinator update."""
        await self._coordinator.async_request_refresh()

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        await super().async_added_to_hass()

        @callback
        def profile_update():
            """Update profile."""
            self.async_write_ha_state()

        self._async_unsub_listeners.append(
            self._coordinator.async_add_listener(profile_update)
        )

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect callbacks when entity is removed."""
        await super().async_will_remove_from_hass()

        for listener in self._async_unsub_listeners:
            listener()

        self._async_unsub_listeners.clear()

    @property
    def unique_id(self):
        """Return unique_id for entity."""
        return f"{DOMAIN}_{slugify(self._name)}"


class ZoomWebhookRequestView(HomeAssistantView):
    """Provide a page for the device to call."""

    requires_auth = False
    core_allowed = True
    url = HA_URL
    name = HA_URL[1:].replace("/", ":")

    def __init__(self, verification_token: str) -> None:
        """Initialize view."""
        self._verification_token = verification_token

    async def post(self, request: Request):
        """Respond to requests from the device."""
        hass = request.app["hass"]
        headers = request.headers

        if (
            "authorization" not in headers
            or headers["authorization"] != self._verification_token
        ):
            _LOGGER.warning(
                "Unauthorized request received: %s (Headers: %s)",
                await request.text(),
                json.dumps(request.headers),
            )
            return Response(status=HTTP_OK)

        try:
            data = await request.json()
            status = WEBHOOK_RESPONSE_SCHEMA(data)
            _LOGGER.debug("Received well-formed event: %s", json.dumps(status))
            hass.bus.async_fire(HA_ZOOM_EVENT, status)
        except:
            _LOGGER.warning("Received unknown event: %s", await request.text())

        return Response(status=HTTP_OK)


class ZoomDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to hold Vizio app config data."""

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

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        try:
            return await self._api.async_get_user_profile()
        except:
            raise UpdateFailed
