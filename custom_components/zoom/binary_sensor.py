"""Sensor platform for Zoom."""
from __future__ import annotations

from datetime import datetime, timedelta
from logging import getLogger
from typing import Any

from aiohttp.web import HTTPUnauthorized
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_NAME
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify
from homeassistant.util.dt import utcnow

from .common import ZoomAPI, ZoomUserProfileDataUpdateCoordinator, get_contact_name
from .const import (
    ALL_CONNECTIVITY_STATUSES,
    API,
    ATTR_EVENT,
    CONF_CONNECTIVITY_ON_STATUSES,
    CONNECTIVITY_EVENT,
    CONNECTIVITY_ID,
    CONNECTIVITY_STATUS,
    DEFAULT_CONNECTIVITY_ON_STATUSES,
    DOMAIN,
    HA_ZOOM_EVENT,
    POLLED_STATUS_ALIASES,
    USER_PROFILE_COORDINATOR,
)

_LOGGER = getLogger(__name__)

ISSUE_URL = "https://github.com/raman325/ha-zoom-automation/issues"

SCAN_INTERVAL = timedelta(seconds=30)
PARALLEL_UPDATES = 5

# How long a webhook's status is trusted over the polled one. Zoom's REST API
# lags its webhooks by a few seconds, so a poll landing right after an event
# can still report the previous status.
WEBHOOK_GRACE_PERIOD = timedelta(seconds=60)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up a Zoom presence sensor entry."""
    # Set default options
    if not config_entry.options:
        hass.config_entries.async_update_entry(
            config_entry,
            options={CONF_CONNECTIVITY_ON_STATUSES: DEFAULT_CONNECTIVITY_ON_STATUSES},
        )
    entity = ZoomAuthenticatedUserBinarySensor(hass, config_entry)
    async_add_entities([entity], update_before_add=True)


def get_data_from_path(data: dict[str, Any], path: list[str]) -> str | None:
    """Get value from dictionary using path list."""
    for val in path:
        data = data.get(val, {})

    if isinstance(data, str):
        return data
    return None


class ZoomBaseBinarySensor(RestoreEntity, BinarySensorEntity):
    """Base class for Zoom binary_sensor."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize base sensor."""
        self._config_entry = config_entry
        self._hass = hass
        self._coordinator: ZoomUserProfileDataUpdateCoordinator = hass.data[DOMAIN][
            config_entry.entry_id
        ][USER_PROFILE_COORDINATOR]
        self._api: ZoomAPI = hass.data[DOMAIN][config_entry.entry_id][API]
        self._name: str = config_entry.data[CONF_NAME]
        self._profile = None
        self._zoom_event_state = None
        self._last_webhook_dt: datetime | None = None
        self._unknown_status: str | None = None
        self._is_on = False

        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_unique_id = f"{DOMAIN}_{slugify(self._name)}"
        self._attr_available = True
        self._attr_should_poll = False

    def _in_webhook_grace_period(self) -> bool:
        """Return whether a webhook arrived too recently to be polled over."""
        return (
            self._last_webhook_dt is not None
            and utcnow() - self._last_webhook_dt < WEBHOOK_GRACE_PERIOD
        )

    def _normalize_polled_status(self, status: str | None) -> str | None:
        """Translate a polled status, returning None if it is unknown."""
        status = POLLED_STATUS_ALIASES.get(status, status)
        if status in ALL_CONNECTIVITY_STATUSES:
            return status

        # A webhook is an event - it says the status just became X, and an X
        # we don't recognise is fair evidence the user isn't on a call. A
        # profile response is only a cross-check, so a status we can't
        # interpret is no evidence and must not be allowed to clear the state.
        if status != self._unknown_status:
            self._unknown_status = status
            _LOGGER.warning(
                "Zoom's user profile reports presence status %s, which this "
                "integration doesn't recognise; leaving the state unchanged. "
                "Please report this at %s",
                status,
                ISSUE_URL,
            )
        return None

    async def _async_update(self, now) -> None:
        """Update state of entity."""
        if not self.id:
            return

        try:
            self._profile = await self._api.async_get_contact_user_profile(self.id)
        except Exception:
            # If API call fails we can assume we can't talk to Zoom
            if self._attr_available:
                _LOGGER.warning(
                    "Unable to reach Zoom, we may miss status updates until we "
                    "can connect again"
                )
                self._attr_available = False
                self.async_write_ha_state()
            return

        if not self._attr_available:
            _LOGGER.info("We can reach Zoom again, resuming polling for current status")
            self._attr_available = True

        # A webhook we never receive leaves our state wrong until the next one
        # arrives, so the poll has to be able to correct it - not only when
        # recovering from an outage. Skip the correction right after an event,
        # since the API can still be reporting the status the webhook replaced.
        status = self._normalize_polled_status(self._profile.get("presence_status"))
        if (
            status is not None
            and status != self._zoom_event_state
            and not self._in_webhook_grace_period()
        ):
            _LOGGER.debug(
                "Polled status %s doesn't match last known status %s, correcting",
                status,
                self._zoom_event_state,
            )
            self._set_state(status)

        self.async_write_ha_state()

    async def _restore_state(self) -> None:
        """Restore state from last known state."""
        restored_state = await self.async_get_last_state()
        if restored_state:
            self._is_on = restored_state.state == "on"

    @staticmethod
    async def _async_send_update_options_signal(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> None:
        """Send update event when Zoom config entry is updated."""
        async_dispatcher_send(hass, config_entry.entry_id)

    async def _async_update_options(self) -> None:
        """Update options if the update signal comes from this entity."""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        await super().async_added_to_hass()

        # Register callback for when config entry is updated.
        self.async_on_remove(
            self._config_entry.add_update_listener(
                self._async_send_update_options_signal
            )
        )

        # Register callback for update event
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._config_entry.entry_id, self._async_update_options
            )
        )

        # Update state when coordinator updates
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

        # Manually set an update interval so we can disable it if needed
        self.async_on_remove(
            async_track_time_interval(
                self._hass, self._async_update, timedelta(seconds=30)
            )
        )

        if self.id:
            try:
                self._profile = await self._api.async_get_contact_user_profile(self.id)
                status = self._normalize_polled_status(
                    self._profile.get("presence_status")
                )
                _LOGGER.debug("Retrieved initial Zoom status: %s", status)
                if status is None:
                    await self._restore_state()
                else:
                    self._set_state(status)
                    self.async_write_ha_state()
            except HTTPUnauthorized:
                _LOGGER.debug(
                    "User is unauthorized to query presence status, restoring state.",
                    exc_info=True,
                )
                await self._restore_state()
            except Exception:
                _LOGGER.warning(
                    "Error retrieving initial zoom status, restoring state.",
                    exc_info=True,
                )
                await self._restore_state()
        else:
            _LOGGER.debug("ID is unknown, restoring state.")
            await self._restore_state()

    def _set_state(self, zoom_event_state: str | None) -> None:
        """Set Zoom and HA state."""
        self._zoom_event_state = zoom_event_state
        self._is_on = (
            self._zoom_event_state
            and self._zoom_event_state
            in self._config_entry.options[CONF_CONNECTIVITY_ON_STATUSES]
        )
        _LOGGER.debug(
            "Set Zoom state to %s and HA state to %s", zoom_event_state, self._is_on
        )

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self._is_on

    @property
    def icon(self) -> str:
        """Entity icon."""
        if self.is_on:
            return "mdi:video"
        return "mdi:video-off"

    @property
    def profile(self) -> dict[str, str]:
        """Get user profile."""
        return self._profile or {}

    @property
    def first_name(self) -> str | None:
        """Return the first name."""
        return self.profile.get("first_name")

    @property
    def last_name(self) -> str | None:
        """Return the last name."""
        return self.profile.get("last_name")

    @property
    def id(self) -> str | None:
        """Return the id."""
        return self._config_entry.data.get(CONF_ID) or self.profile.get("id")

    @property
    def email(self) -> str | None:
        """Return the email."""
        return self.profile.get("email")

    @property
    def account_id(self) -> str | None:
        """Return the account_id."""
        return self.profile.get("account_id")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        data = {}

        for prop in ["id", "first_name", "last_name", "email", "account_id"]:
            val = getattr(self, prop)
            if val:
                data[prop] = val

        if self._zoom_event_state:
            data["status"] = self._zoom_event_state

        return data if data else None


