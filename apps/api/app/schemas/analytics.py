from typing import List
from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_leads: int = 0
    calls_made: int = 0
    answered_calls: int = 0
    completed_calls: int = 0
    interested_leads: int = 0
    not_interested_leads: int = 0
    no_answer_calls: int = 0
    average_duration_seconds: float = 0.0
    completion_rate: float = 0.0
    conversion_rate: float = 0.0


class CallsOverTimePoint(BaseModel):
    date: str
    total: int
    completed: int
    interested: int


class OutcomeDistribution(BaseModel):
    status: str
    count: int
    percentage: float


class LanguageStat(BaseModel):
    language: str
    count: int


class QuestionDropoffStat(BaseModel):
    question_id: str
    question_text: str
    answered_count: int
    dropoff_rate: float


class AnalyticsOverviewResponse(BaseModel):
    summary: DashboardStatsResponse
    calls_over_time: List[CallsOverTimePoint]
    outcomes: List[OutcomeDistribution]
    languages: List[LanguageStat]
    question_dropoffs: List[QuestionDropoffStat] = []
