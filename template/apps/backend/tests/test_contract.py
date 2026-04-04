{% raw %}
"""
Contract tests: validate backend responses against openapi.yaml.

This ensures the OpenAPI spec (source of truth) and the actual API
stay in sync. Catches drift that type generation alone misses.
"""
import pytest
from httpx import AsyncClient

import yaml
from pathlib import Path

SPEC_PATH = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "openapi.yaml"


@pytest.fixture(scope="module")
def openapi_spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text())


def get_schema_fields(spec: dict, schema_name: str) -> set[str]:
    """Extract field names from an OpenAPI schema component."""
    schema = spec["components"]["schemas"][schema_name]
    return set(schema.get("properties", {}).keys())


@pytest.mark.asyncio
async def test_item_response_matches_spec(client: AsyncClient, openapi_spec: dict):
    """Verify that a created item contains all fields from the Item schema."""
    cookies = await _auth(client)
    response = await client.post(
        "/api/items/", json={"title": "Contract test"}, cookies=cookies
    )
    assert response.status_code == 201

    expected_fields = get_schema_fields(openapi_spec, "Item")
    actual_fields = set(response.json().keys())

    missing = expected_fields - actual_fields
    assert not missing, f"Fields in OpenAPI spec but missing from response: {missing}"


@pytest.mark.asyncio
async def test_user_response_matches_spec(client: AsyncClient, openapi_spec: dict):
    """Verify that /auth/me returns all fields from the User schema."""
    cookies = await _auth(client)
    response = await client.get("/api/auth/me", cookies=cookies)
    assert response.status_code == 200

    expected_fields = get_schema_fields(openapi_spec, "UserResponse")
    actual_fields = set(response.json().keys())

    missing = expected_fields - actual_fields
    assert not missing, f"Fields in OpenAPI spec but missing from response: {missing}"


async def _auth(client: AsyncClient) -> dict:
    await client.post(
        "/api/auth/register",
        json={"email": "contract@test.com", "password": "testpass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "contract@test.com", "password": "testpass123"},
    )
    return dict(resp.cookies)
{% endraw %}
