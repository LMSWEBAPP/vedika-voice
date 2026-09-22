import pytest
from app.providers.ai.mock_ai import MockAIProvider
from app.providers.telephony.mock_telephony import MockTelephonyProvider


@pytest.mark.asyncio
async def test_mock_ai_provider_flow():
    provider = MockAIProvider()
    session_id = "test_sess_1"

    config = {
        "opening": "Hello from Mock AI!",
        "questions": [
            {"id": "interest", "text": "Are you interested?", "type": "boolean"},
            {"id": "team_size", "text": "How many members?", "type": "number"},
        ],
        "closing": "Have a great day!",
    }

    await provider.start_session(session_id, config)

    # Send user turn
    await provider.send_text(session_id, "Yes, I am interested! We have 15 members.")

    # Test structured data extraction
    transcript = [
        {"speaker": "ai", "text": "Are you interested?"},
        {"speaker": "user", "text": "Yes, absolutely interested! We have 15 people."},
    ]
    extracted = await provider.extract_structured_data(transcript, config["questions"])
    assert extracted["interest"] is True
    assert extracted["team_size"] == 15

    await provider.end_session(session_id)


@pytest.mark.asyncio
async def test_mock_telephony_provider():
    provider = MockTelephonyProvider()
    resp = await provider.create_call(
        to_phone="+15551234567",
        from_phone="+15557654321",
        callback_url="http://localhost:8000/webhook",
    )
    assert resp.status == "INITIATING"
    assert "mock_call_" in resp.provider_call_id

    status = await provider.get_call_status(resp.provider_call_id)
    assert status in ["INITIATING", "RINGING", "CONNECTED", "COMPLETED"]

    ended = await provider.end_call(resp.provider_call_id)
    assert ended is True
