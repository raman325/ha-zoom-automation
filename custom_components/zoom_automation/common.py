"""Common classes and functions for Zoom Automation."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.network import get_url
from homeassistant.util import slugify

from .api import ZoomAPI
from .const import DEFAULT_NAME, DOMAIN


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
        webhook_id: str,
    ):
        """Initialize local auth implementation."""
        self._webhook_id = webhook_id
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
        self._webhook_id: str = config_entry.data[CONF_WEBHOOK_ID]
        self._name: str = config_entry.data[CONF_NAME]

    @property
    def unique_id(self):
        """Return unique_id for entity."""
        return f"{DOMAIN}_{slugify(self._name)}"
