"""Event platform for Zoom."""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import Any

from homeassistant.components.event import DOMAIN as EVENT_DOMAIN, EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EntityCategory
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get as async_get_entity_registry,
)
from homeassistant.helpers.restore_state import ExtraStoredData, RestoreEntity
from homeassistant.util import slugify

from .const import (
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

# Event types disabled by default (redundant with other entities or internal)
_DISABLED_BY_DEFAULT_EVENTS = {VALIDATION_EVENT, CONNECTIVITY_EVENT}

_LOGGER = getLogger(__name__)


@dataclass
class ZoomEventExtraStoredData(ExtraStoredData):
    """Extra stored data for Zoom event entities."""

    last_payload: dict[str, Any] | None
    last_event_ts: int | None

    def as_dict(self) -> dict[str, Any]:
        """Return a dict representation of the extra data."""
        return {
            ATTR_LAST_PAYLOAD: self.last_payload,
            ATTR_LAST_EVENT_TS: self.last_event_ts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ZoomEventExtraStoredData:
        """Create extra stored data from a dict."""
        return cls(
            last_payload=data.get(ATTR_LAST_PAYLOAD),
            last_event_ts=data.get(ATTR_LAST_EVENT_TS),
        )


def get_zoom_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Extract Zoom-specific data from the webhook event data."""
    return {k: v for k, v in data.items() if k in (ATTR_EVENT_TS, ATTR_PAYLOAD)}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zoom event entities."""

    @callback
    def async_add_event_entity(
        event_type: str, data: dict[str, Any] | None = None
    ) -> None:
        """Add a new event entity when a new event type is discovered."""
        # Only handle events for this config entry
        _LOGGER.info(
            "Creating event entity for Zoom event type: %s (config entry: %s)",
            event_type,
            config_entry.entry_id,
        )
        entity = ZoomWebhookEventEntity(config_entry, event_type, data)
        async_add_entities([entity])

    # Listen for dispatcher signal to add new entities
    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{SIGNAL_NEW_ZOOM_EVENT_TYPE}|{config_entry.entry_id}",
            async_add_event_entity,
        )
    )

    # Recreate existing event entities from the registry and add validation entity
    ent_reg = async_get_entity_registry(hass)

    # Extract event types from existing entities (format: zoom_{name}|{event_type})
    existing_event_types = {
        entity.unique_id.split("|", 1)[1]
        for entity in async_entries_for_config_entry(ent_reg, config_entry.entry_id)
        if entity.domain == EVENT_DOMAIN and "|" in entity.unique_id
    }

    # Always include these events:
    # - VALIDATION_EVENT: sent by Zoom every 72 hours for revalidation
    # - CONNECTIVITY_EVENT: used by the binary sensor for presence tracking
    existing_event_types.add(VALIDATION_EVENT)
    existing_event_types.add(CONNECTIVITY_EVENT)

    # Create entities for all event types
    async_add_entities(
        [
            ZoomWebhookEventEntity(config_entry, event_type)
            for event_type in existing_event_types
        ]
    )


class ZoomWebhookEventEntity(EventEntity, RestoreEntity):
    """Represents a single Zoom webhook event type."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        config_entry: ConfigEntry,
        event_type: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the event entity."""
        self._config_entry = config_entry
        self._event_type = event_type
        self._init_data: dict[str, Any] | None = data
        self._last_payload: dict[str, Any] | None = None
        self._last_event_ts: int | None = None

        # Disable by default for events that are redundant or internal
        self._attr_entity_registry_enabled_default = (
            event_type not in _DISABLED_BY_DEFAULT_EVENTS
        )

        # Unique ID: zoom_{entry_id}_{slugified_event_type}
        self._attr_unique_id = (
            f"{DOMAIN}_{slugify(config_entry.data[CONF_NAME])}|{event_type}"
        )

        # Entity name: Clean up event type for display
        # e.g., "user.presence_status_updated" -> "Presence Status Updated"
        name = self._config_entry.data[CONF_NAME]
        display_event_type = event_type
        if "." in display_event_type:
            display_event_type = display_event_type.split(".")[-1]
        self._attr_name = f"{name} {display_event_type.replace('_', ' ').title()}"

        # EventEntity requires event_types list - we support exactly this one type
        self._attr_event_types = [self._event_type]

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes with last event payload."""
        attrs: dict[str, Any] = {}
        if self._last_event_ts is not None:
            attrs[ATTR_LAST_EVENT_TS] = self._last_event_ts
        if self._last_payload is not None:
            attrs[ATTR_LAST_PAYLOAD] = self._last_payload

        return attrs if attrs else None

    @property
    def extra_restore_state_data(self) -> ZoomEventExtraStoredData:
        """Return extra state data to be stored for restoration."""
        return ZoomEventExtraStoredData(
            last_payload=self._last_payload,
            last_event_ts=self._last_event_ts,
        )

    @callback
    def _filter_event(self, event_data: dict[str, Any]) -> bool:
        """Filter incoming webhook events for this entity."""
        # Only handle events for this config entry and event type
        return (
            event_data.get("ha_config_entry_id") == self._config_entry.entry_id
            and event_data.get(ATTR_EVENT) == self._event_type
        )

    @callback
    def _handle_event(self, event: Event) -> None:
        """Handle incoming webhook event."""
        data = event.data

        # Capture current event_ts/payload from state as the "last" values
        # before we trigger the new event
        if (state := self.hass.states.get(self.entity_id)) and all(
            _attr in state.attributes for _attr in (ATTR_EVENT_TS, ATTR_PAYLOAD)
        ):
            self._last_event_ts = state.attributes[ATTR_EVENT_TS]
            self._last_payload = state.attributes[ATTR_PAYLOAD]

        # Trigger the event (updates entity state timestamp)
        self._trigger_event(self._event_type, get_zoom_dict(data))
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register event listener when entity is added."""
        await super().async_added_to_hass()

        # Fire event for initial data if present (only possible when receiving this
        # event type for the first time)
        if self._init_data:
            self._trigger_event(self._event_type, get_zoom_dict(self._init_data))
            self.async_write_ha_state()
            self._init_data = None
        # Restore previous state if available
        elif extra_data := await self.async_get_last_extra_data():
            restored = ZoomEventExtraStoredData.from_dict(extra_data.as_dict())
            self._last_payload = restored.last_payload
            self._last_event_ts = restored.last_event_ts
            _LOGGER.debug(
                "Restored state for %s: event_ts=%s",
                self.entity_id,
                self._last_event_ts,
            )
            self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(
                HA_ZOOM_EVENT,
                self._handle_event,
                self._filter_event,
            )
        )
