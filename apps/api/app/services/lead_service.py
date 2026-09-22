import csv
import io
import re
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import NotFoundError, VeyraException
from app.models.lead import CampaignLead, Lead
from app.repositories.lead_repo import LeadRepository
from app.schemas.lead import (
    CampaignLeadResponse,
    LeadCreate,
    LeadImportResult,
    LeadResponse,
    LeadUpdate,
)


def normalize_phone(phone: str) -> str:
    """Normalize phone number to standard format (+countrycode or digits)."""
    cleaned = re.sub(r"[^\d+]", "", phone.strip())
    return cleaned


class LeadService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.lead_repo = LeadRepository(session)

    async def create_lead(self, user_id: str, data: LeadCreate) -> LeadResponse:
        phone = normalize_phone(data.phone)
        if len(phone) < 7:
            raise VeyraException("INVALID_PHONE", "Phone number must contain at least 7 digits.")

        existing = await self.lead_repo.get_by_phone(phone, user_id)
        if existing:
            raise VeyraException(
                "DUPLICATE_LEAD",
                f"A lead with phone number {phone} already exists in your account.",
            )

        lead = Lead(
            user_id=user_id,
            phone=phone,
            full_name=data.full_name,
            email=data.email,
            company=data.company,
            custom_data=data.custom_data,
            do_not_call=data.do_not_call,
        )
        created = await self.lead_repo.create(lead)
        return LeadResponse.model_validate(created)

    async def list_leads(
        self,
        user_id: str,
        search: Optional[str] = None,
        do_not_call: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[LeadResponse], int]:
        leads, total = await self.lead_repo.list_by_user(
            user_id=user_id,
            search=search,
            do_not_call=do_not_call,
            skip=skip,
            limit=limit,
        )
        return [LeadResponse.model_validate(l) for l in leads], total

    async def get_lead(self, lead_id: str) -> LeadResponse:
        lead = await self.lead_repo.get(lead_id)
        if not lead:
            raise NotFoundError("Lead", lead_id)
        return LeadResponse.model_validate(lead)

    async def update_lead(self, lead_id: str, data: LeadUpdate) -> LeadResponse:
        lead = await self.lead_repo.get(lead_id)
        if not lead:
            raise NotFoundError("Lead", lead_id)

        update_dict = data.model_dump(exclude_unset=True)
        if "phone" in update_dict and update_dict["phone"]:
            update_dict["phone"] = normalize_phone(update_dict["phone"])

        for k, v in update_dict.items():
            setattr(lead, k, v)

        await self.lead_repo.update(lead)
        return LeadResponse.model_validate(lead)

    async def set_do_not_call(self, lead_id: str, dnc: bool) -> LeadResponse:
        lead = await self.lead_repo.get(lead_id)
        if not lead:
            raise NotFoundError("Lead", lead_id)

        lead.do_not_call = dnc
        await self.lead_repo.update(lead)
        return LeadResponse.model_validate(lead)

    async def assign_to_campaign(self, campaign_id: str, lead_ids: List[str]) -> int:
        count = 0
        for lid in lead_ids:
            lead = await self.lead_repo.get(lid)
            if lead and not lead.do_not_call:
                await self.lead_repo.assign_to_campaign(campaign_id, lid)
                count += 1
        return count

    async def get_campaign_leads(
        self,
        campaign_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[CampaignLeadResponse], int]:
        c_leads, total = await self.lead_repo.get_campaign_leads(
            campaign_id=campaign_id, status=status, skip=skip, limit=limit
        )
        return [
            CampaignLeadResponse(
                id=cl.id,
                campaign_id=cl.campaign_id,
                lead_id=cl.lead_id,
                status=cl.status,
                attempts=cl.attempts,
                last_called_at=cl.last_called_at,
                next_retry_at=cl.next_retry_at,
                lead=LeadResponse.model_validate(cl.lead),
            )
            for cl in c_leads
        ], total

    async def import_csv(
        self,
        user_id: str,
        csv_content: str,
        campaign_id: Optional[str] = None,
    ) -> LeadImportResult:
        result = LeadImportResult(
            total_processed=0,
            imported=0,
            skipped_duplicates=0,
            rejected_dnc=0,
            invalid_format=0,
            errors=[],
        )

        try:
            reader = csv.DictReader(io.StringIO(csv_content.strip()))
        except Exception as exc:
            result.errors.append(f"Invalid CSV structure: {str(exc)}")
            return result

        for row_num, row in enumerate(reader, start=1):
            result.total_processed += 1
            # Flexible column lookup
            phone_raw = (
                row.get("phone")
                or row.get("Phone")
                or row.get("mobile")
                or row.get("Mobile")
                or row.get("phone_number")
                or ""
            )
            phone = normalize_phone(phone_raw)

            if len(phone) < 7:
                result.invalid_format += 1
                result.errors.append(f"Row {row_num}: Invalid phone number '{phone_raw}'.")
                continue

            full_name = row.get("full_name") or row.get("name") or row.get("Name") or None
            email = row.get("email") or row.get("Email") or None
            company = row.get("company") or row.get("Company") or None

            # Check duplicate
            existing = await self.lead_repo.get_by_phone(phone, user_id)
            if existing:
                if existing.do_not_call:
                    result.rejected_dnc += 1
                else:
                    result.skipped_duplicates += 1
                    # If campaign provided, still ensure assigned
                    if campaign_id:
                        await self.lead_repo.assign_to_campaign(campaign_id, existing.id)
                continue

            # Check if CSV specified DNC flag
            dnc_flag = str(row.get("do_not_call", "")).lower() in ["true", "1", "yes"]

            lead = Lead(
                user_id=user_id,
                phone=phone,
                full_name=full_name,
                email=email,
                company=company,
                do_not_call=dnc_flag,
            )
            created = await self.lead_repo.create(lead)
            result.imported += 1

            if campaign_id and not dnc_flag:
                await self.lead_repo.assign_to_campaign(campaign_id, created.id)

        return result
