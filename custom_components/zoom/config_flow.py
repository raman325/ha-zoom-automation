"""Config flow for Zoom Automation."""

import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow, config_validation as cv
from homeassistant.util import slugify
import voluptuous as vol

from .common import ZoomOAuth2Implementation, valid_external_url
from .const import (
    ALL_CONNECTIVITY_STATUSES,
    CONF_CONNECTIVITY_ON_STATUSES,
    CONF_VERIFICATION_TOKEN,
    DEFAULT_NAME,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    ZOOM_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)


class ZoomOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Zoom integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize zoom options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the zoom options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONNECTIVITY_ON_STATUSES,
                        default=self.config_entry.options[
                            CONF_CONNECTIVITY_ON_STATUSES
                        ],
                    ): cv.multi_select(ALL_CONNECTIVITY_STATUSES)
                }
            ),
        )


class ZoomOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Zoom Automation OAuth2 authentication."""

    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ZoomOptionsFlow:
        """Get the options flow for this handler."""
        return ZoomOptionsFlow(config_entry)

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    def __init__(self) -> None:
        """Instantiate config flow."""
        self._name: str = None
        self._stored_data = {}
        super().__init__()

    async def async_step_user(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Handle a flow start."""
        assert self.hass

        if not valid_external_url(self.hass):
            return self.async_abort(reason="no_external_url")

        if (
            user_input is None
            and not await config_entry_oauth2_flow.async_get_implementations(
                self.hass, self.DOMAIN
            )
        ):
            return self.async_show_form(step_id="user", data_schema=ZOOM_SCHEMA)

        if user_input:
            await self.async_set_unique_id(
                f"{DOMAIN}_{slugify(user_input[CONF_NAME])}", raise_on_progress=True
            )
            self._abort_if_unique_id_configured()
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
                    user_input[CONF_NAME],
                ),
            )

        return await self.async_step_pick_implementation()

    async def async_step_reauth(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform reauth when OAuth token is invalid."""
        self._stored_data = {
            CONF_NAME: user_input[CONF_NAME],
            CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
            CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
            CONF_VERIFICATION_TOKEN: user_input[CONF_VERIFICATION_TOKEN],
        }
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Confirm reauth."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm", data_schema=vol.Schema({})
            )
        return await self.async_step_user()

    async def async_step_choose_name(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Require users to choose a name for each entry."""
        if not user_input:
            return self.async_show_form(
                step_id="choose_name",
                data_schema=vol.Schema({vol.Required(CONF_NAME): vol.Coerce(str)}),
            )

        self._name = user_input[CONF_NAME]
        await self.async_set_unique_id(
            f"{DOMAIN}_{slugify(self._name)}", raise_on_progress=True
        )
        self._abort_if_unique_id_configured()

        return await self.async_oauth_create_entry(self._stored_data)

    async def async_oauth_create_entry(
        self, data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create an entry for the flow."""
        # Update existing entry if performing reauth
        if self.source == config_entries.SOURCE_REAUTH:
            data.update(self._stored_data)
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if entry.unique_id == self.unique_id:
                    self.hass.config_entries.async_update_entry(entry, data=data)
                    self.hass.async_create_task(
                        self.hass.config_entries.async_reload(entry.entry_id)
                    )
                    return self.async_abort(reason="reauth_successful")
        elif self.flow_impl.name == DEFAULT_NAME and self._name is None:
            self._stored_data = data.copy()
            return await self.async_step_choose_name()

        self.flow_impl: ZoomOAuth2Implementation
        name = self._name or self.flow_impl.name
        data.update(
            {
                CONF_NAME: name,
                CONF_CLIENT_ID: self.flow_impl.client_id,
                CONF_CLIENT_SECRET: self.flow_impl.client_secret,
                CONF_VERIFICATION_TOKEN: self.flow_impl._verification_token,
            }
        )
        if not self.unique_id:
            await self.async_set_unique_id(
                f"{DOMAIN}_{slugify(name)}", raise_on_progress=True
            )
            self._abort_if_unique_id_configured()
        return self.async_create_entry(title=name, data=data)
