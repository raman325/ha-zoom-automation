"""Constants for the Zoom integration."""

from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_NAME
from homeassistant.helpers.config_validation import string
import voluptuous as vol

API = "api"
DOMAIN = "zoom"
DEFAULT_NAME = "Zoom"

HA_URL = f"/api/{DOMAIN}"

CONF_CONNECTIVITY_ON_STATUSES = "connectivity_on_statuses"
CONF_VERIFICATION_TOKEN = "verification_token"

OAUTH2_AUTHORIZE = "https://zoom.us/oauth/authorize"
OAUTH2_TOKEN = "https://zoom.us/oauth/token"

BASE_URL = "https://api.zoom.us/v2/"
USER_PROFILE_URL = "users/me"
USER_PROFILE_COORDINATOR = "user_profile_coordinator"
CONTACT_LIST_URL = "chat/users/me/contacts"
CONTACT_LIST_COORDINATOR = "contact_list_coordinator"
VERIFICATION_TOKENS = "verification_tokens"

ZOOM_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): vol.Coerce(str),
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
ATTR_CONNECTIVITY_STATUS = "presence_status"

CONNECTIVITY_EVENT = "user.presence_status_updated"
CONNECTIVITY_STATUS = [ATTR_PAYLOAD, ATTR_OBJECT, ATTR_CONNECTIVITY_STATUS]
CONNECTIVITY_ID = [ATTR_PAYLOAD, ATTR_OBJECT, ATTR_ID]

ALL_CONNECTIVITY_STATUSES = [
    "In_Meeting",
    "Presenting",
    "On_Phone_Call",
    "In_Calendar_Event",
    "Available",
    "Away",
    "Do_Not_Disturb",
]
DEFAULT_CONNECTIVITY_ON_STATUSES = ["In_Meeting", "Presenting", "On_Phone_Call"]

HA_ZOOM_EVENT = f"{DOMAIN}_webhook"

WEBHOOK_RESPONSE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_EVENT): string, vol.Required(ATTR_PAYLOAD): dict},
    extra=vol.ALLOW_EXTRA,
)
