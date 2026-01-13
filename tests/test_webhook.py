"""Test Zoom webhook handler."""

import hashlib
import hmac
import json
import time
from unittest.mock import patch

import pytest
from aiohttp import ClientSession
from aiohttp.test_utils import TestClient

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from custom_components.zoom.const import (
    ATTR_EVENT,
    ATTR_EVENT_TS,
    ATTR_PAYLOAD,
    CONF_SECRET_TOKEN,
    CONNECTIVITY_EVENT,
    DOMAIN,
    HA_URL,
    VALIDATION_EVENT,
)

from .const import MOCK_CONFIG, MOCK_ENTRY, get_non_validation_event_entities

# Test secret token
SECRET_TOKEN = MOCK_CONFIG[CONF_SECRET_TOKEN]


def _generate_signature(secret_token: str, timestamp: str, body: str) -> str:
    """Generate Zoom webhook signature."""
    message = f"v0:{timestamp}:{body}"
    hash_hex = hmac.new(
        secret_token.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    return f"v0={hash_hex}"


def _create_webhook_payload(
    event: str,
    event_ts: int | None = None,
    payload: dict | None = None,
) -> dict:
    """Create a webhook payload dict."""
    if event_ts is None:
        event_ts = int(time.time())
    if payload is None:
        payload = {}
    return {
        ATTR_EVENT: event,
        ATTR_EVENT_TS: event_ts,
        ATTR_PAYLOAD: payload,
    }


def _create_presence_payload(
    user_id: str = "user123",
    status: str = "In_Meeting",
) -> dict:
    """Create a presence status update payload."""
    return {
        "account_id": "account123",
        "object": {
            "id": user_id,
            "presence_status": status,
        },
    }


def _create_validation_payload(plain_token: str = "test_token_123") -> dict:
    """Create a URL validation payload."""
    return {"plainToken": plain_token}


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_webhook_missing_headers(
    hass: HomeAssistant, hass_client: pytest.fixture
) -> None:
    """Test webhook request without Zoom headers returns 200 but does nothing."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client: TestClient = await hass_client()

    # Request without x-zm-signature and x-zm-request-timestamp
    payload = _create_webhook_payload(CONNECTIVITY_EVENT)
    response = await client.post(
        HA_URL,
        json=payload,
    )

    assert response.status == 200
    # No new entities should be created (only pre-created validation entity exists)
    ent_reg = er.async_get(hass)
    event_entities = get_non_validation_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    assert len(event_entities) == 0


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_webhook_stale_timestamp(
    hass: HomeAssistant, hass_client: pytest.fixture
) -> None:
    """Test webhook request with stale timestamp is rejected."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client: TestClient = await hass_client()

    # Use a timestamp from 10 minutes ago (> 5 min max age)
    stale_timestamp = str(int(time.time()) - 600)
    payload = _create_webhook_payload(CONNECTIVITY_EVENT)
    body = json.dumps(payload)
    signature = _generate_signature(SECRET_TOKEN, stale_timestamp, body)

    response = await client.post(
        HA_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-zm-signature": signature,
            "x-zm-request-timestamp": stale_timestamp,
        },
    )

    assert response.status == 200
    # No new entities should be created due to stale timestamp
    ent_reg = er.async_get(hass)
    event_entities = get_non_validation_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    assert len(event_entities) == 0


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_webhook_invalid_json(
    hass: HomeAssistant, hass_client: pytest.fixture
) -> None:
    """Test webhook request with invalid JSON returns 200 but does nothing."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client: TestClient = await hass_client()

    timestamp = str(int(time.time()))
    body = "not valid json {"
    signature = _generate_signature(SECRET_TOKEN, timestamp, body)

    response = await client.post(
        HA_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-zm-signature": signature,
            "x-zm-request-timestamp": timestamp,
        },
    )

    assert response.status == 200


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_webhook_invalid_schema(
    hass: HomeAssistant, hass_client: pytest.fixture
) -> None:
    """Test webhook request with invalid schema returns 200 but does nothing."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client: TestClient = await hass_client()

    timestamp = str(int(time.time()))
    # Missing required fields
    payload = {"some": "data"}
    body = json.dumps(payload)
    signature = _generate_signature(SECRET_TOKEN, timestamp, body)

    response = await client.post(
        HA_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-zm-signature": signature,
            "x-zm-request-timestamp": timestamp,
        },
    )

    assert response.status == 200


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_webhook_wrong_signature(
    hass: HomeAssistant, hass_client: pytest.fixture
) -> None:
    """Test webhook request with wrong signature is rejected."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client: TestClient = await hass_client()

    timestamp = str(int(time.time()))
    payload = _create_webhook_payload(
        CONNECTIVITY_EVENT,
        payload=_create_presence_payload(),
    )
    body = json.dumps(payload)
    # Use wrong secret token
    signature = _generate_signature("wrong_token", timestamp, body)

    response = await client.post(
        HA_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-zm-signature": signature,
            "x-zm-request-timestamp": timestamp,
        },
    )

    assert response.status == 200
    # No new entities should be created due to signature mismatch
    ent_reg = er.async_get(hass)
    event_entities = get_non_validation_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    assert len(event_entities) == 0


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_webhook_valid_presence_event(
    hass: HomeAssistant, hass_client: pytest.fixture
) -> None:
    """Test valid presence status update webhook creates event entity."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client: TestClient = await hass_client()

    timestamp = str(int(time.time()))
    payload = _create_webhook_payload(
        CONNECTIVITY_EVENT,
        payload=_create_presence_payload(),
    )
    body = json.dumps(payload)
    signature = _generate_signature(SECRET_TOKEN, timestamp, body)

    response = await client.post(
        HA_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-zm-signature": signature,
            "x-zm-request-timestamp": timestamp,
        },
    )

    assert response.status == 200
    await hass.async_block_till_done()

    # Event entity should be created (excluding pre-created validation entity)
    ent_reg = er.async_get(hass)
    event_entities = get_non_validation_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    assert len(event_entities) == 1
    assert CONNECTIVITY_EVENT in event_entities[0].unique_id


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_webhook_url_validation(
    hass: HomeAssistant, hass_client: pytest.fixture
) -> None:
    """Test URL validation webhook returns correct response."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client: TestClient = await hass_client()

    plain_token = "qgg8vlvZRS6UYooatFL8Aw"
    timestamp = str(int(time.time()))
    payload = _create_webhook_payload(
        VALIDATION_EVENT,
        payload=_create_validation_payload(plain_token),
    )
    body = json.dumps(payload)
    signature = _generate_signature(SECRET_TOKEN, timestamp, body)

    response = await client.post(
        HA_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-zm-signature": signature,
            "x-zm-request-timestamp": timestamp,
        },
    )

    assert response.status == 200
    response_data = await response.json()

    # Check response contains plainToken and encryptedToken
    assert response_data["plainToken"] == plain_token
    assert "encryptedToken" in response_data

    # Verify encrypted token is correct HMAC
    expected_hash = hmac.new(
        SECRET_TOKEN.encode(), plain_token.encode(), hashlib.sha256
    ).hexdigest()
    assert response_data["encryptedToken"] == expected_hash


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_webhook_url_validation_missing_plain_token(
    hass: HomeAssistant, hass_client: pytest.fixture
) -> None:
    """Test URL validation with missing plainToken returns 200."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client: TestClient = await hass_client()

    timestamp = str(int(time.time()))
    # Missing plainToken in payload
    payload = _create_webhook_payload(
        VALIDATION_EVENT,
        payload={},
    )
    body = json.dumps(payload)
    signature = _generate_signature(SECRET_TOKEN, timestamp, body)

    response = await client.post(
        HA_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-zm-signature": signature,
            "x-zm-request-timestamp": timestamp,
        },
    )

    # Should return 200 but not the validation response
    assert response.status == 200
    # Response should be empty (not JSON)
    text = await response.text()
    assert text == ""


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_webhook_no_duplicate_entities(
    hass: HomeAssistant, hass_client: pytest.fixture
) -> None:
    """Test that duplicate webhook events don't create duplicate entities."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client: TestClient = await hass_client()

    # Send first event
    timestamp = str(int(time.time()))
    payload = _create_webhook_payload(
        CONNECTIVITY_EVENT,
        payload=_create_presence_payload(status="In_Meeting"),
    )
    body = json.dumps(payload)
    signature = _generate_signature(SECRET_TOKEN, timestamp, body)

    response = await client.post(
        HA_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-zm-signature": signature,
            "x-zm-request-timestamp": timestamp,
        },
    )
    assert response.status == 200
    await hass.async_block_till_done()

    # Send second event of same type
    timestamp2 = str(int(time.time()))
    payload2 = _create_webhook_payload(
        CONNECTIVITY_EVENT,
        payload=_create_presence_payload(status="Available"),
    )
    body2 = json.dumps(payload2)
    signature2 = _generate_signature(SECRET_TOKEN, timestamp2, body2)

    response2 = await client.post(
        HA_URL,
        data=body2,
        headers={
            "Content-Type": "application/json",
            "x-zm-signature": signature2,
            "x-zm-request-timestamp": timestamp2,
        },
    )
    assert response2.status == 200
    await hass.async_block_till_done()

    # Should still only have one presence entity (excluding validation entity)
    ent_reg = er.async_get(hass)
    event_entities = get_non_validation_event_entities(ent_reg, MOCK_ENTRY.entry_id)
    assert len(event_entities) == 1


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_webhook_fires_ha_event(
    hass: HomeAssistant, hass_client: pytest.fixture
) -> None:
    """Test that valid webhook fires HA event."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client: TestClient = await hass_client()

    # Track events fired
    events_fired = []

    def event_listener(event):
        events_fired.append(event)

    hass.bus.async_listen("zoom_webhook", event_listener)

    timestamp = str(int(time.time()))
    payload = _create_webhook_payload(
        CONNECTIVITY_EVENT,
        payload=_create_presence_payload(),
    )
    body = json.dumps(payload)
    signature = _generate_signature(SECRET_TOKEN, timestamp, body)

    response = await client.post(
        HA_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-zm-signature": signature,
            "x-zm-request-timestamp": timestamp,
        },
    )

    assert response.status == 200
    await hass.async_block_till_done()

    # Should have fired one event
    assert len(events_fired) == 1
    assert events_fired[0].data[ATTR_EVENT] == CONNECTIVITY_EVENT
    assert events_fired[0].data["ha_config_entry_id"] == MOCK_ENTRY.entry_id


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_webhook_validation_does_not_fire_event(
    hass: HomeAssistant, hass_client: pytest.fixture
) -> None:
    """Test that validation webhook does not fire HA event."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client: TestClient = await hass_client()

    # Track events fired
    events_fired = []

    def event_listener(event):
        events_fired.append(event)

    hass.bus.async_listen("zoom_webhook", event_listener)

    timestamp = str(int(time.time()))
    payload = _create_webhook_payload(
        VALIDATION_EVENT,
        payload=_create_validation_payload(),
    )
    body = json.dumps(payload)
    signature = _generate_signature(SECRET_TOKEN, timestamp, body)

    response = await client.post(
        HA_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-zm-signature": signature,
            "x-zm-request-timestamp": timestamp,
        },
    )

    assert response.status == 200
    await hass.async_block_till_done()

    # No events should be fired for validation
    assert len(events_fired) == 0
