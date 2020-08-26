"""Constants for the Zoom Automation integration."""
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_WEBHOOK_ID,
)
from homeassistant.helpers import config_validation as cv
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
        vol.Optional(CONF_WEBHOOK_ID): vol.Coerce(str),
    }
)

ATTR_EVENT = "event"
ATTR_PAYLOAD = "payload"
ATTR_ACCOUNT_ID = "account_id"
ATTR_OBJECT = "object"
ATTR_DATE_TIME = "date_time"
ATTR_EMAIL = "email"
ATTR_ID = "id"
ATTR_PRESENCE_STATUS = "presence_status"

OCCUPANCY_EVENT = "user.presence_status_updated"
OCCUPANCY_STATUS = [ATTR_PAYLOAD, ATTR_OBJECT, ATTR_PRESENCE_STATUS]
OCCUPANCY_ID = [ATTR_PAYLOAD, ATTR_OBJECT, ATTR_ID]
OCCUPANCY_STATUS_OFF = "Available"

HA_OCCUPANCY_EVENT = f"{DOMAIN}_webhook"

WEBHOOK_RESPONSE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_EVENT): "user.presence_status_updated",
        vol.Required(ATTR_PAYLOAD): {
            vol.Required(ATTR_ACCOUNT_ID): cv.string,
            vol.Required(ATTR_OBJECT): {
                vol.Required(ATTR_DATE_TIME): cv.string,
                vol.Required(ATTR_EMAIL): cv.string,
                vol.Required(ATTR_ID): cv.string,
                vol.Required(ATTR_PRESENCE_STATUS): cv.string,
            },
        },
    }
)
