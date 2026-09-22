from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.call import Call, CallAnswer, CallEvent, CallTranscript
from app.repositories.base import BaseRepository


class CallRepository(BaseRepository[Call]):
    def __init__(self, session: AsyncSession):
        super().__init__(Call, session)

    async def get_with_details(self, call_id: str) -> Optional[Call]:
        result = await self.session.execute(
            select(Call)
            .options(
                selectinload(Call.transcripts),
                selectinload(Call.answers),
                selectinload(Call.events),
                selectinload(Call.lead),
            )
            .filter(Call.id == call_id)
        )
        return result.scalars().first()

    async def get_by_provider_call_id(self, provider_call_id: str) -> Optional[Call]:
        result = await self.session.execute(
            select(Call)
            .options(
                selectinload(Call.transcripts),
                selectinload(Call.answers),
                selectinload(Call.lead),
            )
            .filter(Call.provider_call_id == provider_call_id)
        )
        return result.scalars().first()

    async def list_calls(
        self,
        campaign_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Call], int]:
        query = select(Call).options(selectinload(Call.lead))
        if campaign_id:
            query = query.filter(Call.campaign_id == campaign_id)
        if status:
            query = query.filter(Call.status == status)

        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_q)).scalar() or 0

        items_res = await self.session.execute(
            query.order_by(Call.created_at.desc()).offset(skip).limit(limit)
        )
        return list(items_res.scalars().all()), total

    async def add_event(self, call_id: str, event_type: str, payload: Optional[dict] = None) -> CallEvent:
        event = CallEvent(call_id=call_id, event_type=event_type, payload=payload or {})
        self.session.add(event)
        await self.session.flush()
        return event

    async def add_transcript_turn(
        self,
        call_id: str,
        speaker: str,
        text: str,
        language: str = "en",
        confidence: float = 1.0,
        metadata_json: Optional[dict] = None,
    ) -> CallTranscript:
        transcript = CallTranscript(
            call_id=call_id,
            speaker=speaker,
            text=text,
            language=language,
            confidence=confidence,
            metadata_json=metadata_json,
        )
        self.session.add(transcript)
        await self.session.flush()
        return transcript

    async def add_answer(
        self,
        call_id: str,
        question_id: str,
        question_text: str,
        raw_answer: str,
        extracted_value: Optional[Any] = None,
        is_valid: bool = True,
        confidence: float = 1.0,
    ) -> CallAnswer:
        answer = CallAnswer(
            call_id=call_id,
            question_id=question_id,
            question_text=question_text,
            raw_answer=raw_answer,
            extracted_value=extracted_value,
            is_valid=is_valid,
            confidence=confidence,
        )
        self.session.add(answer)
        await self.session.flush()
        return answer

    async def update_status(
        self,
        call_id: str,
        new_status: str,
        termination_reason: Optional[str] = None,
        recording_url: Optional[str] = None,
    ) -> Optional[Call]:
        call = await self.get(call_id)
        if not call:
            return None

        old_status = call.status
        call.status = new_status
        now = datetime.now(timezone.utc)

        if new_status == "CONNECTED" and not call.answered_at:
            call.answered_at = now
            if not call.started_at:
                call.started_at = now
        elif new_status in ["COMPLETED", "FAILED", "NO_ANSWER", "BUSY", "CANCELLED"]:
            if not call.ended_at:
                call.ended_at = now
            if call.started_at:
                call.duration_seconds = int((call.ended_at - call.started_at).total_seconds())

        if termination_reason:
            call.termination_reason = termination_reason
        if recording_url:
            call.recording_url = recording_url

        # Log event for state transition
        await self.add_event(
            call_id=call_id,
            event_type="CALL_STATE_TRANSITION",
            payload={"from_status": old_status, "to_status": new_status},
        )
        await self.session.flush()
        return call
