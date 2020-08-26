"""The Zoom Automation integration."""
import json
from logging import getLogger

from aiohttp.web import Request
from homeassistant.components.webhook import async_register, async_unregister
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_NAME,
    CONF_WEBHOOK_ID,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .api import ZoomAPI
from .common import ZoomOAuth2Implementation
from .config_flow import OAuth2FlowHandler
from .const import (
    DOMAIN,
    HA_CONNECTIVITY_EVENT,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    WEBHOOK_RESPONSE_SCHEMA,
    ZOOM_SCHEMA,
)

_LOGGER = getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: ZOOM_SCHEMA}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["binary_sensor", "sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the Zoom Automation component."""
    hass.data.setdefault(DOMAIN, {})

    if DOMAIN not in config:
        return True

    OAuth2FlowHandler.async_register_implementation(
        hass,
        ZoomOAuth2Implementation(
            hass,
            DOMAIN,
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
            config[DOMAIN][CONF_WEBHOOK_ID],
        ),
    )
    hass.data[DOMAIN][SOURCE_IMPORT] = True

    return True


async def handle_webhook(hass: HomeAssistant, webhook_id: str, request: Request):
    """Handle incoming webhook from Zoom."""
    try:
        data = await request.json()
        status = WEBHOOK_RESPONSE_SCHEMA(data)
        _LOGGER.debug("Received webhook: %s", json.dumps(status))
    except:
        _LOGGER.warning("Received unknown webhook event: %s", await request.text())
        return

    hass.bus.async_fire(HA_CONNECTIVITY_EVENT, status)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Zoom from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    try:
        implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    except ValueError:
        implementation = ZoomOAuth2Implementation(
            hass,
            DOMAIN,
            entry.data[CONF_CLIENT_ID],
            entry.data[CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
            entry.data[CONF_WEBHOOK_ID],
        )
        OAuth2FlowHandler.async_register_implementation(hass, implementation)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = ZoomAPI(
        config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    )

    # Register callback just once for when Zoom event is received.
    if entry.data[CONF_WEBHOOK_ID] not in hass.data[DOMAIN]:
        async_register(
            hass,
            DOMAIN,
            entry.data[CONF_NAME],
            entry.data[CONF_WEBHOOK_ID],
            handle_webhook,
        )
        _LOGGER.debug("webhook registered")
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id)

    if entry.data[CONF_WEBHOOK_ID] and len(hass.data[DOMAIN]) == 1:
        async_unregister(hass, entry.data[CONF_WEBHOOK_ID])

    return True
