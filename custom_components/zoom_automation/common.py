"""Common classes and functions for Zoom Automation."""
import json
from logging import getLogger

from aiohttp.web import Request, Response
from homeassistant.components.http.view import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, HTTP_OK
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.network import get_url
from homeassistant.util import slugify

from .api import ZoomAPI
from .const import (
    DEFAULT_NAME,
    DOMAIN,
    HA_OCCUPANCY_EVENT,
    HA_URL,
    WEBHOOK_RESPONSE_SCHEMA,
)

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
            hass, domain, client_id, client_secret, authorize_url, token_url,
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
        self._api: ZoomAPI = hass.data[DOMAIN][config_entry.entry_id]
        self._name: str = config_entry.data[CONF_NAME]

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
            hass.bus.async_fire(HA_OCCUPANCY_EVENT, status)
        except:
            _LOGGER.warning("Received unknown event: %s", await request.text())

        return Response(status=HTTP_OK)
