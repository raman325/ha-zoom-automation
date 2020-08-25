"""Common classes and functions for Zoom Automation."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.network import get_url

from .const import DEFAULT_NAME


class ZoomOAuth2Implementation(
    config_entry_oauth2_flow.LocalOAuth2Implementation
):
    """Oauth2 implementation that only uses the external url."""

    def __init__(
        self,
        hass: HomeAssistant,
        domain: str,
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
    ):
        """Initialize local auth implementation."""
        super().__init__(
            hass,
            domain,
            client_id,
            client_secret,
            authorize_url,
            token_url,
        )

    @property
    def name(self) -> str:
        """Name of the implementation."""
        return DEFAULT_NAME

    @property
    def domain(self) -> str:
        """Domain of the implementation."""
        return self._domain

    @property
    def redirect_uri(self) -> str:
        """Return the redirect uri."""
        url = get_url(self.hass, allow_internal=False, prefer_cloud=True)
        return f"{url}{config_entry_oauth2_flow.AUTH_CALLBACK_PATH}"
