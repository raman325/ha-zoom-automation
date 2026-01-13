"""Test Zoom event entity platform."""

import pytest
from unittest.mock import patch

from homeassistant.components.event import DOMAIN as EVENT_DOMAIN
from homeassistant.const import CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from custom_components.zoom.const import (
    ATTR_EVENT,
    ATTR_EVENT_TS,
    ATTR_LAST_EVENT_TS,
    ATTR_LAST_PAYLOAD,
    ATTR_PAYLOAD,
    CONNECTIVITY_EVENT,
    DOMAIN,
    HA_ZOOM_EVENT,
    SIGNAL_NEW_ZOOM_EVENT_TYPE,
    VALIDATION_EVENT,
)
from custom_components.zoom.event import ZoomEventExtraStoredData

from .const import MOCK_ENTRY, get_non_precreated_event_entities

# Use meeting.started for tests since it's enabled by default
# (CONNECTIVITY_EVENT is disabled by default as it's redundant with binary_sensor)
TEST_EVENT_TYPE = "meeting.started"


def _create_test_event_data(
    entry_id: str,
    event_type: str = TEST_EVENT_TYPE,
    event_ts: int = 1234567890,
) -> dict:
    """Create a test event data dict."""
    return {
        ATTR_EVENT: event_type,
        ATTR_EVENT_TS: event_ts,
        ATTR_PAYLOAD: {
            "account_id": "account123",
            "object": {
                "id": "meeting123",
                "topic": "Test Meeting",
            },
        },
        "ha_config_entry_id": entry_id,
    }


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_validation_event_entity_precreated_disabled(hass: HomeAssistant) -> None:
    """Test that the validation event entity is pre-created but disabled."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    ent_reg = er.async_get(hass)

    # Find the validation event entity
    validation_entities = [
        e
        for e in er.async_entries_for_config_entry(ent_reg, MOCK_ENTRY.entry_id)
        if e.domain == EVENT_DOMAIN and VALIDATION_EVENT in e.unique_id
    ]
    assert len(validation_entities) == 1
    validation_entity = validation_entities[0]

    # Should be disabled by default (disabled_by = INTEGRATION)
    assert validation_entity.disabled_by == er.RegistryEntryDisabler.INTEGRATION


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_connectivity_event_entity_disabled_by_default(
    hass: HomeAssistant,
) -> None:
    """Test that the connectivity event entity is disabled by default."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    # Create connectivity event entity via dispatcher
    from homeassistant.helpers.dispatcher import async_dispatcher_send

    event_data = _create_test_event_data(
        MOCK_ENTRY.entry_id, event_type=CONNECTIVITY_EVENT
    )
    async_dispatcher_send(
        hass,
        f"{SIGNAL_NEW_ZOOM_EVENT_TYPE}|{MOCK_ENTRY.entry_id}",
        CONNECTIVITY_EVENT,
        event_data,
    )
    await hass.async_block_till_done()

    ent_reg = er.async_get(hass)

    # Find the connectivity event entity
    connectivity_entities = [
        e
        for e in er.async_entries_for_config_entry(ent_reg, MOCK_ENTRY.entry_id)
        if e.domain == EVENT_DOMAIN and CONNECTIVITY_EVENT in e.unique_id
    ]
    assert len(connectivity_entities) == 1
    connectivity_entity = connectivity_entities[0]

    # Should be disabled by default (redundant with binary sensor)
    assert connectivity_entity.disabled_by == er.RegistryEntryDisabler.INTEGRATION


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_event_entity_created_on_signal(hass: HomeAssistant) -> None:
    """Test that an event entity is created when dispatcher signal is sent."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    # Get entity registry
    ent_reg = er.async_get(hass)

    # Initially no event entities (excluding pre-created validation entity)
    event_entities = get_non_precreated_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    assert len(event_entities) == 0

    # Send dispatcher signal for new event type
    from homeassistant.helpers.dispatcher import async_dispatcher_send

    event_data = _create_test_event_data(MOCK_ENTRY.entry_id)
    async_dispatcher_send(
        hass,
        f"{SIGNAL_NEW_ZOOM_EVENT_TYPE}|{MOCK_ENTRY.entry_id}",
        TEST_EVENT_TYPE,
        event_data,
    )
    await hass.async_block_till_done()

    # Now we should have one event entity (excluding validation)
    event_entities = get_non_precreated_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    assert len(event_entities) == 1
    assert TEST_EVENT_TYPE in event_entities[0].unique_id


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_event_entity_has_correct_attributes(hass: HomeAssistant) -> None:
    """Test that the event entity has correct attributes."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    ent_reg = er.async_get(hass)

    # Send dispatcher signal
    from homeassistant.helpers.dispatcher import async_dispatcher_send

    event_data = _create_test_event_data(MOCK_ENTRY.entry_id)
    async_dispatcher_send(
        hass,
        f"{SIGNAL_NEW_ZOOM_EVENT_TYPE}|{MOCK_ENTRY.entry_id}",
        TEST_EVENT_TYPE,
        event_data,
    )
    await hass.async_block_till_done()

    # Get the entity (excluding pre-created validation entity)
    event_entities = get_non_precreated_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    assert len(event_entities) == 1
    entity_entry = event_entities[0]

    # Check entity category is DIAGNOSTIC
    assert entity_entry.entity_category == EntityCategory.DIAGNOSTIC

    # Check the unique_id contains the event type
    assert TEST_EVENT_TYPE in entity_entry.unique_id


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_event_entity_handles_webhook_event(hass: HomeAssistant) -> None:
    """Test that the event entity handles incoming webhook events."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    # Create entity via dispatcher
    from homeassistant.helpers.dispatcher import async_dispatcher_send

    initial_event_data = _create_test_event_data(
        MOCK_ENTRY.entry_id, event_ts=1000000000
    )
    async_dispatcher_send(
        hass,
        f"{SIGNAL_NEW_ZOOM_EVENT_TYPE}|{MOCK_ENTRY.entry_id}",
        TEST_EVENT_TYPE,
        initial_event_data,
    )
    await hass.async_block_till_done()

    # Get entity registry entry (excluding pre-created disabled entities)
    ent_reg = er.async_get(hass)
    event_entities = get_non_precreated_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    assert len(event_entities) == 1
    entity_id = event_entities[0].entity_id

    # Fire a second webhook event
    second_event_data = _create_test_event_data(
        MOCK_ENTRY.entry_id,
        event_ts=2000000000,
    )
    hass.bus.async_fire(HA_ZOOM_EVENT, second_event_data)
    await hass.async_block_till_done()

    # Check entity state has last_event_ts from the first event
    state = hass.states.get(entity_id)
    assert state is not None
    # After second event, last_event_ts should be from the first event
    assert state.attributes.get(ATTR_LAST_EVENT_TS) == 1000000000


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_event_entity_filters_by_config_entry(hass: HomeAssistant) -> None:
    """Test that event entities only respond to events for their config entry."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    # Create entity for MOCK_ENTRY
    from homeassistant.helpers.dispatcher import async_dispatcher_send

    event_data = _create_test_event_data(MOCK_ENTRY.entry_id, event_ts=1000000000)
    async_dispatcher_send(
        hass,
        f"{SIGNAL_NEW_ZOOM_EVENT_TYPE}|{MOCK_ENTRY.entry_id}",
        TEST_EVENT_TYPE,
        event_data,
    )
    await hass.async_block_till_done()

    ent_reg = er.async_get(hass)
    event_entities = get_non_precreated_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    entity_id = event_entities[0].entity_id

    # Get initial state
    initial_state = hass.states.get(entity_id)
    initial_last_changed = initial_state.last_changed

    # Fire event for a DIFFERENT config entry - should be ignored
    other_event_data = _create_test_event_data("other_entry_id", event_ts=3000000000)
    hass.bus.async_fire(HA_ZOOM_EVENT, other_event_data)
    await hass.async_block_till_done()

    # State should not have changed
    current_state = hass.states.get(entity_id)
    assert current_state.last_changed == initial_last_changed


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_event_entity_filters_by_event_type(hass: HomeAssistant) -> None:
    """Test that event entities only respond to their specific event type."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    # Create entity for meeting.started
    from homeassistant.helpers.dispatcher import async_dispatcher_send

    event_data = _create_test_event_data(MOCK_ENTRY.entry_id, event_ts=1000000000)
    async_dispatcher_send(
        hass,
        f"{SIGNAL_NEW_ZOOM_EVENT_TYPE}|{MOCK_ENTRY.entry_id}",
        TEST_EVENT_TYPE,
        event_data,
    )
    await hass.async_block_till_done()

    ent_reg = er.async_get(hass)
    event_entities = get_non_precreated_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    entity_id = event_entities[0].entity_id

    # Get initial state
    initial_state = hass.states.get(entity_id)
    initial_last_changed = initial_state.last_changed

    # Fire a DIFFERENT event type - should be ignored
    different_event_data = {
        ATTR_EVENT: "meeting.ended",
        ATTR_EVENT_TS: 3000000000,
        ATTR_PAYLOAD: {"object": {"id": "meeting123"}},
        "ha_config_entry_id": MOCK_ENTRY.entry_id,
    }
    hass.bus.async_fire(HA_ZOOM_EVENT, different_event_data)
    await hass.async_block_till_done()

    # State should not have changed
    current_state = hass.states.get(entity_id)
    assert current_state.last_changed == initial_last_changed


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_existing_entities_restored_on_startup(hass: HomeAssistant) -> None:
    """Test that existing event entities are recreated from registry on startup."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    # Create entity via dispatcher signal
    from homeassistant.helpers.dispatcher import async_dispatcher_send

    event_data = _create_test_event_data(MOCK_ENTRY.entry_id)
    async_dispatcher_send(
        hass,
        f"{SIGNAL_NEW_ZOOM_EVENT_TYPE}|{MOCK_ENTRY.entry_id}",
        TEST_EVENT_TYPE,
        event_data,
    )
    await hass.async_block_till_done()

    # Verify entity was created
    ent_reg = er.async_get(hass)
    event_entities = get_non_precreated_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    assert len(event_entities) == 1
    entity_id = event_entities[0].entity_id

    # Unload the entry
    await hass.config_entries.async_unload(MOCK_ENTRY.entry_id)
    await hass.async_block_till_done()

    # Entity should still be in registry
    event_entities = get_non_precreated_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    assert len(event_entities) == 1

    # Reload the entry - entities should be recreated from registry
    await hass.config_entries.async_setup(MOCK_ENTRY.entry_id)
    await hass.async_block_till_done()

    # Verify entity still exists with same entity_id
    event_entities = get_non_precreated_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    assert len(event_entities) == 1
    assert event_entities[0].entity_id == entity_id

    # Verify state is available (entity was properly recreated)
    state = hass.states.get(entity_id)
    assert state is not None


