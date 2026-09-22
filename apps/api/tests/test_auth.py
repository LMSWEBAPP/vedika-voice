import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    # 1. Register
    reg_payload = {
        "email": "testuser@veyravoice.com",
        "password": "SecurePassword123!",
        "full_name": "Test User",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 200
    user_data = reg_resp.json()
    assert user_data["email"] == "testuser@veyravoice.com"
    assert "id" in user_data

    # 2. Duplicate registration should fail
    dup_resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_resp.status_code == 400
    assert dup_resp.json()["error"]["code"] == "USER_ALREADY_EXISTS"

    # 3. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@veyravoice.com", "password": "SecurePassword123!"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 4. Access protected /me
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "testuser@veyravoice.com"
