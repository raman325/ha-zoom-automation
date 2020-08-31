"""Config flow for Zoom Automation."""
import logging
from typing import Any, Dict

from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_NAME
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.util import slugify
import voluptuous as vol

from .common import ZoomOAuth2Implementation
from .const import (
    CONF_VERIFICATION_TOKEN,
    DEFAULT_NAME,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    ZOOM_SCHEMA,
)

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

    def __init__(self) -> None:
        """Intantiate config flow."""
        self._name: str = ""
        self._picked_name: bool = False
        self._stored_data = {}
        super().__init__()

    async def async_step_user(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Handle a flow start."""
        assert self.hass

        if user_input is None:
            return (
                self.async_show_form(step_id="user", data_schema=ZOOM_SCHEMA)
                if not await config_entry_oauth2_flow.async_get_implementations(
                    self.hass, self.DOMAIN
                )
                else await self.async_step_pick_implementation()
            )

        self.async_register_implementation(
            self.hass,
            ZoomOAuth2Implementation(
                self.hass,
                DOMAIN,
                user_input[CONF_CLIENT_ID],
                user_input[CONF_CLIENT_SECRET],
                OAUTH2_AUTHORIZE,
                OAUTH2_TOKEN,
                user_input[CONF_VERIFICATION_TOKEN],
            ),
        )

        return await self.async_step_pick_implementation()

    async def async_step_choose_name(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Require users to choose a name for each entry."""
        if not user_input:
            return self.async_show_form(
                step_id="choose_name",
                data_schema=vol.Schema(
                    {vol.Required(CONF_NAME, default=DEFAULT_NAME): vol.Coerce(str)}
                ),
            )

        self._name = user_input[CONF_NAME]
        await self.async_set_unique_id(
            f"{DOMAIN}_{slugify(self._name)}", raise_on_progress=True
        )
        self._abort_if_unique_id_configured()

        self._picked_name = True
        return await self.async_oauth_create_entry()

    async def async_oauth_create_entry(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create an entry for the flow."""
        if not self._picked_name:
            self._stored_data = data.copy()
            return await self.async_step_choose_name()

        data = self._stored_data
        self.flow_impl: ZoomOAuth2Implementation
        data.update(
            {
                CONF_NAME: self._name,
                CONF_CLIENT_ID: self.flow_impl.client_id,
                CONF_CLIENT_SECRET: self.flow_impl.client_secret,
                CONF_VERIFICATION_TOKEN: self.flow_impl._verification_token,
            }
        )
        return self.async_create_entry(title=self._name, data=data)
