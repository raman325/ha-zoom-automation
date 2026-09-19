"""Test the Zoom config and options flows."""

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
import pytest

from custom_components.zoom.const import CONF_CONNECTIVITY_ON_STATUSES, DOMAIN

from .const import MOCK_ENTRY


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_options_flow(hass: HomeAssistant) -> None:
    """Test the options flow opens and saves.

    OptionsFlow.config_entry is a read-only property supplied by Home
    Assistant; assigning it in __init__ raises AttributeError and takes the
    whole Configure dialog down.
    """
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(MOCK_ENTRY.entry_id)
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_CONNECTIVITY_ON_STATUSES: ["In_Meeting", "Presenting"]},
    )
    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert MOCK_ENTRY.options[CONF_CONNECTIVITY_ON_STATUSES] == [
        "In_Meeting",
        "Presenting",
    ]
    assert MOCK_ENTRY.state is config_entries.ConfigEntryState.LOADED
