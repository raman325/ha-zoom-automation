"""Sensor platform for Zoom."""
from datetime import timedelta
from logging import getLogger
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from .common import ZoomBaseEntity

SCAN_INTERVAL = timedelta(hours=1)

_LOGGER = getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up a Zoom profile sensor entry."""
    async_add_entities([ZoomProfileSensor(hass, config_entry)], update_before_add=True)


class ZoomProfileSensor(ZoomBaseEntity):
    """Class for a Zoom user profile sensor."""

    @property
    def name(self) -> str:
        """Entity name."""
        return f"Zoom {self._name} User Profile"

    @property
    def state(self) -> str:
        """Entity state."""
        return self._coordinator.data.get("email")

    @property
    def icon(self) -> str:
        """Entity icon."""
        return "mdi:account-details"

    @property
    def should_poll(self) -> bool:
        """Should entity be polled."""
        return False

    @property
    def state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return the state attributes."""
        return {
            "id": self._coordinator.data.get("id"),
            "first_name": self._coordinator.data.get("first_name"),
            "last_name": self._coordinator.data.get("last_name"),
            "email": self._coordinator.data.get("email"),
            "account_id": self._coordinator.data.get("account_id"),
        }
