"""Sensor platform for Zoom Automation."""
from logging import getLogger
from typing import Any, Dict, List, Optional

from homeassistant.components.binary_sensor import DEVICE_CLASS_CONNECTIVITY
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import Event
from homeassistant.helpers.typing import HomeAssistantType

from .common import ZoomBaseEntity
from .const import (
    ATTR_EVENT,
    CONNECTIVITY_EVENT,
    CONNECTIVITY_ID,
    CONNECTIVITY_STATUS,
    CONNECTIVITY_STATUS_OFF,
    HA_CONNECTIVITY_EVENT,
)

_LOGGER = getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up a Zoom Automation presence sensor entry."""
    async_add_entities(
        [ZoomConnectivitySensor(hass, config_entry)],
        update_before_add=True,
    )


def get_data_from_path(data: Dict[str, Any], path: List[str]) -> Optional[str]:
    """Get value from dictionary using path list."""
    for val in path:
        data = data.get(val, {})

    if isinstance(data, str):
        return data
    return None


class ZoomConnectivitySensor(ZoomBaseEntity):
    """Class for a Zoom Automation user profile sensor."""

    def __init__(self, hass: HomeAssistantType, config_entry: ConfigEntry) -> None:
        """Initialize base sensor."""
        super().__init__(hass, config_entry)
        self._state: str = STATE_OFF
        self._async_unsub_listeners = []

    async def async_update_status(self, event: Event):
        """Update status if webhook event received for this entity."""
        profile = await self._api.async_get_user_profile()

        if (
            event.data[ATTR_EVENT] == CONNECTIVITY_EVENT
            and get_data_from_path(event.data, CONNECTIVITY_ID).lower()
            == profile["id"].lower()
        ):
            self._state = (
                STATE_OFF
                if get_data_from_path(event.data, CONNECTIVITY_STATUS).lower()
                == CONNECTIVITY_STATUS_OFF.lower()
                else STATE_ON
            )

            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        # Register callback for webhook event
        self._async_unsub_listeners.append(
            self.hass.bus.async_listen(HA_CONNECTIVITY_EVENT, self.async_update_status)
        )

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect callbacks when entity is removed."""
        for listener in self._async_unsub_listeners:
            listener()

        self._async_unsub_listeners.clear()

    @property
    def name(self) -> str:
        """Entity name."""
        return f"Zoom {self._name}"

    @property
    def state(self) -> str:
        """Entity state."""
        return self._state

    @property
    def should_poll(self) -> bool:
        """Should entity be polled."""
        return False

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_CONNECTIVITY
