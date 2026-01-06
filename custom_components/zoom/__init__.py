"""The Zoom integration."""
from __future__ import annotations

from copy import deepcopy
from logging import getLogger

from aiohttp.client_exceptions import ClientResponseError
from aiohttp.web_exceptions import HTTPUnauthorized
from homeassistant.config_entries import ConfigEntry
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
    CONF_SECRET_TOKEN,
    CONF_VERIFICATION_TOKEN,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    USER_PROFILE_COORDINATOR,
    ZOOM_SCHEMA,
)

_LOGGER = getLogger(__name__)


def ensure_all_have_unique_names(value: list[dict[str, str]]) -> list[dict[str, str]]:
    """Validate that for multiple entries, they have names."""
    if len({entry[CONF_NAME] for entry in value}) != len(value):
        raise vol.Invalid(
            "You must provide a unique name for each Zoom app when providing "
            "multiple sets of application credentials."
        )

    return value


SCHEMA = ZOOM_SCHEMA.schema
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [SCHEMA],
            ensure_all_have_unique_names,
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = [Platform.BINARY_SENSOR]


def remove_verification_token_from_entry(
    hass: HomeAssistant, entry: ConfigEntry, secret_token: str | None = None
) -> None:
    """Remove the verification token from the config entry."""
    new_data = deepcopy(entry.data)
    new_data.pop(CONF_VERIFICATION_TOKEN, None)
    if secret_token:
        new_data[CONF_SECRET_TOKEN] = secret_token
    hass.config_entries.async_update_entry(entry, data=new_data)


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the Zoom component."""
    if DOMAIN not in config:
        return True

    if not valid_external_url(hass):
        return False

    for app in config[DOMAIN]:
        # Get secret_token from YAML, falling back to None if only verification_token exists
        secret_token = app.get(CONF_SECRET_TOKEN)

        if not secret_token and CONF_VERIFICATION_TOKEN in app:
            _LOGGER.warning(
                "Zoom app '%s' is using deprecated 'verification_token'. "
                "Please update your configuration.yaml to use 'secret_token' instead. "
                "You can find your Secret Token under Features > Access in your Zoom app. "
                "Webhook validation will not work until you update to secret_token.",
                app[CONF_NAME],
            )

        ZoomOAuth2FlowHandler.async_register_implementation(
            hass,
            ZoomOAuth2Implementation(
                hass,
                DOMAIN,
                app[CONF_CLIENT_ID],
                app[CONF_CLIENT_SECRET],
                OAUTH2_AUTHORIZE,
                OAUTH2_TOKEN,
                secret_token,
                app[CONF_NAME],
            ),
        )

        # If YAML has secret_token, migrate any matching config entries
        if secret_token:
            for entry in hass.config_entries.async_entries(DOMAIN):
                if (
                    entry.data[CONF_CLIENT_ID] == app[CONF_CLIENT_ID]
                    and entry.data[CONF_CLIENT_SECRET] == app[CONF_CLIENT_SECRET]
                ):
                    # Migrate entry if it has verification_token or missing secret_token
                    if (
                        CONF_VERIFICATION_TOKEN in entry.data
                        or CONF_SECRET_TOKEN not in entry.data
                        or entry.data.get(CONF_SECRET_TOKEN) != secret_token
                    ):
                        _LOGGER.info(
                            "Migrating Zoom config entry '%s' with secret_token from YAML",
                            entry.title,
                        )
                        remove_verification_token_from_entry(hass, entry, secret_token)
                        # Also update version if needed
                        if entry.version < 2:
                            hass.config_entries.async_update_entry(entry, version=2)

    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entry to new version."""
    _LOGGER.debug("Migrating Zoom config entry from version %s", entry.version)

    if entry.version == 1:
        # V1 -> V2: Replace verification_token with secret_token
        new_data = deepcopy(dict(entry.data))

        # If entry already has secret_token, just clean up verification_token
        if CONF_SECRET_TOKEN in new_data:
            new_data.pop(CONF_VERIFICATION_TOKEN, None)
            hass.config_entries.async_update_entry(entry, data=new_data, version=2)
            _LOGGER.info("Migrated Zoom config entry to version 2")
            return True

        # No secret_token available - user must provide it through reauth
        _LOGGER.warning(
            "Zoom has moved from verification tokens to secret tokens. "
            "Please reconfigure this integration with your app's secret token. "
            "See the integration README for instructions."
        )
        # Trigger a reauth flow so the user can provide the new secret token
        entry.async_start_reauth(hass, data=dict(entry.data))
        return False

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Zoom from a config entry."""
    hass.data.setdefault(DOMAIN, {})
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
            entry.data[CONF_SECRET_TOKEN],
            entry.data[CONF_NAME],
        )
        ZoomOAuth2FlowHandler.async_register_implementation(hass, implementation)

    api = ZoomAPI(config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation))
    coordinator = ZoomUserProfileDataUpdateCoordinator(hass, api)
    await coordinator.async_refresh()
    hass.data[DOMAIN][entry.entry_id][USER_PROFILE_COORDINATOR] = coordinator
    hass.data[DOMAIN][entry.entry_id][API] = api

    try:
        my_profile = await api.async_get_my_user_profile()
    except (HTTPUnauthorized, ClientResponseError) as err:
        if isinstance(err, ClientResponseError) and err.status not in (400, 401):
            return False

        # If we are not authorized, we need to revalidate OAuth
        entry.async_start_reauth(hass, data=dict(entry.data))
        return False
    new_data = entry.data.copy()
    new_data[CONF_ID] = my_profile.get("id")  # type: ignore
    hass.config_entries.async_update_entry(entry, data=new_data)  # type: ignore

    # Register view
    hass.http.register_view(ZoomWebhookRequestView())

    # Forward config entry setups for all defined platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    hass.data[DOMAIN].pop(config_entry.entry_id)

    return True
