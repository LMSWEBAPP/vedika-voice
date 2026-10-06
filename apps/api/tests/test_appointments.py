from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_appointment_lifecycle_and_reminders(client: AsyncClient):
    # 1. Setup authenticated user
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "madhu_user@veyravoice.com", "password": "Password123!"},
    )
    assert reg_resp.status_code == 200

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "madhu_user@veyravoice.com", "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a Campaign
    camp_resp = await client.post(
        "/api/v1/campaigns",
        json={
            "name": "Madhu Pan-India Software Pitch",
            "objective": "Book 15-minute custom software demos",
            "primary_language": "en",
        },
        headers=headers,
    )
    assert camp_resp.status_code == 200
    campaign = camp_resp.json()
    campaign_id = campaign["id"]

    # 3. Create a Lead with domain
    lead_resp = await client.post(
        "/api/v1/leads",
        json={
            "phone": "+919876543210",
            "full_name": "Vikram Malhotra",
            "company": "Malhotra Textiles",
            "domain": "Manufacturing & Textiles",
            "email": "vikram@malhotratextiles.in",
        },
        headers=headers,
    )
    assert lead_resp.status_code == 200
    lead = lead_resp.json()
    lead_id = lead["id"]
    assert lead["domain"] == "Manufacturing & Textiles"

    # 4. Create an Appointment
    scheduled_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    apt_resp = await client.post(
        "/api/v1/appointments",
        json={
            "lead_id": lead_id,
            "campaign_id": campaign_id,
            "scheduled_at": scheduled_time,
            "contact_channel": "Google Meet",
            "requirement_notes": "Custom ERP bridge for automated yarn inventory and GST billing.",
            "status": "REMINDER_SCHEDULED",
        },
        headers=headers,
    )
    assert apt_resp.status_code == 200
    apt = apt_resp.json()
    apt_id = apt["id"]
    assert apt["contact_channel"] == "Google Meet"
    assert apt["reminder_sent"] is False
    assert apt["status"] == "REMINDER_SCHEDULED"

    # 5. List Appointments
    list_resp = await client.get("/api/v1/appointments", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["lead"]["full_name"] == "Vikram Malhotra"
    assert items[0]["lead"]["domain"] == "Manufacturing & Textiles"

    # 6. Update Status
    update_resp = await client.put(
        f"/api/v1/appointments/{apt_id}",
        json={"status": "CONFIRMED"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "CONFIRMED"

    # 7. Mark Reminder Sent
    reminder_resp = await client.post(
        f"/api/v1/appointments/{apt_id}/reminder-sent",
        headers=headers,
    )
    assert reminder_resp.status_code == 200
    assert reminder_resp.json()["reminder_sent"] is True

    # 8. Filter by Status
    filter_resp = await client.get(
        "/api/v1/appointments?status=CONFIRMED",
        headers=headers,
    )
    assert filter_resp.status_code == 200
    assert len(filter_resp.json()) == 1
