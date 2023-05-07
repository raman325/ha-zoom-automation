"""Constants for the Zoom integration."""

from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_NAME
import voluptuous as vol

API = "api"
DOMAIN = "zoom"
DEFAULT_NAME = "Zoom"

HA_URL = f"/api/{DOMAIN}"

CONF_CONNECTIVITY_ON_STATUSES = "connectivity_on_statuses"
CONF_VERIFICATION_TOKEN = "verification_token"
CONF_SECRET_TOKEN = "secret_token"

OAUTH2_AUTHORIZE = "https://zoom.us/oauth/authorize"
OAUTH2_TOKEN = "https://zoom.us/oauth/token"

BASE_URL = "https://api.zoom.us/v2/"
USER_PROFILE_URL = "users/me"
USER_PROFILE_COORDINATOR = "user_profile_coordinator"
CONTACT_LIST_URL = "chat/users/me/contacts"
CONTACT_LIST_COORDINATOR = "contact_list_coordinator"

ZOOM_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): vol.Coerce(str),
        vol.Required(CONF_CLIENT_ID): vol.Coerce(str),
        vol.Required(CONF_CLIENT_SECRET): vol.Coerce(str),
        vol.Required(CONF_SECRET_TOKEN): vol.Coerce(str),
    },
    extra=vol.ALLOW_EXTRA,
)

ATTR_EVENT = "event"
ATTR_EVENT_TS = "event_ts"
ATTR_PAYLOAD = "payload"
ATTR_OBJECT = "object"
ATTR_ID = "id"
ATTR_CONNECTIVITY_STATUS = "presence_status"

CONNECTIVITY_EVENT = "user.presence_status_updated"
CONNECTIVITY_STATUS = [ATTR_PAYLOAD, ATTR_OBJECT, ATTR_CONNECTIVITY_STATUS]
CONNECTIVITY_ID = [ATTR_PAYLOAD, ATTR_OBJECT, ATTR_ID]

VALIDATION_EVENT = "endpoint.url_validation"

ALL_CONNECTIVITY_STATUSES = [
    "Available",
    "Away",
    "Do_Not_Disturb",
    "In_Calendar_Event",
    "In_Meeting",
    "Offline",
    "On_Phone_Call",
    "Presenting",
]
DEFAULT_CONNECTIVITY_ON_STATUSES = ["In_Meeting", "Presenting", "On_Phone_Call"]

HA_ZOOM_EVENT = f"{DOMAIN}_webhook"

WEBHOOK_RESPONSE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_EVENT): vol.Coerce(str),
        vol.Required(ATTR_PAYLOAD): dict,
        vol.Required(ATTR_EVENT_TS): vol.Coerce(int),
    },
    extra=vol.ALLOW_EXTRA,
)
