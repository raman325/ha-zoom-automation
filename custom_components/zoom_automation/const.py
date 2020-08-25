"""Constants for the Zoom Automation integration."""
from homeassistant.const import (
    CONF_ALIAS,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
)
import voluptuous as vol

DOMAIN = "zoom_automation"
DEFAULT_ALIAS = "Zoom Automation"
CREATE_NEW = "(Create New App)"

OAUTH2_AUTHORIZE = "https://zoom.us/oauth/authorize"
OAUTH2_TOKEN = "https://zoom.us/oauth/token"

ZOOM_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ALIAS, default=DEFAULT_ALIAS): vol.Coerce(str),
        vol.Required(CONF_CLIENT_ID): vol.Coerce(str),
        vol.Required(CONF_CLIENT_SECRET): vol.Coerce(str),
    }
)
