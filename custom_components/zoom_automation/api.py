"""API for Zoom Automation bound to Home Assistant OAuth."""
from homeassistant.helpers import config_entry_oauth2_flow

from custom_components.zoom_automation.const import BASE_URL, USER_PROFILE


class ZoomAPI:
    """Provide Zoom Automation authentication tied to an OAuth2 based config entry."""

    def __init__(
        self, oauth_session: config_entry_oauth2_flow.OAuth2Session
    ):
        """Initialize Zoom auth."""
        self._oauth_session = oauth_session
        self.id = None
        self.first_name = None
        self.last_name = None
        self.email = None
        self.account_id = None

    async def async_get_access_token(self):
        """Return a valid access token."""
        await self._oauth_session.async_ensure_token_valid()

        return self._oauth_session.token

    async def async_get_user_profile(self):
        """Get user profile for this authentication."""
        resp = await self._oauth_session.async_request(
            "get", f"{BASE_URL}{USER_PROFILE}", raise_for_status=True
        )
        return await resp.json()