class TestZoomEventExtraStoredData:
    """Test ZoomEventExtraStoredData dataclass."""

    def test_as_dict(self) -> None:
        """Test as_dict method."""
        data = ZoomEventExtraStoredData(
            last_payload={"test": "payload"},
            last_event_ts=1234567890,
        )
        result = data.as_dict()
        assert result == {
            ATTR_LAST_PAYLOAD: {"test": "payload"},
            ATTR_LAST_EVENT_TS: 1234567890,
        }

    def test_as_dict_with_none(self) -> None:
        """Test as_dict with None values."""
        data = ZoomEventExtraStoredData(
            last_payload=None,
            last_event_ts=None,
        )
        result = data.as_dict()
        assert result == {
            ATTR_LAST_PAYLOAD: None,
            ATTR_LAST_EVENT_TS: None,
        }

    def test_from_dict(self) -> None:
        """Test from_dict class method."""
        input_dict = {
            ATTR_LAST_PAYLOAD: {"test": "payload"},
            ATTR_LAST_EVENT_TS: 1234567890,
        }
        data = ZoomEventExtraStoredData.from_dict(input_dict)
        assert data.last_payload == {"test": "payload"}
        assert data.last_event_ts == 1234567890

    def test_from_dict_missing_keys(self) -> None:
        """Test from_dict with missing keys defaults to None."""
        data = ZoomEventExtraStoredData.from_dict({})
        assert data.last_payload is None
        assert data.last_event_ts is None
