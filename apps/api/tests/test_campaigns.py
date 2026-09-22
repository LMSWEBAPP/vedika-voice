import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_campaign_lifecycle_and_script(client: AsyncClient):
    # Register and login user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "camp_user@veyravoice.com", "password": "Password123!"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "camp_user@veyravoice.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create campaign
    camp_payload = {
        "name": "Q1 Product Discovery",
        "description": "Outbound discovery call for enterprise tech leaders",
        "objective": "Qualify interest and company size",
        "primary_language": "en",
        "script": {
            "persona": "Warm and consultative executive caller",
            "voice_name": "Aoede",
            "opening": "Hi, this is Alex calling regarding AI solutions.",
            "objective": "Qualify team size and interest",
            "questions": [
                {
                    "id": "q1_interested",
                    "text": "Are you interested in automating your outbound calls?",
                    "type": "boolean",
                    "required": True,
                },
                {
                    "id": "q2_team_size",
                    "text": "How many representatives are on your team?",
                    "type": "number",
                    "required": False,
                    "condition": {
                        "depends_on_question_id": "q1_interested",
                        "operator": "equals",
                        "expected_value": True,
                    },
                },
            ],
            "closing": "Thank you for your time today. Goodbye!",
        },
    }

    create_resp = await client.post("/api/v1/campaigns", json=camp_payload, headers=headers)
    assert create_resp.status_code == 200
    camp_data = create_resp.json()
    assert camp_data["name"] == "Q1 Product Discovery"
    assert camp_data["status"] == "DRAFT"
    assert len(camp_data["script"]["questions"]) == 2
    camp_id = camp_data["id"]

    # 2. Transition status: DRAFT -> ACTIVE
    active_resp = await client.post(
        f"/api/v1/campaigns/{camp_id}/status",
        json={"status": "ACTIVE"},
        headers=headers,
    )
    assert active_resp.status_code == 200
    assert active_resp.json()["status"] == "ACTIVE"

    # 3. Invalid transition: ACTIVE -> DRAFT directly should fail
    bad_resp = await client.post(
        f"/api/v1/campaigns/{camp_id}/status",
        json={"status": "DRAFT"},
        headers=headers,
    )
    assert bad_resp.status_code == 400
