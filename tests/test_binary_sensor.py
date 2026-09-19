"""Test Zoom binary sensor platform."""

from datetime import timedelta
from unittest.mock import patch

from homeassistant.core import HomeAssistant, State
from homeassistant.setup import async_setup_component
import pytest
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    mock_restore_cache,
)

from custom_components.zoom.const import (
    ATTR_EVENT,
    ATTR_PAYLOAD,
    CONNECTIVITY_EVENT,
    DOMAIN,
    HA_ZOOM_EVENT,
)

from .const import MOCK_ENTRY

ENTITY_ID = "binary_sensor.zoom_test"
SCAN_INTERVAL = timedelta(seconds=30)


def _presence_event(status: str) -> dict:
    """Build a presence webhook event for the mock entry."""
    return {
        ATTR_EVENT: CONNECTIVITY_EVENT,
        ATTR_PAYLOAD: {"object": {"id": "test", "presence_status": status}},
        "ha_config_entry_id": MOCK_ENTRY.entry_id,
    }


@pytest.fixture(name="presence")
def presence_fixture():
    """Mock the polled user profile with a mutable presence status."""
    profile = {"id": "test", "presence_status": "Available"}
    with patch(
        "custom_components.zoom.common.ZoomAPI.async_get_contact_user_profile",
        return_value=profile,
    ):
        yield profile


async def _advance(hass: HomeAssistant, freezer, seconds: int) -> None:
    """Move time forward and let the polling interval fire."""
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


@pytest.mark.usefixtures("enable_custom_integrations", "presence")
async def test_setup(hass: HomeAssistant) -> None:
    """Test the binary sensor is created from the polled presence status."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == "off"
    assert state.attributes["status"] == "Available"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_setup_translates_the_profile_vocabulary(
    hass: HomeAssistant, presence: dict
) -> None:
    """Test the initial profile status uses the webhook vocabulary."""
    presence["presence_status"] = "In_A_Meeting"
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["status"] == "In_Meeting"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_setup_restores_state_for_an_unrecognised_status(
    hass: HomeAssistant, presence: dict
) -> None:
    """Test an unknown initial profile status does not clear restored state."""
    presence["presence_status"] = "Something_Zoom_Invented"
    mock_restore_cache(hass, [State(ENTITY_ID, "on")])
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state.state == "on"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_poll_corrects_missed_webhook(
    hass: HomeAssistant, freezer, presence: dict
) -> None:
    """Test a status change we never got a webhook for is picked up by the poll.

    Webhooks are missed whenever Home Assistant is restarted mid-call or Zoom
    fails to deliver one, and nothing else would ever correct the state.
    """
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "off"

    # Zoom knows we joined a call, but no webhook ever arrives.
    presence["presence_status"] = "In_Meeting"
    await _advance(hass, freezer, 31)

    state = hass.states.get(ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["status"] == "In_Meeting"

    # ...and the same in reverse when the call ends.
    presence["presence_status"] = "Available"
    await _advance(hass, freezer, 31)
    assert hass.states.get(ENTITY_ID).state == "off"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_poll_does_not_undo_a_fresh_webhook(
    hass: HomeAssistant, freezer, presence: dict
) -> None:
    """Test the API lagging behind a webhook doesn't flap the state back."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "off"

    hass.bus.async_fire(HA_ZOOM_EVENT, _presence_event("In_Meeting"))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "on"

    # The REST API can still be serving the status the webhook just replaced,
    # so a poll inside the grace period must not overwrite it.
    await _advance(hass, freezer, 31)
    assert hass.states.get(ENTITY_ID).state == "on"

    # Once the grace period is over the poll is authoritative again.
    await _advance(hass, freezer, 61)
    assert hass.states.get(ENTITY_ID).state == "off"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_unavailable_when_zoom_is_unreachable(
    hass: HomeAssistant, freezer, presence: dict
) -> None:
    """Test the sensor goes unavailable and recovers with the current status."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "off"

    with patch(
        "custom_components.zoom.common.ZoomAPI.async_get_contact_user_profile",
        side_effect=Exception("boom"),
    ):
        await _advance(hass, freezer, 31)
        assert hass.states.get(ENTITY_ID).state == "unavailable"

    presence["presence_status"] = "In_Meeting"
    await _advance(hass, freezer, 31)
    assert hass.states.get(ENTITY_ID).state == "on"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_poll_translates_the_profile_vocabulary(
    hass: HomeAssistant, freezer, presence: dict
) -> None:
    """Test the profile's spelling of a status is matched against the webhook's.

    The user profile endpoint says "In_A_Meeting" where the webhook says
    "In_Meeting", and only the webhook's spelling can appear in the configured
    "on" statuses, so an untranslated poll reads as "not on a call".
    """
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "off"

    presence["presence_status"] = "In_A_Meeting"
    await _advance(hass, freezer, 31)

    state = hass.states.get(ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["status"] == "In_Meeting"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_poll_ignores_an_unrecognised_status(
    hass: HomeAssistant, freezer, presence: dict
) -> None:
    """Test a status we can't interpret doesn't clear a state a webhook set.

    A webhook is an event - an unrecognised status is evidence the user is no
    longer on a call. The poll is only a cross-check, so a status it can't
    interpret is no evidence at all.
    """
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    hass.bus.async_fire(HA_ZOOM_EVENT, _presence_event("In_Meeting"))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "on"

    presence["presence_status"] = "Something_Zoom_Invented"
    await _advance(hass, freezer, 31)   # inside the grace period
    await _advance(hass, freezer, 61)   # and outside it
    await _advance(hass, freezer, 31)

    state = hass.states.get(ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["status"] == "In_Meeting"
