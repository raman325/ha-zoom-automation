"""Config flow for Zoom Automation."""
import logging

from homeassistant import config_entries

# from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_NAME
from homeassistant.helpers import config_entry_oauth2_flow

# from .common import ZoomOAuth2Implementation
# from .const import DEFAULT_NAME, DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN, ZOOM_SCHEMA
from .const import DOMAIN

# from homeassistant.util import slugify


_LOGGER = logging.getLogger(__name__)


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Zoom Automation OAuth2 authentication."""

    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    # async def async_step_user(self, user_input=None):
    #     """Handle a flow start."""
    #     assert self.hass
    #     implementation = None
    #     self.hass.data.setdefault(DOMAIN, {})
    #     if user_input is None and not self.hass.data[DOMAIN].get(
    #         config_entries.SOURCE_IMPORT
    #     ):
    #         return self.async_show_form(step_id="user", data_schema=ZOOM_SCHEMA)

    #     errors = {}

    #     if user_input and CONF_CLIENT_ID in user_input:
    #         name = user_input.get(CONF_NAME)
    #         name = name if name else DEFAULT_NAME

    #         for entry in self.hass.config_entries.async_entries(DOMAIN):
    #             if slugify(name) == slugify(entry.data[CONF_NAME]):
    #                 errors[CONF_NAME] = "unique_name_required"

    #         implementation = ZoomOAuth2Implementation(
    #             self.hass,
    #             DOMAIN,
    #             name,
    #             user_input[CONF_CLIENT_ID],
    #             user_input[CONF_CLIENT_SECRET],
    #             OAUTH2_AUTHORIZE,
    #             OAUTH2_TOKEN,
    #         )
    #         self.async_register_implementation(
    #             self.hass, implementation,
    #         )

    #     if errors:
    #         return self.async_show_form(
    #             step_id="user", data_schema=ZOOM_SCHEMA, errors=errors
    #         )

    #     return await self.async_step_pick_implementation(
    #         user_input={"implementation": implementation} if implementation else None
    #     )
