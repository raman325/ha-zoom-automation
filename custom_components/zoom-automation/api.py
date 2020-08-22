"""API for Zoom Automation bound to Home Assistant OAuth."""
from homeassistant.helpers import config_entry_oauth2_flow


class AsyncConfigEntryAuth:
    """Provide Zoom Automation authentication tied to an OAuth2 based config entry."""

    def __init__(
        self, oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ):
        """Initialize Zoom auth."""
        self._oauth_session = oauth_session

    async def async_get_access_token(self):
        """Return a valid access token."""
        if not self._oauth_session.is_valid:
            await self._oauth_session.async_ensure_token_valid()

        return self._oauth_session.token