class ZoomAuthenticatedUserBinarySensor(ZoomBaseBinarySensor):
    """Class for Zoom user profile binary sensor for authenticated user."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize Zoom user profile binary sensor for authenticated user."""
        super().__init__(hass, config_entry)
        self._attr_name = f"Zoom - {self._name}"

    async def async_event_received(self, event: Event) -> None:
        """Update status if event received for this entity."""
        status = event.data
        if (
            status["ha_config_entry_id"] == self._config_entry.entry_id
            and status[ATTR_EVENT] == CONNECTIVITY_EVENT
            and get_data_from_path(status, CONNECTIVITY_ID).lower() == self.id.lower()
        ):
            self._last_webhook_dt = utcnow()
            self._set_state(get_data_from_path(status, CONNECTIVITY_STATUS))
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        await super().async_added_to_hass()
        # Register callback for webhook event
        self.async_on_remove(
            self.hass.bus.async_listen(f"{HA_ZOOM_EVENT}", self.async_event_received)
        )

    @property
    def assumed_state(self) -> bool:
        """Return True if unable to access real state of the entity."""
        return not self.available

    @property
    def profile(self) -> dict[str, str]:
        """Get user profile."""
        return self._profile or self._coordinator.data or {}


class ZoomContactUserBinarySensor(ZoomBaseBinarySensor):
    """Class for Zoom user profile binary sensor for contacts of authenticated user."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, id: str
    ) -> None:
        """Initialize entity."""
        super().__init__(hass, config_entry)
        self._id = id

        self._attr_unique_id = f"{super().unique_id}_{id}"
        self._attr_should_poll = True
        self._attr_name = (
            f"Zoom - {self._name}'s Contact - {get_contact_name(self.profile)}"
        )

    @property
    def id(self) -> str | None:
        """Get user ID."""
        return self._id
