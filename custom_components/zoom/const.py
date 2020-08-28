"""Constants for the Zoom integration."""
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

DOMAIN = "zoom"
DEFAULT_NAME = "Zoom"

HA_URL = f"/api/{DOMAIN}"

CONF_VERIFICATION_TOKEN = "verification_token"

OAUTH2_AUTHORIZE = "https://zoom.us/oauth/authorize"
OAUTH2_TOKEN = "https://zoom.us/oauth/token"

BASE_URL = "https://api.zoom.us/v2/"
USER_PROFILE = "users/me"

ZOOM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): vol.Coerce(str),
        vol.Required(CONF_CLIENT_SECRET): vol.Coerce(str),
        vol.Required(CONF_VERIFICATION_TOKEN): vol.Coerce(str),
    }
)

CONF_VERIFICATION_TOKEN = "verification_token"

ATTR_EVENT = "event"
ATTR_PAYLOAD = "payload"
ATTR_OBJECT = "object"
ATTR_ID = "id"
ATTR_PRESENCE_STATUS = "presence_status"

OCCUPANCY_EVENT = "user.presence_status_updated"
OCCUPANCY_STATUS = [ATTR_PAYLOAD, ATTR_OBJECT, ATTR_PRESENCE_STATUS]
OCCUPANCY_ID = [ATTR_PAYLOAD, ATTR_OBJECT, ATTR_ID]
OCCUPANCY_STATUS_OFF = "Available"

HA_ZOOM_EVENT = f"{DOMAIN}_webhook"

WEBHOOK_RESPONSE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_EVENT): cv.string, vol.Required(ATTR_PAYLOAD): dict}
)
