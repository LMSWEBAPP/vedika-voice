#!/usr/bin/env python3
"""
Veyra Voice - Quick Twilio Outbound Call Smoke Test
Place a direct test call to your verified phone number to confirm your telephony setup.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add apps/api to python path
current_dir = Path(__file__).resolve().parent
api_dir = current_dir.parent / "apps" / "api"
sys.path.insert(0, str(api_dir))

from app.core.config import settings
from app.providers.telephony.twilio import TwilioProvider


async def main():
    print("=" * 60)
    print("  VEYRA VOICE - TWILIO OUTBOUND CALL TEST")
    print("=" * 60)

    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    twilio_number = settings.TWILIO_PHONE_NUMBER

    print(f"Twilio Account SID : {account_sid[:8]}...{account_sid[-4:] if account_sid else ''}")
    print(f"Twilio Caller ID   : {twilio_number}")

    if not account_sid or not auth_token or not twilio_number:
        print("\n[ERROR] Twilio credentials missing in .env! Please ensure:")
        print("  TWILIO_ACCOUNT_SID=...")
        print("  TWILIO_AUTH_TOKEN=...")
        print("  TWILIO_PHONE_NUMBER=...")
        return

    # Target phone number (Default to verified number from your Twilio Console)
    target_phone = sys.argv[1] if len(sys.argv) > 1 else "+917981104636"
    print(f"Destination Number : {target_phone}")
    print("-" * 60)
    print(f"Placing outbound test call from {twilio_number} to {target_phone}...")

    provider = TwilioProvider()
    try:
        response = await provider.create_call(
            to_phone=target_phone,
            from_phone=twilio_number,
            callback_url=f"{settings.TELEPHONY_WEBHOOK_BASE_URL}/api/v1/webhooks/telephony/call-status",
            custom_data={"call_id": "test_direct_call_001"},
        )
        print("\n" + "=" * 60)
        print("  [SUCCESS] OUTBOUND CALL PLACED!")
        print("=" * 60)
        print(f"Call SID : {response.provider_call_id}")
        print(f"Status   : {response.status}")
        print(f"To       : {response.to_phone}")
        print(f"From     : {response.from_phone}")
        print("\nYour mobile phone should ring within a few seconds! Answer to hear the Veyra Voice greeting.")
    except Exception as exc:
        print(f"\n[FAILED] Call initiation failed: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
