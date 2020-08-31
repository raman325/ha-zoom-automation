"""Sensor platform for Zoom."""
from logging import getLogger
from typing import Any, Dict, List, Optional

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import Event
from homeassistant.helpers.config_entry_oauth2_flow import DATA_IMPLEMENTATIONS
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
        [ZoomAuthenticatedUserBinarySensor(hass, config_entry)], update_before_add=True
    )


def get_data_from_path(data: Dict[str, Any], path: List[str]) -> Optional[str]:
    """Get value from dictionary using path list."""
    for val in path:
        data = data.get(val, {})

    if isinstance(data, str):
        return data
    return None


class ZoomBaseBinarySensor(RestoreEntity, ZoomBaseEntity, BinarySensorEntity):
    """Base class for Zoom binary_sensor."""

    def __init__(self, hass: HomeAssistantType, config_entry: ConfigEntry) -> None:
        """Initialize base sensor."""
        super().__init__(hass, config_entry)
        self._zoom_event_state = None
        self._state = STATE_OFF

    def _get_id(self) -> Optional[str]:
        """Get user ID."""
        raise NotImplemented

    def _get_user_profile(self) -> Optional[Dict[str, str]]:
        """Get user profile."""
        raise NotImplemented

    def _set_state(self, zoom_event_state: Optional[str]) -> None:
        """Set Zoom and HA state."""
        self._zoom_event_state = zoom_event_state
        self._state = (
            STATE_ON
            if self._zoom_event_state
            and self._zoom_event_state.lower() == CONNECTIVITY_STATUS_ON.lower()
            else STATE_OFF
        )
        _LOGGER.debug(
            "Set Zoom state to %s and HA state to %s", zoom_event_state, self._state
        )
        self.async_write_ha_state()

    async def async_event_received(self, event: Event) -> None:
        """Update status if event received for this entity."""
        if (
            event.data[ATTR_EVENT] == CONNECTIVITY_EVENT
            and get_data_from_path(event.data, CONNECTIVITY_ID).lower()
            == self._get_id().lower()
        ):
            self._set_state(get_data_from_path(event.data, CONNECTIVITY_STATUS))

    async def _restore_state(self) -> None:
        """Restore state from last known state."""
        restored_state = await self.async_get_last_state()
        if restored_state:
            self._state = restored_state.state

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        await super().async_added_to_hass()

        # Register callback for webhook event
        self._async_unsub_listeners.append(
            self.hass.bus.async_listen(HA_ZOOM_EVENT, self.async_event_received)
        )

        id = self._get_id()
        if not id:
            _LOGGER.debug("ID not found, restoring state.")
            await self._restore_state()

        try:
            contact = await self._api.async_get_contact_user_profile(id)
            status = contact["presence_status"]
            _LOGGER.debug("Retrieved initial Zoom status: %s", status)
            self._set_state(status)
        except:
            _LOGGER.warning(
                "Error retrieving initial zoom status, restoring state.", exc_info=True
            )
            await self._restore_state()

    @property
    def name(self) -> str:
        """Entity name."""
        raise NotImplemented

    @property
    def state(self) -> str:
        """Entity state."""
        return self._state

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.state == STATE_ON

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
        data = {}
        user_profile = self._get_user_profile()
        if user_profile:
            data.update(
                {
                    "id": user_profile.get("id"),
                    "first_name": user_profile.get("first_name"),
                    "last_name": user_profile.get("last_name"),
                    "email": user_profile.get("email"),
                }
            )
            account_id = user_profile.get("account_id")
            if account_id:
                data["account_id"] = account_id

        if self._zoom_event_state:
            data["status"] = self._zoom_event_state

        return data if DATA_IMPLEMENTATIONS else None


class ZoomAuthenticatedUserBinarySensor(ZoomBaseBinarySensor):
    """Class for Zoom user profile binary sensor for authenticated user."""

    def _get_id(self) -> Optional[str]:
        """Get user ID."""
        return self._coordinator.data.get("id", "")

    def _get_user_profile(self) -> Optional[Dict[str, str]]:
        """Get user profile."""
        return self._coordinator.data

    @property
    def name(self) -> str:
        """Entity name."""
        return f"Zoom {self._name}"


class ZoomContactUserBinarySensor(ZoomBaseBinarySensor):
    """Class for Zoom user profile binary sensor for contacts of authenticated user."""

    def __init__(
        self, hass: HomeAssistantType, config_entry: ConfigEntry, id: str
    ) -> None:
        """Initialize entity."""
        super().__init__(hass, config_entry)
        self._id = id
        self._profile = None

    async def async_update(self) -> None:
        """Update state of entity."""
        self._profile = await self._api.async_get_contact_user_profile(self._id)
        self._zoom_event_state = self._profile["presence_status"]

    def _get_id(self) -> Optional[str]:
        """Get user ID."""
        return self._id

    def _get_user_profile(self) -> Optional[Dict[str, str]]:
        """Get user profile."""
        return self._profile

    @property
    def name(self) -> str:
        """Entity name."""
        return f"Zoom {self._name}"

    @property
    def should_poll(self) -> bool:
        """Should entity be polled."""
        return True
