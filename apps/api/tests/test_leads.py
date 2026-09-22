import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_leads_csv_import_and_dnc(client: AsyncClient):
    # Setup user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "lead_user@veyravoice.com", "password": "Password123!"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "lead_user@veyravoice.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    csv_data = """phone,full_name,email,company,do_not_call
+15551234567,Alice Smith,alice@example.com,Acme Corp,false
+15559876543,Bob Jones,bob@example.com,Global Tech,true
123,Invalid Number,invalid@example.com,Short Corp,false
+15551234567,Alice Duplicate,alice@example.com,Acme Corp,false
"""

    files = {"file": ("leads.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    resp = await client.post("/api/v1/leads/upload-csv", files=files, headers=headers)
    assert resp.status_code == 200
    res = resp.json()
    assert res["total_processed"] == 4
    assert res["imported"] == 2  # Alice (valid) and Bob (valid lead with DNC=true)
    assert res["invalid_format"] == 1  # 123 is invalid length
    assert res["skipped_duplicates"] == 1  # Alice duplicate phone

    # Verify Bob has do_not_call set to True
    leads_resp = await client.get("/api/v1/leads?search=Bob", headers=headers)
    assert leads_resp.status_code == 200
    bobs = leads_resp.json()
    assert len(bobs) == 1
    assert bobs[0]["do_not_call"] is True
