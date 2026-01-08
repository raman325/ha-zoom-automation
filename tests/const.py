"""Constants for zoom tests."""

from datetime import timedelta

from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_NAME
import homeassistant.util.dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zoom.const import CONF_SECRET_TOKEN, DOMAIN

MOCK_CONFIG = {
    CONF_NAME: "test",
    CONF_CLIENT_ID: "client_id",
    CONF_CLIENT_SECRET: "client_secret",
    CONF_SECRET_TOKEN: "token",
}

MOCK_TOKEN = {
    "access_token": "test",
    "token_type": "bearer",
    "refresh_token": "test",
    "expires_in": 3600,
    "scope": "chat_contact:read user:read",
    "expires_at": dt_util.as_timestamp(dt_util.now() + timedelta(days=365)),
}

MOCK_ENTRY = MockConfigEntry(
    domain=DOMAIN,
    data={
        **MOCK_CONFIG,
        CONF_NAME: "test",
        "auth_implementation": DOMAIN,
        "token": MOCK_TOKEN,
    },
    entry_id="test",
    unique_id="zoom_test",
)
