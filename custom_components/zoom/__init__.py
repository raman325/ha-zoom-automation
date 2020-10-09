"""The Zoom integration."""
from logging import getLogger

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .api import ZoomAPI
from .common import (
    ZoomOAuth2Implementation,
    ZoomUserProfileDataUpdateCoordinator,
    ZoomWebhookRequestView,
    valid_external_url,
)
from .config_flow import ZoomOAuth2FlowHandler
from .const import (
    API,
    CONF_VERIFICATION_TOKEN,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    USER_PROFILE_COORDINATOR,
    ZOOM_SCHEMA,
)

_LOGGER = getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: ZOOM_SCHEMA}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["binary_sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the Zoom component."""
    hass.data.setdefault(DOMAIN, {})

    if DOMAIN not in config:
        return True

    if not valid_external_url(hass):
        return False

    ZoomOAuth2FlowHandler.async_register_implementation(
        hass,
        ZoomOAuth2Implementation(
            hass,
            DOMAIN,
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
            config[DOMAIN][CONF_VERIFICATION_TOKEN],
        ),
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Zoom from a config entry."""
    hass.data[DOMAIN].setdefault(entry.entry_id, {})
    try:
        implementation = (
            await config_entry_oauth2_flow.async_get_config_entry_implementation(
                hass, entry
            )
        )
    except ValueError:
        implementation = ZoomOAuth2Implementation(
            hass,
            DOMAIN,
            entry.data[CONF_CLIENT_ID],
            entry.data[CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
            entry.data[CONF_VERIFICATION_TOKEN],
        )
        ZoomOAuth2FlowHandler.async_register_implementation(hass, implementation)

    api = ZoomAPI(config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation))
    coordinator = ZoomUserProfileDataUpdateCoordinator(hass, api)
    await coordinator.async_refresh()
    hass.data[DOMAIN][entry.entry_id][USER_PROFILE_COORDINATOR] = coordinator
    hass.data[DOMAIN][entry.entry_id][API] = api
    my_profile = await api.async_get_my_user_profile()
    new_data = entry.data.copy()
    new_data[CONF_ID] = my_profile.get("id")  # type: ignore
    hass.config_entries.async_update_entry(entry, data=new_data)  # type: ignore

    # Register view
    hass.http.register_view(ZoomWebhookRequestView(entry.data[CONF_VERIFICATION_TOKEN]))

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    hass.data[DOMAIN].pop(config_entry.entry_id)

    return True
