"""Constants for the Zoom Automation integration."""
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_NAME
import voluptuous as vol

DOMAIN = "zoom_automation"
DEFAULT_NAME = "Zoom Automation"

OAUTH2_AUTHORIZE = "https://zoom.us/oauth/authorize"
OAUTH2_TOKEN = "https://zoom.us/oauth/token"

BASE_URL = "https://api.zoom.us/v2/"
USER_PROFILE = "users/me"

ZOOM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): vol.Coerce(str),
        vol.Required(CONF_CLIENT_SECRET): vol.Coerce(str),
    }
)
