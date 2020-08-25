"""The Zoom Automation integration."""
from logging import getLogger
from typing import Dict, List

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow, config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import slugify
import voluptuous as vol

from . import api, config_flow
from .common import ZoomOAuth2Implementation
from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN, ZOOM_SCHEMA

_LOGGER = getLogger(__name__)


def validate_unique_names(config: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Validate CONF_NAME is unique for every entry."""
    slug_names = [slugify(zoom_config[CONF_NAME]) for zoom_config in config]
    if len(set(slug_names)) != len(slug_names):
        raise vol.Invalid(f"'{CONF_NAME}' must be unique for every entry.")
    return config


CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [vol.All(ZOOM_SCHEMA)], validate_unique_names)},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the Zoom Automation component."""
    hass.data.setdefault(DOMAIN, {})

    if DOMAIN not in config:
        return True

    for zoom_config in config[DOMAIN]:
        config_flow.OAuth2FlowHandler.async_register_implementation(
            hass,
            ZoomOAuth2Implementation(
                hass,
                DOMAIN,
                zoom_config[CONF_NAME],
                zoom_config[CONF_CLIENT_ID],
                zoom_config[CONF_CLIENT_SECRET],
                OAUTH2_AUTHORIZE,
                OAUTH2_TOKEN,
            ),
        )
        hass.data[DOMAIN][SOURCE_IMPORT] = True

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Zoom from a config entry."""
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )

    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    hass.data[DOMAIN][entry.entry_id] = api.AsyncConfigEntryAuth(session)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id)

    if len(hass.data[DOMAIN]) == 1:
        hass.data.pop(DOMAIN)

    return True
