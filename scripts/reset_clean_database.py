import asyncio
import os
import sys

# Ensure apps/api is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from sqlalchemy import delete
from app.core.database import AsyncSessionLocal, init_db
from app.core.security import hash_password
from app.models.appointment import Appointment
from app.models.call import Call, CallAnswer, CallEvent, CallTranscript
from app.models.campaign import Campaign
from app.models.lead import CampaignLead, Lead
from app.models.script import CampaignScript
from app.models.user import User


async def clear_all_dummy_data():
    print("Connecting to database to clear all dummy data...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Delete in order of foreign key dependencies
        print("Clearing appointments...")
        await session.execute(delete(Appointment))

        print("Clearing call answers, transcripts, events, and calls...")
        await session.execute(delete(CallAnswer))
        await session.execute(delete(CallTranscript))
        await session.execute(delete(CallEvent))
        await session.execute(delete(Call))

        print("Clearing campaign scripts and campaign leads...")
        await session.execute(delete(CampaignScript))
        await session.execute(delete(CampaignLead))

        print("Clearing leads...")
        await session.execute(delete(Lead))

        print("Clearing campaigns...")
        await session.execute(delete(Campaign))

        print("Clearing dummy users...")
        await session.execute(delete(User))

        # Create one clean default local workspace user for seamless local development without login prompts
        print("Creating clean local workspace user...")
        clean_user = User(
            email="workspace@local.veyra",
            hashed_password=hash_password("clean_workspace_local"),
            full_name="Workspace Owner",
            role="admin",
            is_active=True,
        )
        session.add(clean_user)

        await session.commit()
        print("\nSUCCESS: All dummy users, dummy leads, calls, transcripts, and appointments have been permanently wiped.")
        print("The database is completely fresh, clean, and ready for your real data!")


if __name__ == "__main__":
    asyncio.run(clear_all_dummy_data())
