"""Sensor platform for Zoom."""
from logging import getLogger
from typing import Any, Dict, List, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    DEVICE_CLASS_CONNECTIVITY,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import Event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import HomeAssistantType

from .common import ZoomBaseEntity
from .const import (
    ATTR_EVENT,
    CONNECTIVITY_EVENT,
    CONNECTIVITY_ID,
    CONNECTIVITY_STATUS,
    CONNECTIVITY_STATUS_ON,
    HA_ZOOM_EVENT,
)

_LOGGER = getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up a Zoom presence sensor entry."""
    async_add_entities(
        [ZoomConnectivitySensor(hass, config_entry)], update_before_add=True
    )


def get_data_from_path(data: Dict[str, Any], path: List[str]) -> Optional[str]:
    """Get value from dictionary using path list."""
    for val in path:
        data = data.get(val, {})

    if isinstance(data, str):
        return data
    return None


class ZoomConnectivitySensor(RestoreEntity, ZoomBaseEntity, BinarySensorEntity):
    """Class for a Zoom user profile sensor."""

    def __init__(self, hass: HomeAssistantType, config_entry: ConfigEntry) -> None:
        """Initialize base sensor."""
        super().__init__(hass, config_entry)
        self._zoom_event_state = None
        self._state = STATE_OFF

    async def async_event_received(self, event: Event) -> None:
        """Update status if event received for this entity."""
        if (
            event.data[ATTR_EVENT] == CONNECTIVITY_EVENT
            and get_data_from_path(event.data, CONNECTIVITY_ID).lower()
            == self._coordinator.data.get("id", "").lower()
        ):
            self._zoom_event_state = get_data_from_path(event.data, CONNECTIVITY_STATUS)
            self._state = (
                STATE_ON
                if self._zoom_event_state
                and self._zoom_event_state.lower() == CONNECTIVITY_STATUS_ON.lower()
                else STATE_OFF
            )
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        await super().async_added_to_hass()

        # Register callback for webhook event
        self._async_unsub_listeners.append(
            self.hass.bus.async_listen(HA_ZOOM_EVENT, self.async_event_received)
        )

        restored_state = await self.async_get_last_state()
        if restored_state:
            self._state = restored_state.state

    @property
    def name(self) -> str:
        """Entity name."""
        return f"Zoom {self._name}"

    @property
    def state(self) -> str:
        """Entity state."""
        return self._state

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self._state == STATE_ON

    @property
    def assumed_state(self) -> bool:
        """Return True if unable to access real state of the entity."""
        return True

    @property
    def icon(self) -> str:
        """Entity icon."""
        return "mdi:do-not-disturb"

    @property
    def device_class(self) -> str:
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return additional state attributes."""
        return {"status": self._zoom_event_state} if self._zoom_event_state else None
