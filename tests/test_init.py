"""Test zoom init."""
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import DATA_IMPLEMENTATIONS
from homeassistant.setup import async_setup_component

from custom_components.zoom.common import ZoomOAuth2Implementation
from custom_components.zoom.const import DOMAIN

from .const import MOCK_CONFIG, MOCK_ENTRY


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_component_setup(hass: HomeAssistant) -> None:
    """Test component setup."""
    # CONFIG_SCHEMA expects a list of configs
    assert await async_setup_component(
        hass,
        DOMAIN,
        {DOMAIN: [MOCK_CONFIG]},
    )
    # Implementation is registered under the config's name ("test"), not DOMAIN
    assert (
        type(hass.data[DATA_IMPLEMENTATIONS][DOMAIN]["test"])
        == ZoomOAuth2Implementation
    )


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_component_setup_failure(hass: HomeAssistant) -> None:
    """Test component setup failure."""
    hass.config.external_url = None
    assert (
        await async_setup_component(
            hass,
            DOMAIN,
            {DOMAIN: [MOCK_CONFIG]},
        )
        is False
    )


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_entry_setup_and_unload(hass: HomeAssistant) -> None:
    """Test entry setup and unload."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(
        hass,
        DOMAIN,
        {},
    )
    assert MOCK_ENTRY.state == config_entries.ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(MOCK_ENTRY.entry_id)
    await hass.async_block_till_done()
    assert MOCK_ENTRY.state == config_entries.ConfigEntryState.NOT_LOADED
