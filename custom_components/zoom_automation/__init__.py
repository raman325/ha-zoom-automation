"""The Zoom Automation integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    config_entry_oauth2_flow,
    config_validation as cv,
)
from homeassistant.helpers.network import get_url
import voluptuous as vol

from . import api, config_flow
from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN

ZOOM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): vol.Coerce(str),
        vol.Required(CONF_CLIENT_SECRET): vol.Coerce(str),
    }
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: ZOOM_SCHEMA}, extra=vol.ALLOW_EXTRA)


class ZoomOAuth2Implementation(
    config_entry_oauth2_flow.LocalOAuth2Implementation
):
    """Oauth2 implementation that only uses the external url."""

    @property
    def redirect_uri(self) -> str:
        """Return the redirect uri."""
        url = get_url(self.hass, allow_internal=False, prefer_cloud=True)
        return f"{url}{config_entry_oauth2_flow.AUTH_CALLBACK_PATH}"


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Zoom Automation component."""
    hass.data[DOMAIN] = {}

    if DOMAIN not in config:
        return True

    config_flow.OAuth2FlowHandler.async_register_implementation(
        hass,
        ZoomOAuth2Implementation(
            hass,
            DOMAIN,
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        ),
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Zoom from a config entry."""
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )

    session = config_entry_oauth2_flow.OAuth2Session(
        hass, entry, implementation
    )

    hass.data[DOMAIN][entry.entry_id] = api.AsyncConfigEntryAuth(session)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id)

    return True
