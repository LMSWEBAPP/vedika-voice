import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure project root and apps/api are in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.core.database import AsyncSessionLocal, init_db
from app.core.security import hash_password
from app.models.campaign import Campaign
from app.models.lead import CampaignLead, Lead
from app.models.script import CampaignScript
from app.models.user import User
from app.models.call import Call, CallAnswer, CallEvent, CallTranscript


async def seed():
    print("Initializing database tables...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Create Default Admin User
        from sqlalchemy import select
        res = await session.execute(select(User).filter(User.email == "admin@veyravoice.com"))
        user = res.scalars().first()

        if not user:
            print("Creating default admin account: admin@veyravoice.com / admin123456")
            user = User(
                email="admin@veyravoice.com",
                hashed_password=hash_password("admin123456"),
                full_name="Alex Mercer",
                role="admin",
                is_active=True,
            )
            session.add(user)
            await session.flush()
        else:
            print("Admin account already exists.")

        # 2. Create Sample Campaign 1: SaaS Outbound Discovery
        camp1_res = await session.execute(select(Campaign).filter(Campaign.name == "Enterprise SaaS Discovery"))
        camp1 = camp1_res.scalars().first()
        if not camp1:
            print("Creating Campaign 1: Enterprise SaaS Discovery")
            camp1 = Campaign(
                user_id=user.id,
                name="Enterprise SaaS Discovery",
                description="Outbound conversational AI agent qualifying B2B software team leaders.",
                objective="Qualify interest, team size, current CRM, and schedule demo walkthrough.",
                status="ACTIVE",
                primary_language="en",
                fallback_language="en",
            )
            session.add(camp1)
            await session.flush()

            # Script for Campaign 1
            script1 = CampaignScript(
                campaign_id=camp1.id,
                persona="Courteous, sharp, consultative executive representative. Clear and natural pacing.",
                voice_name="Aoede",
                opening="Hello, this is Jordan from Veyra Voice. Am I speaking with the person leading sales operations?",
                objective="Determine if company is interested in automating outbound sales calls.",
                questions=[
                    {
                        "id": "q1_interest",
                        "text": "Are you currently exploring automated voice AI agents for customer outreach?",
                        "type": "boolean",
                        "required": True,
                        "description": "Primary qualification check"
                    },
                    {
                        "id": "q2_team_size",
                        "text": "How many customer-facing representatives are currently on your team?",
                        "type": "number",
                        "required": False,
                        "condition": {
                            "depends_on_question_id": "q1_interest",
                            "operator": "equals",
                            "expected_value": True
                        }
                    },
                    {
                        "id": "q3_crm",
                        "text": "What CRM or lead management software do you currently use?",
                        "type": "single_choice",
                        "options": ["HubSpot", "Salesforce", "Zoho", "Custom / Other"],
                        "required": False
                    },
                    {
                        "id": "q4_email",
                        "text": "Could you please confirm the best email address for our senior consultant to send over an overview?",
                        "type": "email",
                        "required": False
                    }
                ],
                closing="Thank you so much for your time today! Our team will send through the details shortly. Have a wonderful day.",
                fallback_response="I understand completely. I will note that for our team.",
                ai_disclosure="This is an automated conversational voice assistant calling on behalf of Veyra Voice."
            )
            session.add(script1)
            await session.flush()

        # 3. Create Sample Campaign 2: Fintech Merchant Verification
        camp2_res = await session.execute(select(Campaign).filter(Campaign.name == "Merchant Verification & Care"))
        camp2 = camp2_res.scalars().first()
        if not camp2:
            print("Creating Campaign 2: Merchant Verification & Care")
            camp2 = Campaign(
                user_id=user.id,
                name="Merchant Verification & Care",
                description="Follow-up with retail merchants on activation and satisfaction.",
                objective="Verify account readiness and assess onboarding rating.",
                status="ACTIVE",
                primary_language="en",
                fallback_language="hi",
            )
            session.add(camp2)
            await session.flush()

            script2 = CampaignScript(
                campaign_id=camp2.id,
                persona="Empathetic, reassuring, and meticulous banking specialist.",
                voice_name="Puck",
                opening="Good afternoon! This is Priya from PaySwift Merchant Services. I'm following up on your digital account activation.",
                objective="Confirm document verification and measure customer onboarding experience.",
                questions=[
                    {
                        "id": "q1_verified",
                        "text": "Have you been able to log in to your merchant portal and submit your verification documents?",
                        "type": "boolean",
                        "required": True
                    },
                    {
                        "id": "q2_satisfaction",
                        "text": "On a scale of 1 to 10, how seamless was your experience getting started?",
                        "type": "rating",
                        "required": False
                    },
                    {
                        "id": "q3_pos_help",
                        "text": "Would you like our technical engineer to visit your store for a free POS demonstration?",
                        "type": "boolean",
                        "required": False
                    }
                ],
                closing="Thank you for your partnership with PaySwift. We are always here to help you grow!",
                fallback_response="Understood. Let me create a quick ticket for our support crew.",
                ai_disclosure="This is PaySwift's automated customer success voice agent."
            )
            session.add(script2)
            await session.flush()

        # 4. Seed Leads
        sample_leads_data = [
            ("+919876543210", "Rahul Sharma", "rahul@techflow.io", "TechFlow Solutions", False),
            ("+919812345678", "Pooja Reddy", "pooja@cloudapex.in", "CloudApex Systems", False),
            ("+919701234567", "Vikram Patel", "vikram@finscale.co", "FinScale India", False),
            ("+919654321098", "Ananya Iyer", "ananya@growthwave.com", "GrowthWave Media", False),
            ("+14155552671", "David Miller", "david@orbitscale.com", "OrbitScale USA", False),
            ("+14155559823", "Sarah Jenkins", "sarah@apexventures.io", "Apex Ventures", False),
            ("+919988776655", "Suresh Kumar", "suresh@kumarretail.in", "Kumar Retailers", False),
            ("+919123456780", "Sneha Rao", "sneha@bengalurulabs.org", "Bengaluru TechLabs", False),
            ("+919888877777", "Rohan Verma", "rohan@dnc-test.com", "Restricted Entity", True),  # DNC
            ("+15558889999", "Elena Rostova", "elena@nordicscale.eu", "Nordic Scale", False),
        ]

        created_leads = []
        for phone, name, email, company, is_dnc in sample_leads_data:
            res = await session.execute(select(Lead).filter(Lead.phone == phone, Lead.user_id == user.id))
            lead = res.scalars().first()
            if not lead:
                lead = Lead(
                    user_id=user.id,
                    phone=phone,
                    full_name=name,
                    email=email,
                    company=company,
                    do_not_call=is_dnc,
                )
                session.add(lead)
                await session.flush()
            created_leads.append(lead)

        print(f"Seeded {len(created_leads)} sample leads.")

        # 5. Assign Leads to Campaigns
        for idx, lead in enumerate(created_leads):
            target_campaign = camp1 if idx % 2 == 0 else camp2
            res = await session.execute(
                select(CampaignLead).filter(
                    CampaignLead.campaign_id == target_campaign.id,
                    CampaignLead.lead_id == lead.id
                )
            )
            c_lead = res.scalars().first()
            if not c_lead:
                c_status = "DO_NOT_CALL" if lead.do_not_call else ("INTERESTED" if idx < 3 else "QUEUED")
                c_lead = CampaignLead(
                    campaign_id=target_campaign.id,
                    lead_id=lead.id,
                    status=c_status,
                    attempts=1 if idx < 4 else 0,
                    last_called_at=datetime.now(timezone.utc) - timedelta(hours=idx) if idx < 4 else None,
                )
                session.add(c_lead)
                await session.flush()

        # 6. Seed Realistic Call Histories & Transcripts for the first few leads
        sample_calls = [
            {
                "lead": created_leads[0],
                "campaign": camp1,
                "status": "COMPLETED",
                "duration": 142,
                "answers": [
                    ("q1_interest", "Are you exploring voice AI?", "Yes, absolutely interested", True, 0.98),
                    ("q2_team_size", "How many representatives?", "Around 35 representatives", 35, 0.95),
                    ("q3_crm", "What CRM do you use?", "We are on Salesforce", "Salesforce", 0.92),
                    ("q4_email", "Best email address?", "rahul@techflow.io", "rahul@techflow.io", 0.99),
                ],
                "turns": [
                    ("ai", "Hello, this is Jordan from Veyra Voice. Am I speaking with the person leading sales operations?"),
                    ("user", "Yes, Rahul here. I head sales operations at TechFlow."),
                    ("ai", "Pleasure to connect Rahul. Are you currently exploring automated voice AI agents for customer outreach?"),
                    ("user", "Yes, we are actively looking to automate our Tier 1 discovery calls."),
                    ("ai", "That aligns directly with our platform. How many customer-facing representatives are currently on your team?"),
                    ("user", "We currently have around 35 representatives across inbound and outbound."),
                    ("ai", "Great. And what CRM or lead management software do you currently use?"),
                    ("user", "We use Salesforce Enterprise."),
                    ("ai", "Could you please confirm the best email address for our senior consultant to send over an overview?"),
                    ("user", "Sure, you can send it to rahul@techflow.io."),
                    ("ai", "Thank you so much for your time today Rahul! Our team will send through the details shortly. Have a wonderful day."),
                    ("user", "Thanks Jordan, looking forward to it. Bye.")
                ]
            },
            {
                "lead": created_leads[1],
                "campaign": camp1,
                "status": "COMPLETED",
                "duration": 98,
                "answers": [
                    ("q1_interest", "Are you exploring voice AI?", "Yes, definitely interested", True, 0.96),
                    ("q2_team_size", "How many representatives?", "12 agents", 12, 0.95),
                    ("q3_crm", "What CRM do you use?", "HubSpot", "HubSpot", 0.94),
                ],
                "turns": [
                    ("ai", "Hello, this is Jordan from Veyra Voice. Am I speaking with the person leading sales operations?"),
                    ("user", "Hi Jordan, yes, Pooja speaking."),
                    ("ai", "Hi Pooja! Are you currently exploring automated voice AI agents for customer outreach?"),
                    ("user", "Yes, definitely interested. We want to qualify leads faster."),
                    ("ai", "Wonderful. How many customer-facing representatives are currently on your team?"),
                    ("user", "We have 12 agents right now."),
                    ("ai", "Got it. And what CRM do you use?"),
                    ("user", "We are on HubSpot."),
                    ("ai", "Thank you Pooja! We'll prepare a tailored showcase for your team. Have a great day!"),
                    ("user", "Thank you, goodbye.")
                ]
            }
        ]

        for c_data in sample_calls:
            c_lead = c_data["lead"]
            camp = c_data["campaign"]

            now = datetime.now(timezone.utc)
            call = Call(
                campaign_id=camp.id,
                lead_id=c_lead.id,
                provider="mock",
                provider_call_id=f"mock_call_seeded_{c_lead.id[:8]}",
                status=c_data["status"],
                started_at=now - timedelta(minutes=10),
                answered_at=now - timedelta(minutes=9, seconds=50),
                ended_at=now - timedelta(minutes=10 - (c_data["duration"] // 60)),
                duration_seconds=c_data["duration"],
                language="en",
                termination_reason="NORMAL_HANGUP"
            )
            session.add(call)
            await session.flush()

            # Add Transcripts
            for speaker, text in c_data["turns"]:
                t = CallTranscript(
                    call_id=call.id,
                    speaker=speaker,
                    text=text,
                    language="en",
                    confidence=0.98,
                )
                session.add(t)

            # Add Structured Answers
            for q_id, q_text, raw_ans, ext_val, conf in c_data["answers"]:
                ans = CallAnswer(
                    call_id=call.id,
                    question_id=q_id,
                    question_text=q_text,
                    raw_answer=raw_ans,
                    extracted_value=ext_val,
                    is_valid=True,
                    confidence=conf,
                )
                session.add(ans)

            # Add Call Events
            session.add(CallEvent(call_id=call.id, event_type="CALL_INITIATED", payload={"provider": "mock"}))
            session.add(CallEvent(call_id=call.id, event_type="CALL_CONNECTED", payload={"duration": c_data["duration"]}))
            session.add(CallEvent(call_id=call.id, event_type="CALL_COMPLETED", payload={"reason": "NORMAL_HANGUP"}))

        await session.commit()
        print("Database successfully seeded with campaigns, structured scripts, leads, and call logs!")


if __name__ == "__main__":
    asyncio.run(seed())
