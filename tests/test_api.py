"""Test zoom API."""
from http import HTTPStatus
from unittest.mock import patch

from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.helpers import config_entry_oauth2_flow
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMockResponse,
)

from custom_components.zoom.api import ZoomAPI
from custom_components.zoom.common import ZoomOAuth2Implementation
from custom_components.zoom.const import (
    CONF_SECRET_TOKEN,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)

from .const import MOCK_ENTRY, MOCK_TOKEN


async def test_api(hass):
    """Test API."""
    MOCK_ENTRY.add_to_hass(hass)
    implementation = ZoomOAuth2Implementation(
        hass,
        DOMAIN,
        MOCK_ENTRY.data[CONF_CLIENT_ID],
        MOCK_ENTRY.data[CONF_CLIENT_SECRET],
        OAUTH2_AUTHORIZE,
        OAUTH2_TOKEN,
        MOCK_ENTRY.data[CONF_SECRET_TOKEN],
        "test",
    )
    api = ZoomAPI(
        config_entry_oauth2_flow.OAuth2Session(hass, MOCK_ENTRY, implementation)
    )

    assert await api.async_get_access_token() == MOCK_TOKEN

    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session.async_request",
        return_value=AiohttpClientMockResponse(
            "get",
            "zoom_url",
            status=HTTPStatus.OK,
            json={"id": "test", "first_name": "test"},
        ),
    ):
        await api.async_get_contact_user_profile("test")

    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session.async_request",
        return_value=AiohttpClientMockResponse(
            "get",
            "zoom_url",
            status=HTTPStatus.OK,
            json={
                "next_page_token": "",
                "contacts": [{"id": "test", "first_name": "test"}],
            },
        ),
    ):
        await api.async_get_contacts()

    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session.async_request",
        return_value=AiohttpClientMockResponse(
            "get",
            "zoom_url",
            status=HTTPStatus.OK,
            json={"id": "test", "first_name": "test"},
        ),
    ):
        await api.async_get_my_user_profile()
