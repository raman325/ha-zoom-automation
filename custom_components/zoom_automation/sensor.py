"""Sensor platform for Zoom Automation."""
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType

from custom_components.zoom_automation.api import ZoomAPI

from .const import DOMAIN

SCAN_INTERVAL = timedelta(days=1)


async def async_setup_entry(
    hass: HomeAssistantType, config_entry: ConfigEntry, async_add_entities,
) -> None:
    """Set up a Zoom Automation profile sensor entry."""
    async_add_entities([ZoomProfileSensor(hass, config_entry)], update_before_add=True)


class ZoomProfileSensor(Entity):
    """Class for a Zoom Automation user profile sensor."""

    def __init__(self, hass: HomeAssistantType, config_entry: ConfigEntry) -> None:
        """Initialize base sensor."""
        self._api: ZoomAPI = hass.data[DOMAIN][config_entry.entry_id]
        self._name: str = config_entry.data[CONF_NAME]
        self._id: str = ""
        self._first_name: str = ""
        self._last_name: str = ""
        self._email: str = ""
        self._account_id: str = ""

    async def async_update(self) -> None:
        profile = await self._api.async_get_user_profile()
        self._id = profile["id"]
        self._first_name = profile["first_name"]
        self._last_name = profile["last_name"]
        self._email = profile["email"]
        self._account_id = profile["account_id"]

    @property
    def name(self) -> str:
        """Entity name."""
        return f"Zoom {self._name} User Profile"

    @property
    def state(self) -> str:
        """Entity state."""
        return self._id

    @property
    def state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return the state attributes."""
        return {
            "id": self._id,
            "first_name": self._first_name,
            "last_name": self._last_name,
            "email": self._email,
            "account_id": self._account_id,
        }
