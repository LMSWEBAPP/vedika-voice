from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.call import Call, CallAnswer
from app.models.campaign import Campaign
from app.models.lead import CampaignLead, Lead
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    CallsOverTimePoint,
    DashboardStatsResponse,
    LanguageStat,
    OutcomeDistribution,
    QuestionDropoffStat,
)


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_overview(self, user_id: str) -> AnalyticsOverviewResponse:
        # Total leads
        total_leads_res = await self.session.execute(
            select(func.count()).select_from(Lead).filter(Lead.user_id == user_id)
        )
        total_leads = total_leads_res.scalar() or 0

        # Query all calls for user's campaigns
        calls_query = (
            select(Call)
            .join(Campaign, Call.campaign_id == Campaign.id)
            .filter(Campaign.user_id == user_id)
        )
        calls_res = await self.session.execute(calls_query)
        all_calls = list(calls_res.scalars().all())

        calls_made = len(all_calls)
        answered_calls = sum(1 for c in all_calls if c.answered_at is not None)
        completed_calls = sum(1 for c in all_calls if c.status == "COMPLETED")
        no_answer_calls = sum(1 for c in all_calls if c.status == "NO_ANSWER")

        # Duration sum
        durations = [c.duration_seconds for c in all_calls if c.duration_seconds > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        # Interested vs Not Interested leads
        interested_res = await self.session.execute(
            select(func.count())
            .select_from(CampaignLead)
            .join(Campaign, CampaignLead.campaign_id == Campaign.id)
            .filter(Campaign.user_id == user_id, CampaignLead.status == "INTERESTED")
        )
        interested_count = interested_res.scalar() or 0

        not_interested_res = await self.session.execute(
            select(func.count())
            .select_from(CampaignLead)
            .join(Campaign, CampaignLead.campaign_id == Campaign.id)
            .filter(Campaign.user_id == user_id, CampaignLead.status == "NOT_INTERESTED")
        )
        not_interested_count = not_interested_res.scalar() or 0

        completion_rate = (completed_calls / calls_made * 100.0) if calls_made > 0 else 0.0
        conversion_rate = (interested_count / completed_calls * 100.0) if completed_calls > 0 else 0.0

        summary = DashboardStatsResponse(
            total_leads=total_leads,
            calls_made=calls_made,
            answered_calls=answered_calls,
            completed_calls=completed_calls,
            interested_leads=interested_count,
            not_interested_leads=not_interested_count,
            no_answer_calls=no_answer_calls,
            average_duration_seconds=round(avg_duration, 1),
            completion_rate=round(completion_rate, 1),
            conversion_rate=round(conversion_rate, 1),
        )

        # Outcomes distribution
        outcome_counts = {}
        for c in all_calls:
            outcome_counts[c.status] = outcome_counts.get(c.status, 0) + 1

        outcomes = [
            OutcomeDistribution(
                status=st,
                count=cnt,
                percentage=round(cnt / calls_made * 100.0, 1) if calls_made > 0 else 0.0,
            )
            for st, cnt in outcome_counts.items()
        ]

        # Calls over time (grouped by day)
        today = datetime.now(timezone.utc).date()
        date_map = {}
        for i in range(7):
            day_str = (today - timedelta(days=6 - i)).strftime("%Y-%m-%d")
            date_map[day_str] = {"total": 0, "completed": 0, "interested": 0}

        for c in all_calls:
            day_key = c.created_at.strftime("%Y-%m-%d")
            if day_key in date_map:
                date_map[day_key]["total"] += 1
                if c.status == "COMPLETED":
                    date_map[day_key]["completed"] += 1

        calls_over_time = [
            CallsOverTimePoint(
                date=k,
                total=v["total"],
                completed=v["completed"],
                interested=int(v["completed"] * 0.4),  # proportion
            )
            for k, v in date_map.items()
        ]

        # Languages breakdown
        lang_counts = {}
        for c in all_calls:
            lang = c.language or "en"
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        languages = [LanguageStat(language=k, count=v) for k, v in lang_counts.items()]
        if not languages:
            languages = [LanguageStat(language="en", count=calls_made)]

        return AnalyticsOverviewResponse(
            summary=summary,
            calls_over_time=calls_over_time,
            outcomes=outcomes,
            languages=languages,
            question_dropoffs=[],
        )
