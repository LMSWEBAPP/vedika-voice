from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["Appointments & Reminders"])


@router.get("", response_model=List[AppointmentResponse])
async def list_appointments(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db)
    items, _ = await service.list_appointments(
        user_id=current_user.id, status=status, skip=skip, limit=limit
    )
    return items


@router.post("", response_model=AppointmentResponse)
async def create_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db)
    return await service.create_appointment(data)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db)
    return await service.get_appointment(appointment_id)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    data: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db)
    return await service.update_appointment(appointment_id, data)


@router.post("/{appointment_id}/reminder-sent", response_model=AppointmentResponse)
async def mark_reminder_sent(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db)
    return await service.update_appointment(
        appointment_id, AppointmentUpdate(reminder_sent=True, status="CONFIRMED")
    )
