"""API for Zoom Automation bound to Home Assistant OAuth."""

import logging
from typing import Any, Dict, List, Optional

from aiohttp.web import HTTPUnauthorized
from homeassistant.helpers import config_entry_oauth2_flow

from .const import BASE_URL, CONTACT_LIST_URL, USER_PROFILE_URL

_LOGGER = logging.getLogger(__name__)


class ZoomAPI:
    """Provide Zoom Automation authentication tied to an OAuth2 based config entry."""

    def __init__(self, oauth_session: config_entry_oauth2_flow.OAuth2Session) -> None:
        """Initialize Zoom auth."""
        self._oauth_session = oauth_session

    async def async_get_access_token(self) -> dict:
        """Return a valid access token."""
        await self._oauth_session.async_ensure_token_valid()

        return self._oauth_session.token

    async def async_get_my_user_profile(self) -> Dict[str, Any]:
        """Get user profile for this authentication."""
        resp = await self._oauth_session.async_request(
            "get", f"{BASE_URL}{USER_PROFILE_URL}", raise_for_status=True
        )
        return await resp.json()

    async def async_get_contact_user_profile(self, id: Optional[str]) -> Dict[str, str]:
        """Get presence status for user with given ID."""
        resp = await self._oauth_session.async_request(
            "get",
            f"{BASE_URL}{CONTACT_LIST_URL}/{id}",
            params={"query_presence_status": "true"},
            raise_for_status=True,
        )
        return await resp.json()

    async def async_get_contacts(
        self, contact_types: List[str] = ["external"], limit: int = None
    ) -> List[Dict[str, str]]:
        contacts = []

        for contact_type in contact_types:
            next_page_token = None

            while (next_page_token or next_page_token is None) and (
                not limit or len(contacts) < limit
            ):
                params = {"type": contact_type, "page_size": 50}
                if next_page_token:
                    params["next_page_token"] = next_page_token
                try:
                    resp = await self._oauth_session.async_request(
                        "get",
                        f"{BASE_URL}{CONTACT_LIST_URL}",
                        params=params,
                        raise_for_status=True,
                    )
                except HTTPUnauthorized:
                    return []

                resp_json = await resp.json()
                for item in resp_json["contacts"]:
                    item.update({"contact_type": contact_type})
                contacts.extend(resp_json["contacts"])

                next_page_token = resp_json.get("next_page_token")

        if limit:
            return contacts[:limit]

        return contacts
