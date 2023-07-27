"""The Zoom integration."""

from logging import getLogger
from typing import Dict, List

from aiohttp.client_exceptions import ClientResponseError
from aiohttp.web_exceptions import HTTPUnauthorized
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntry
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_ID,
    CONF_NAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow, config_validation as cv
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
    VERIFICATION_TOKENS,
    ZOOM_SCHEMA,
)

_LOGGER = getLogger(__name__)


def ensure_multiple_have_names(value: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Validate that for multiple entries, they have names."""
    if len({entry[CONF_NAME] for entry in value}) != len(value):
        raise vol.Invalid(
            "You must provide a unique name for each Zoom app when providing "
            "multiple sets of application credentials."
        )

    return value


CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [ZOOM_SCHEMA], ensure_multiple_have_names)},
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = [Platform.BINARY_SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the Zoom component."""
    if DOMAIN not in config:
        return True

    if not valid_external_url(hass):
        return False

    for app in config[DOMAIN]:
        ZoomOAuth2FlowHandler.async_register_implementation(
            hass,
            ZoomOAuth2Implementation(
                hass,
                DOMAIN,
                app[CONF_CLIENT_ID],
                app[CONF_CLIENT_SECRET],
                OAUTH2_AUTHORIZE,
                OAUTH2_TOKEN,
                app[CONF_VERIFICATION_TOKEN],
                app[CONF_NAME],
            ),
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Zoom from a config entry."""
    hass.data.setdefault(DOMAIN, {}).setdefault(VERIFICATION_TOKENS, set())
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
            entry.data[CONF_NAME],
        )
        ZoomOAuth2FlowHandler.async_register_implementation(hass, implementation)

    api = ZoomAPI(config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation))
    coordinator = ZoomUserProfileDataUpdateCoordinator(hass, api)
    await coordinator.async_refresh()
    hass.data[DOMAIN][entry.entry_id][USER_PROFILE_COORDINATOR] = coordinator
    hass.data[DOMAIN][entry.entry_id][API] = api
    hass.data[DOMAIN][VERIFICATION_TOKENS].add(entry.data[CONF_VERIFICATION_TOKEN])

    try:
        my_profile = await api.async_get_my_user_profile()
    except (HTTPUnauthorized, ClientResponseError) as err:
        if isinstance(err, ClientResponseError) and err.status not in (400, 401):
            return False

        # If we are not authorized, we need to revalidate OAuth
        if not [
            flow
            for flow in hass.config_entries.flow.async_progress()
            if flow["context"]["source"] == SOURCE_REAUTH
            and flow["context"]["unique_id"] == entry.unique_id
        ]:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_REAUTH, "unique_id": entry.unique_id},
                    data=entry.data,
                )
            )
        return False
    new_data = entry.data.copy()
    new_data[CONF_ID] = my_profile.get("id")  # type: ignore
    hass.config_entries.async_update_entry(entry, data=new_data)  # type: ignore

    # Register view
    hass.http.register_view(ZoomWebhookRequestView())

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    hass.data[DOMAIN].pop(config_entry.entry_id)

    return True
