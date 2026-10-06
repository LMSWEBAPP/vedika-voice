import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.data_extractor import DataExtractor
from app.agents.safety_guard import SafetyGuard
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.errors import NotFoundError, VeyraException
from app.core.logging import logger
from app.models.call import Call
from app.models.lead import CampaignLead
from app.providers.ai.factory import get_ai_provider
from app.providers.telephony.factory import get_telephony_provider
from app.repositories.call_repo import CallRepository
from app.repositories.campaign_repo import CampaignRepository
from app.repositories.lead_repo import LeadRepository
from app.schemas.call import (
    CallAnswerResponse,
    CallDetailResponse,
    CallEventResponse,
    CallResponse,
    CallTranscriptResponse,
)
from app.schemas.lead import LeadResponse


class CallService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.call_repo = CallRepository(session)
        self.campaign_repo = CampaignRepository(session)
        self.lead_repo = LeadRepository(session)
        self.telephony_provider = get_telephony_provider()
        self.ai_provider = get_ai_provider()

    async def initiate_call(self, campaign_id: str, lead_id: str) -> CallResponse:
        campaign = await self.campaign_repo.get_with_script(campaign_id)
        if not campaign:
            raise NotFoundError("Campaign", campaign_id)

        lead = await self.lead_repo.get(lead_id)
        if not lead:
            raise NotFoundError("Lead", lead_id)

        # 1. Enforce DNC Safety Guard
        SafetyGuard.check_dnc(lead.phone, lead.do_not_call)

        # 2. Find or assign campaign lead
        campaign_lead = await self.lead_repo.assign_to_campaign(campaign_id, lead_id)
        await self.lead_repo.update_campaign_lead_status(
            campaign_id, lead_id, status="CALLING", increment_attempt=True
        )

        # 3. Create initial Call record
        call = Call(
            campaign_id=campaign_id,
            lead_id=lead_id,
            campaign_lead_id=campaign_lead.id,
            provider=settings.TELEPHONY_PROVIDER,
            status="QUEUED",
            language=campaign.primary_language,
        )
        created_call = await self.call_repo.create(call)

        # 4. Initiate via Telephony Provider
        callback_url = f"{settings.TELEPHONY_WEBHOOK_BASE_URL}{settings.API_V1_STR}/webhooks/telephony/call-status"
        caller_phone = (
            settings.TWILIO_PHONE_NUMBER
            if settings.TELEPHONY_PROVIDER == "twilio" and settings.TWILIO_PHONE_NUMBER
            else settings.EXOTEL_CALLER_ID
        )
        try:
            telephony_res = await self.telephony_provider.create_call(
                to_phone=lead.phone,
                from_phone=caller_phone,
                callback_url=callback_url,
                custom_data={"call_id": created_call.id},
            )
            created_call.provider_call_id = telephony_res.provider_call_id
            await self.call_repo.update_status(created_call.id, "INITIATING")

        except Exception as exc:
            logger.error(f"Failed to initiate call via provider: {exc}")
            await self.call_repo.update_status(
                created_call.id, "FAILED", termination_reason=str(exc)
            )
            await self.lead_repo.update_campaign_lead_status(campaign_id, lead_id, status="INVALID")
            raise VeyraException("CALL_INITIATION_FAILED", f"Could not initiate call: {str(exc)}")

        # 5. If running MockTelephony, simulate lifecycle in background
        if settings.TELEPHONY_PROVIDER == "mock":
            asyncio.create_task(
                self._run_mock_call_lifecycle(
                    call_id=created_call.id,
                    campaign_id=campaign_id,
                    lead_id=lead_id,
                    script_data=campaign.script.__dict__ if campaign.script else {},
                )
            )

        return CallResponse.model_validate(created_call)

    async def _run_mock_call_lifecycle(
        self, call_id: str, campaign_id: str, lead_id: str, script_data: dict
    ) -> None:
        """
        Background simulator that transitions a mock call through its lifecycle:
        INITIATING -> RINGING -> CONNECTED -> AI_GREETING -> IN_PROGRESS -> COMPLETED
        and records realistic transcripts and structured answers.
        """
        await asyncio.sleep(1.0)
        async with AsyncSessionLocal() as session:
            repo = CallRepository(session)
            await repo.update_status(call_id, "RINGING")

        await asyncio.sleep(1.5)
        async with AsyncSessionLocal() as session:
            repo = CallRepository(session)
            await repo.update_status(call_id, "CONNECTED")
            await repo.update_status(call_id, "AI_GREETING")

            # AI Greeting turn
            opening = script_data.get("opening", "Hello! Thank you for taking our call.")
            await repo.add_transcript_turn(call_id, speaker="ai", text=opening)

        await asyncio.sleep(1.5)
        async with AsyncSessionLocal() as session:
            repo = CallRepository(session)
            await repo.update_status(call_id, "IN_PROGRESS")

            # Simulated User response
            await repo.add_transcript_turn(
                call_id, speaker="user", text="Hi, yes! I'm happy to learn more."
            )

            # AI asks questions from script
            questions = script_data.get("questions", [])
            for q in questions[:3]:
                await asyncio.sleep(1.0)
                await repo.add_transcript_turn(call_id, speaker="ai", text=q.get("text", ""))

                await asyncio.sleep(1.0)
                q_type = q.get("type", "text")
                if q_type == "boolean":
                    user_reply = "Yes, absolutely interested."
                elif q_type == "number":
                    user_reply = "We have around 40 employees."
                elif q_type == "email":
                    user_reply = "contact@acme.com"
                else:
                    user_reply = "Next Tuesday at 2 PM works best for me."
                await repo.add_transcript_turn(call_id, speaker="user", text=user_reply)

            # AI Closing
            closing = script_data.get("closing", "Thank you for your time. Have a great day!")
            await repo.add_transcript_turn(call_id, speaker="ai", text=closing)

        # Complete Call and Extract Data
        await asyncio.sleep(1.0)
        async with AsyncSessionLocal() as session:
            service = CallService(session)
            await service.complete_call(call_id, termination_reason="NORMAL_HANGUP")

    async def complete_call(self, call_id: str, termination_reason: str = "NORMAL_HANGUP") -> None:
        call = await self.call_repo.get_with_details(call_id)
        if not call or call.status == "COMPLETED":
            return

        await self.call_repo.update_status(
            call_id, "COMPLETED", termination_reason=termination_reason
        )

        campaign = await self.campaign_repo.get_with_script(call.campaign_id)
        questions = campaign.script.questions if campaign and campaign.script else []

        # Structured Data Extraction
        transcript_history = [
            {"speaker": t.speaker, "text": t.text, "language": t.language}
            for t in call.transcripts
        ]

        if questions and transcript_history:
            extracted_raw = await self.ai_provider.extract_structured_data(
                transcript=transcript_history,
                questions=questions,
            )
            extracted_results = DataExtractor.process_extracted_dict(
                raw_extracted=extracted_raw,
                questions=questions,
                transcript_history=transcript_history,
            )

            is_interested = False
            for res in extracted_results:
                await self.call_repo.add_answer(
                    call_id=call.id,
                    question_id=res.question_id,
                    question_text=res.question_text,
                    raw_answer=res.raw_answer,
                    extracted_value=res.extracted_value,
                    is_valid=res.is_valid,
                    confidence=res.confidence,
                )
                if "interest" in res.question_id.lower() and res.extracted_value is True:
                    is_interested = True

            # Update CampaignLead final status
            lead_status = "INTERESTED" if is_interested else "CONTACTED"
            await self.lead_repo.update_campaign_lead_status(
                campaign_id=call.campaign_id,
                lead_id=call.lead_id,
                status=lead_status,
            )

            # Automatically schedule Appointment with reminder if affirmative
            if is_interested:
                from app.services.appointment_service import AppointmentService
                app_service = AppointmentService(self.session)
                lead_domain = None
                if call.lead and call.lead.custom_data:
                    lead_domain = call.lead.custom_data.get("domain")
                await app_service.create_from_extracted_answers(
                    lead_id=call.lead_id,
                    campaign_id=call.campaign_id,
                    call_id=call.id,
                    answers=extracted_raw,
                    lead_domain=lead_domain,
                )

    async def get_call_details(self, call_id: str) -> CallDetailResponse:
        call = await self.call_repo.get_with_details(call_id)
        if not call:
            raise NotFoundError("Call", call_id)

        resp = CallDetailResponse.model_validate(call)
        if call.lead:
            resp.lead = LeadResponse.model_validate(call.lead)
        resp.transcripts = [CallTranscriptResponse.model_validate(t) for t in call.transcripts]
        resp.answers = [CallAnswerResponse.model_validate(a) for a in call.answers]
        resp.events = [CallEventResponse.model_validate(e) for e in call.events]
        return resp

    async def list_calls(
        self,
        campaign_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[CallResponse], int]:
        calls, total = await self.call_repo.list_calls(
            campaign_id=campaign_id, status=status, skip=skip, limit=limit
        )
        results = []
        for c in calls:
            r = CallResponse.model_validate(c)
            if c.lead:
                r.lead = LeadResponse.model_validate(c.lead)
            results.append(r)
        return results, total
