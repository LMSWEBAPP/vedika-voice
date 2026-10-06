import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure project root and apps/api are in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.core.security import hash_password
from app.models.campaign import Campaign
from app.models.lead import CampaignLead, Lead
from app.models.script import CampaignScript
from app.models.user import User
from app.models.call import Call, CallAnswer, CallEvent, CallTranscript
from app.models.appointment import Appointment


async def seed():
    print("Initializing database tables...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Create Default Admin User
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

        # 2. Create Flagship Campaign: Madhu - Pan-India Custom Software Solutions
        camp_madhu_res = await session.execute(
            select(Campaign).filter(Campaign.name == "Madhu - Pan-India Custom Software Solutions")
        )
        camp_madhu = camp_madhu_res.scalars().first()
        if not camp_madhu:
            print("Creating Flagship Campaign: Madhu - Pan-India Custom Software Solutions")
            camp_madhu = Campaign(
                user_id=user.id,
                name="Madhu - Pan-India Custom Software Solutions",
                description="Outbound AI caller Madhu reaching out to business owners across India to understand their domain workflow and secure 15-minute tailored custom software demos.",
                objective="Understand business bottlenecks, highlight custom software solutions, handle objections gracefully, and book a 15-minute tailored demo.",
                status="ACTIVE",
                primary_language="en",
                fallback_language="hi",
            )
            session.add(camp_madhu)
            await session.flush()

            # Script for Madhu
            script_madhu = CampaignScript(
                campaign_id=camp_madhu.id,
                persona="Madhu — a courteous, warm, articulate, and gentle Indian female software consultant representing our freelance software development collective.",
                voice_name="Kore",
                opening="Hello! Good day! This is Madhu calling from our custom software development team. Do you have just a quick minute?",
                objective="Understand business bottlenecks, highlight custom software solutions, handle objections gracefully, and book a 15-minute tailored demo.",
                questions=[
                    {
                        "id": "q1_domain",
                        "text": "What domain or industry does your business primarily operate in?",
                        "type": "text",
                        "required": True,
                        "description": "Domain qualification hook"
                    },
                    {
                        "id": "q2_bottleneck",
                        "text": "What is the biggest manual task or software challenge your team faces today?",
                        "type": "text",
                        "required": True,
                        "description": "Pain point identification"
                    },
                    {
                        "id": "q3_interest",
                        "text": "Would you be open to a 15-minute demo showing how custom software or automation can save you hours every week?",
                        "type": "boolean",
                        "required": True,
                        "description": "Demo interest check"
                    },
                    {
                        "id": "q4_demo_time",
                        "text": "What day and time slot works best for a quick demo call?",
                        "type": "text",
                        "required": False,
                        "description": "Preferred appointment time"
                    },
                    {
                        "id": "q5_channel",
                        "text": "Would you prefer a Google Meet link or a WhatsApp walkthrough?",
                        "type": "single_choice",
                        "options": ["Google Meet", "WhatsApp", "Phone Call"],
                        "required": False,
                        "description": "Meeting platform preference"
                    }
                ],
                closing="Thank you so much for your time! We look forward to connecting and showing you how custom software can make your operations more profitable. Have a wonderful day!",
                fallback_response="I completely understand sir/ma'am. We will note that down. Thank you so much!",
                ai_disclosure="This is an automated conversational voice assistant calling on behalf of our software collective."
            )
            session.add(script_madhu)
            await session.flush()

        # 3. Create Sample Secondary Campaign: Enterprise SaaS Discovery
        camp1_res = await session.execute(select(Campaign).filter(Campaign.name == "Enterprise SaaS Discovery"))
        camp1 = camp1_res.scalars().first()
        if not camp1:
            print("Creating Campaign: Enterprise SaaS Discovery")
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
                    },
                    {
                        "id": "q2_team_size",
                        "text": "How many customer-facing representatives are currently on your team?",
                        "type": "number",
                        "required": False,
                    }
                ],
                closing="Thank you so much for your time today! Our team will send through the details shortly. Have a wonderful day.",
                fallback_response="I understand completely. I will note that for our team.",
                ai_disclosure="This is an automated conversational voice assistant calling on behalf of Veyra Voice."
            )
            session.add(script1)
            await session.flush()

        # 4. Seed Pan-India Leads across Business Domains
        sample_leads_data = [
            ("+919876543210", "Rajesh Khanna", "rajesh@apexrealty.in", "Apex Realty Developers", "Real Estate & Property Management", False),
            ("+919812345678", "Dr. Sunita Kulkarni", "sunita@apollosmiles.com", "Apollo Smiles Dental Clinic", "Healthcare & Dental Clinics", False),
            ("+919701234567", "Amit Singhania", "amit@trendkart.in", "TrendKart Fashion Wear", "E-Commerce & Retail", False),
            ("+919654321098", "Gurpreet Singh", "gurpreet@singhaniaprecision.com", "Singhania Precision Parts", "Manufacturing & Supply Chain", False),
            ("+919988776655", "Priya Venkatesh", "priya@apexwealth.in", "Apex Wealth Advisors", "Financial Advisory & Tax", False),
            ("+919123456780", "Karthik Raman", "karthik@spiceroutekitchens.com", "SpiceRoute Gourmet Kitchens", "Restaurant & Cloud Kitchens", False),
            ("+919888877777", "Rohan Verma", "rohan@dnc-test.com", "Restricted Entity", "Telemarketing Opt-Out", True),  # DNC
            ("+919845012345", "Manish Agarwal", "manish@agarwalchem.in", "Agarwal Chemicals Ltd", "Chemicals & Distribution", False),
        ]

        created_leads = []
        for phone, name, email, company, domain, is_dnc in sample_leads_data:
            res = await session.execute(select(Lead).filter(Lead.phone == phone, Lead.user_id == user.id))
            lead = res.scalars().first()
            if not lead:
                lead = Lead(
                    user_id=user.id,
                    phone=phone,
                    full_name=name,
                    email=email,
                    company=company,
                    domain=domain,
                    do_not_call=is_dnc,
                )
                session.add(lead)
                await session.flush()
            else:
                lead.domain = domain
                session.add(lead)
                await session.flush()
            created_leads.append(lead)

        print(f"Seeded {len(created_leads)} Pan-India domain leads.")

        # 5. Assign Leads to Madhu Campaign
        for idx, lead in enumerate(created_leads):
            res = await session.execute(
                select(CampaignLead).filter(
                    CampaignLead.campaign_id == camp_madhu.id,
                    CampaignLead.lead_id == lead.id
                )
            )
            c_lead = res.scalars().first()
            if not c_lead:
                c_status = "DO_NOT_CALL" if lead.do_not_call else ("INTERESTED" if idx < 3 else "QUEUED")
                c_lead = CampaignLead(
                    campaign_id=camp_madhu.id,
                    lead_id=lead.id,
                    status=c_status,
                    attempts=1 if idx < 3 else 0,
                    last_called_at=datetime.now(timezone.utc) - timedelta(hours=idx + 1) if idx < 3 else None,
                )
                session.add(c_lead)
                await session.flush()

        # 6. Seed Calls & Detailed Transcripts with Madhu (Pan-India Multilingual & Objection Handling)
        now = datetime.now(timezone.utc)
        
        # Call 1: Rajesh Khanna (Real Estate - Booked Demo)
        lead_rajesh = created_leads[0]
        call_rajesh_res = await session.execute(
            select(Call).filter(Call.campaign_id == camp_madhu.id, Call.lead_id == lead_rajesh.id)
        )
        call_rajesh = call_rajesh_res.scalars().first()
        if not call_rajesh:
            call_rajesh = Call(
                campaign_id=camp_madhu.id,
                lead_id=lead_rajesh.id,
                provider="mock",
                provider_call_id=f"mock_madhu_{lead_rajesh.id[:8]}",
                status="COMPLETED",
                started_at=now - timedelta(hours=2),
                answered_at=now - timedelta(hours=2, seconds=-5),
                ended_at=now - timedelta(hours=1, minutes=57),
                duration_seconds=175,
                language="hi",
                termination_reason="NORMAL_HANGUP"
            )
            session.add(call_rajesh)
            await session.flush()

            # Transcripts
            turns_rajesh = [
                ("ai", "Hello! Good day! This is Madhu calling from our custom software development team. Do you have just a quick minute?"),
                ("user", "Haanji Madhu ji boliye, what is this regarding?"),
                ("ai", "Haanji sir! We are a dedicated collective of freelance software developers. We build customized portals, CRMs, and automations for businesses across India. I noticed Apex Realty is expanding rapidly in Bangalore. What is your team's biggest challenge managing property inquiries today?"),
                ("user", "Our main headache is managing broker leads from 99acres and MagicBricks. Agents take too long to follow up, and our current software doesn't sync WhatsApp."),
                ("ai", "Arthamaindi sir, that is such a critical bottleneck! We recently built a tailored WhatsApp CRM bridge for a real estate firm that pings sales agents within 10 seconds of lead arrival, doubling site visit bookings. Would you be open to a quick 15-minute demo to see how it works?"),
                ("user", "How much does something like that cost?"),
                ("ai", "Because we are an agile collective of freelance developers, our pricing is much lower than large agencies with zero lock-in contracts. In a quick 15-minute demo, we understand your exact setup before quoting a single rupee. Could we schedule a slot tomorrow around 3:30 PM?"),
                ("user", "Sounds reasonable. Yes, tomorrow at 3:30 PM works."),
                ("ai", "Bilkul sir! Would you prefer a Google Meet link or a WhatsApp walkthrough?"),
                ("user", "Google Meet link to my email rajesh@apexrealty.in please."),
                ("ai", "Done sir! I have scheduled your demo for tomorrow at 3:30 PM and sent the calendar invite. Thank you so much for your time and have a wonderful day ahead!"),
                ("user", "Thank you Madhu. Bye.")
            ]
            for speaker, text in turns_rajesh:
                session.add(CallTranscript(call_id=call_rajesh.id, speaker=speaker, text=text, language="hi", confidence=0.98))

            answers_rajesh = [
                ("q1_domain", "What domain does your business operate in?", "Real estate broker lead management", "Real Estate", 0.99),
                ("q2_bottleneck", "What is the biggest manual task or software challenge?", "Lead delay from portals and lack of WhatsApp sync", "WhatsApp CRM Sync", 0.96),
                ("q3_interest", "Open to 15-minute demo?", "Yes, tomorrow at 3:30 PM", True, 0.98),
                ("q4_demo_time", "Preferred slot?", "Tomorrow at 3:30 PM", "Tomorrow 3:30 PM", 0.97),
                ("q5_channel", "Channel preference?", "Google Meet link to rajesh@apexrealty.in", "Google Meet", 0.99)
            ]
            for q_id, q_text, raw_ans, ext_val, conf in answers_rajesh:
                session.add(CallAnswer(
                    call_id=call_rajesh.id,
                    question_id=q_id,
                    question_text=q_text,
                    raw_answer=raw_ans,
                    extracted_value=ext_val,
                    is_valid=True,
                    confidence=conf,
                ))

            # Add Events
            session.add(CallEvent(call_id=call_rajesh.id, event_type="CALL_INITIATED", payload={"provider": "mock"}))
            session.add(CallEvent(call_id=call_rajesh.id, event_type="CALL_CONNECTED", payload={"duration": 175}))
            session.add(CallEvent(call_id=call_rajesh.id, event_type="APPOINTMENT_SCHEDULED", payload={"slot": "Tomorrow 3:30 PM", "channel": "Google Meet"}))
            session.add(CallEvent(call_id=call_rajesh.id, event_type="CALL_COMPLETED", payload={"reason": "NORMAL_HANGUP"}))

        # Call 2: Dr. Sunita Kulkarni (Healthcare - Booked Demo)
        lead_sunita = created_leads[1]
        call_sunita_res = await session.execute(
            select(Call).filter(Call.campaign_id == camp_madhu.id, Call.lead_id == lead_sunita.id)
        )
        call_sunita = call_sunita_res.scalars().first()
        if not call_sunita:
            call_sunita = Call(
                campaign_id=camp_madhu.id,
                lead_id=lead_sunita.id,
                provider="mock",
                provider_call_id=f"mock_madhu_{lead_sunita.id[:8]}",
                status="COMPLETED",
                started_at=now - timedelta(hours=4),
                answered_at=now - timedelta(hours=4, seconds=-8),
                ended_at=now - timedelta(hours=3, minutes=58),
                duration_seconds=118,
                language="te",
                termination_reason="NORMAL_HANGUP"
            )
            session.add(call_sunita)
            await session.flush()

            turns_sunita = [
                ("ai", "Hello Dr. Sunita garu, good afternoon! This is Madhu calling from our custom software collective. Do you have just a minute?"),
                ("user", "Namaskaram Madhu garu, I am in between patient consultations. What is this about?"),
                ("ai", "Namaskaram doctor! I will only take 30 seconds. We build custom patient booking portals and automated WhatsApp reminders for dental clinics to reduce no-shows. Would you be open to a quick 10-minute demo on your phone?"),
                ("user", "Actually patient no-shows are a big issue for us. How does the WhatsApp reminder work?"),
                ("ai", "It sends an interactive WhatsApp confirmation 2 hours before the visit, allowing patients to confirm or reschedule with one tap. Can I send a brief walkthrough video to your WhatsApp?"),
                ("user", "Yes please, send it to this number. And we can do a quick call on Thursday at 11:00 AM."),
                ("ai", "Chala thanks doctor! Thursday at 11:00 AM is scheduled via WhatsApp. Have a wonderful day!"),
                ("user", "Thank you Madhu.")
            ]
            for speaker, text in turns_sunita:
                session.add(CallTranscript(call_id=call_sunita.id, speaker=speaker, text=text, language="te", confidence=0.98))

        # 7. Seed Appointments linked to Leads and Calls
        scheduled_1 = datetime.now(timezone.utc) + timedelta(days=1, hours=3)
        scheduled_2 = datetime.now(timezone.utc) + timedelta(days=2, hours=1)
        scheduled_3 = datetime.now(timezone.utc) + timedelta(days=3, hours=5)

        appointments_data = [
            {
                "lead_id": lead_rajesh.id,
                "campaign_id": camp_madhu.id,
                "call_id": call_rajesh.id if call_rajesh else None,
                "scheduled_at": scheduled_1,
                "contact_channel": "Google Meet",
                "requirement_notes": "Interested in custom 99acres/MagicBricks lead capture bridge and WhatsApp CRM router. Budget approved.",
                "status": "CONFIRMED",
                "reminder_sent": False,
            },
            {
                "lead_id": lead_sunita.id,
                "campaign_id": camp_madhu.id,
                "call_id": call_sunita.id if call_sunita else None,
                "scheduled_at": scheduled_2,
                "contact_channel": "WhatsApp",
                "requirement_notes": "Dental clinic patient appointment reminder portal & WhatsApp automated confirmation.",
                "status": "REMINDER_SCHEDULED",
                "reminder_sent": True,
            },
            {
                "lead_id": created_leads[2].id,
                "campaign_id": camp_madhu.id,
                "call_id": None,
                "scheduled_at": scheduled_3,
                "contact_channel": "Google Meet",
                "requirement_notes": "TrendKart Fashion: Needs multi-channel inventory sync (Shopify + Amazon India) and custom warehouse picker UI.",
                "status": "REMINDER_SCHEDULED",
                "reminder_sent": False,
            },
        ]

        for apt in appointments_data:
            existing_apt = await session.execute(
                select(Appointment).filter(
                    Appointment.lead_id == apt["lead_id"],
                    Appointment.campaign_id == apt["campaign_id"]
                )
            )
            if not existing_apt.scalars().first():
                session.add(Appointment(
                    lead_id=apt["lead_id"],
                    campaign_id=apt["campaign_id"],
                    call_id=apt["call_id"],
                    scheduled_at=apt["scheduled_at"],
                    contact_channel=apt["contact_channel"],
                    requirement_notes=apt["requirement_notes"],
                    status=apt["status"],
                    reminder_sent=apt["reminder_sent"],
                ))

        await session.commit()
        print("Database successfully seeded with Madhu campaign, Pan-India domain leads, transcripts, and demo appointments!")


if __name__ == "__main__":
    asyncio.run(seed())
