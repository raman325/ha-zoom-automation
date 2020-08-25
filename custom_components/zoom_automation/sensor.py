"""Sensor platform for Zoom Automation."""
from datetime import timedelta
from typing import Any, Callable, Dict, List, Optional

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType

from custom_components.zoom_automation.api import ZoomAPI

from .const import BASE_URL, DOMAIN, USER_PROFILE

SCAN_INTERVAL = timedelta(days=1)


async def async_setup_entry(
    hass: HomeAssistantType,
    config_entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None],
) -> None:
    """Set up a Zoom Automation profile sensor entry."""
    name = config_entry.data[CONF_NAME]
    api = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        [ZoomProfileSensor(name, api)], update_before_add=True
    )


class ZoomProfileSensor(Entity):
    """Class for a Zoom Automation user profile sensor."""

    def __init__(self, name: str, api: ZoomAPI) -> None:
        """Initialize base sensor."""
        self._api = api
        self._name = name
        self._id: str = ""
        self.first_name: str = ""
        self.last_name: str = ""
        self.email: str = ""
        self.account_id: str = ""

    async def async_update(self) -> None:
        resp = await self._api._oauth_session.async_request(
            "get", f"{BASE_URL}{USER_PROFILE}", raise_for_status=True
        )
        profile = await resp.json()
        self._id = profile["id"]
        self.first_name = profile["first_name"]
        self.last_name = profile["last_name"]
        self.email = profile["email"]
        self.account_id = profile["account_id"]

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
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "account_id": self.account_id,
        }
