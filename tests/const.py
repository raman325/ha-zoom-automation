"""Constants and helpers for zoom tests."""

from datetime import timedelta

from homeassistant.components.event import DOMAIN as EVENT_DOMAIN
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_NAME
from homeassistant.helpers import entity_registry as er
import homeassistant.util.dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zoom.const import CONF_SECRET_TOKEN, DOMAIN, VALIDATION_EVENT


def get_non_validation_event_entities(
    ent_reg: er.EntityRegistry, entry_id: str
) -> list[er.RegistryEntry]:
    """Get event entities excluding the pre-created validation entity."""
    return [
        e
        for e in er.async_entries_for_config_entry(ent_reg, entry_id)
        if e.domain == EVENT_DOMAIN and VALIDATION_EVENT not in e.unique_id
    ]

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
