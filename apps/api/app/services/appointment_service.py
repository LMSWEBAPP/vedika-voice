from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import NotFoundError
from app.models.appointment import Appointment
from app.repositories.appointment_repo import AppointmentRepository
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
)


class AppointmentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.appointment_repo = AppointmentRepository(session)

    async def create_appointment(self, data: AppointmentCreate) -> AppointmentResponse:
        appointment = Appointment(
            lead_id=data.lead_id,
            campaign_id=data.campaign_id,
            call_id=data.call_id,
            scheduled_at=data.scheduled_at,
            status=data.status,
            contact_channel=data.contact_channel,
            requirement_notes=data.requirement_notes,
            reminder_sent=data.reminder_sent,
        )
        created = await self.appointment_repo.create(appointment)
        loaded = await self.appointment_repo.get_with_details(created.id)
        return AppointmentResponse.model_validate(loaded)

    async def list_appointments(
        self,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[AppointmentResponse], int]:
        items, total = await self.appointment_repo.list_by_user(
            user_id=user_id, status=status, skip=skip, limit=limit
        )
        return [AppointmentResponse.model_validate(a) for a in items], total

    async def get_appointment(self, appointment_id: str) -> AppointmentResponse:
        item = await self.appointment_repo.get_with_details(appointment_id)
        if not item:
            raise NotFoundError("Appointment", appointment_id)
        return AppointmentResponse.model_validate(item)

    async def update_appointment(
        self, appointment_id: str, data: AppointmentUpdate
    ) -> AppointmentResponse:
        item = await self.appointment_repo.get(appointment_id)
        if not item:
            raise NotFoundError("Appointment", appointment_id)

        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(item, k, v)

        await self.appointment_repo.update(item)
        loaded = await self.appointment_repo.get_with_details(appointment_id)
        return AppointmentResponse.model_validate(loaded)

    async def create_from_extracted_answers(
        self,
        lead_id: str,
        campaign_id: str,
        call_id: str,
        answers: dict,
        lead_domain: Optional[str] = None,
    ) -> Optional[Appointment]:
        """
        Creates an appointment automatically if the call produced a positive meeting intent.
        """
        # Look for interest affirmation
        has_interest = False
        scheduled_time = None
        requirement = answers.get("requirement") or answers.get("need") or ""

        for q_id, val in answers.items():
            if "interest" in q_id.lower() and (val is True or str(val).lower() in ["yes", "interested"]):
                has_interest = True
            if "time" in q_id.lower() or "slot" in q_id.lower() or "date" in q_id.lower():
                scheduled_time = val

        if not has_interest and not scheduled_time:
            return None

        # Default schedule: Tomorrow 3:00 PM if free-text time provided or relative
        now = datetime.now(timezone.utc)
        scheduled_at = now + timedelta(days=1, hours=4)

        notes = f"Domain: {lead_domain or 'Custom Software'}."
        if requirement:
            notes += f" Requirement: {requirement}."
        if scheduled_time:
            notes += f" Client requested slot: {scheduled_time}."

        channel = "WhatsApp"
        if "meet" in str(scheduled_time).lower():
            channel = "Google Meet"
        elif "call" in str(scheduled_time).lower() or "phone" in str(scheduled_time).lower():
            channel = "Phone"

        appointment = Appointment(
            lead_id=lead_id,
            campaign_id=campaign_id,
            call_id=call_id,
            scheduled_at=scheduled_at,
            status="REMINDER_SCHEDULED",
            contact_channel=channel,
            requirement_notes=notes,
            reminder_sent=False,
        )
        created = await self.appointment_repo.create(appointment)
        return created
