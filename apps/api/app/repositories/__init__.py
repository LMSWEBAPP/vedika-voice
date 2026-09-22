from app.repositories.base import BaseRepository
from app.repositories.user_repo import UserRepository
from app.repositories.campaign_repo import CampaignRepository
from app.repositories.lead_repo import LeadRepository
from app.repositories.call_repo import CallRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "CampaignRepository",
    "LeadRepository",
    "CallRepository",
]
