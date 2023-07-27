"""Test zoom init."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import DATA_IMPLEMENTATIONS
from homeassistant.setup import async_setup_component

from custom_components.zoom.common import ZoomOAuth2Implementation
from custom_components.zoom.const import DOMAIN

from .const import MOCK_CONFIG, MOCK_ENTRY


async def test_component_setup(hass: HomeAssistant) -> None:
    """Test component setup."""
    assert await async_setup_component(
        hass,
        DOMAIN,
        {DOMAIN: MOCK_CONFIG},
    )
    assert (
        type(hass.data[DATA_IMPLEMENTATIONS][DOMAIN][DOMAIN])
        == ZoomOAuth2Implementation
    )


async def test_component_setup_failure(hass: HomeAssistant) -> None:
    """Test component setup failure."""
    hass.config.external_url = None
    assert (
        await async_setup_component(
            hass,
            DOMAIN,
            {DOMAIN: MOCK_CONFIG},
        )
        is False
    )


async def test_entry_setup_and_unload(hass: HomeAssistant) -> None:
    """Test entry setup and unload."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(
        hass,
        DOMAIN,
        {},
    )
    assert MOCK_ENTRY.state == config_entries.ENTRY_STATE_LOADED

    assert await MOCK_ENTRY.async_unload(hass)
    await hass.async_block_till_done()
    assert MOCK_ENTRY.state == config_entries.ENTRY_STATE_NOT_LOADED
