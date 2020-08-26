"""Sensor platform for Zoom Automation."""
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from .common import ZoomBaseEntity

SCAN_INTERVAL = timedelta(hours=1)


async def async_setup_entry(
    hass: HomeAssistantType,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up a Zoom Automation profile sensor entry."""
    async_add_entities([ZoomProfileSensor(hass, config_entry)], update_before_add=True)


class ZoomProfileSensor(ZoomBaseEntity):
    """Class for a Zoom Automation user profile sensor."""

    def __init__(self, hass: HomeAssistantType, config_entry: ConfigEntry) -> None:
        super().__init__(hass, config_entry)
        self._profile: dict = {}

    async def async_update(self) -> None:
        self._profile = await self._api.async_get_user_profile()

    @property
    def name(self) -> str:
        """Entity name."""
        return f"Zoom {self._name} User Profile"

    @property
    def state(self) -> str:
        """Entity state."""
        return self._profile["id"]

    @property
    def state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return the state attributes."""
        return {
            "id": self._profile["id"],
            "first_name": self._profile["first_name"],
            "last_name": self._profile["last_name"],
            "email": self._profile["email"],
            "account_id": self._profile["account_id"],
        }
