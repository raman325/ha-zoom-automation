"""Config flow for Zoom Automation."""
import logging
from typing import Dict

from homeassistant import config_entries
from homeassistant.const import CONF_ALIAS, CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.util import slugify
import voluptuous as vol

from .common import ZoomOAuth2Implementation
from .const import (
    CREATE_NEW,
    DEFAULT_ALIAS,
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

    async def async_step_user(self, user_input=None):
        """Handle a flow start."""
        assert self.hass
        implementation = None
        self.hass.data.setdefault(DOMAIN, {})
        if user_input is None:
            if not self.hass.data[DOMAIN].get(config_entries.SOURCE_IMPORT, False):
                implementations = await config_entry_oauth2_flow.async_get_implementations(
                    self.hass, self.DOMAIN
                )
                if not implementations:
                    return self.async_show_form(step_id="user", data_schema=ZOOM_SCHEMA)

                return await self._async_user_choose_implementation_form(
                    implementations
                )

            return await self.async_step_pick_implementation()

        errors = {}

        name = (
            user_input.get(CONF_ALIAS) if user_input.get(CONF_ALIAS) else DEFAULT_ALIAS
        )

        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if slugify(name) == slugify(entry.data[CONF_ALIAS]):
                errors[CONF_ALIAS] = "unique_name_required"

        implementation = ZoomOAuth2Implementation(
            self.hass,
            DOMAIN,
            name,
            user_input[CONF_CLIENT_ID],
            user_input[CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        )
        self.async_register_implementation(self.hass, implementation)

        if errors:
            return self.async_show_form(
                step_id="user", data_schema=ZOOM_SCHEMA, errors=errors
            )

        return await self.async_step_pick_implementation(
            user_input={"implementation": implementation.domain}
        )

    async def async_step_user_choose_implementation(self, user_input) -> dict:
        """Have user choose an implementation."""
        if not user_input:
            self._async_user_choose_implementation_form()

        if user_input["implementation"] == CREATE_NEW:
            return self.async_show_form(step_id="user", data_schema=ZOOM_SCHEMA)

        return self.async_step_pick_implementation(user_input)

    async def _async_user_choose_implementation_form(
        self, implementations: Dict[str, ZoomOAuth2Implementation] = None
    ) -> dict:
        """Get implementations and add `create new` option to show form."""
        if not implementations:
            implementations = await config_entry_oauth2_flow.async_get_implementations(
                self.hass, self.DOMAIN
            )
        choices = {key: impl.name for key, impl in implementations.items()}
        choices[CREATE_NEW] = CREATE_NEW

        return self.async_show_form(
            step_id="user_choose_implementation",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "implementation", default=list(implementations.keys())[0]
                    ): vol.In(choices)
                }
            ),
        )

    async def async_oauth_create_entry(self, data: dict) -> dict:
        """Create an entry for the flow."""
        data.update(
            {
                CONF_ALIAS: self.flow_impl.name,
                CONF_CLIENT_ID: self.flow_impl.client_id,
                CONF_CLIENT_SECRET: self.flow_impl.client_secret,
            }
        )
        return self.async_create_entry(title=self.flow_impl.name, data=data)
