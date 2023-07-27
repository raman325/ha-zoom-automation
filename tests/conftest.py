"""Fixtures for zoom tests."""

from pytest import fixture
from pytest_homeassistant_custom_component.async_mock import patch


@fixture(name="external_url", autouse=True)
def external_url_fixture(hass):
    """Set external URL."""
    hass.config.external_url = "https://example.com"


@fixture(name="my_profile", autouse=True)
def my_profile_fixture():
    """Set external URL."""
    with patch(
        "custom_components.zoom.ZoomAPI.async_get_my_user_profile",
        return_value={"id": "test", "profile": {}},
    ):
        yield
