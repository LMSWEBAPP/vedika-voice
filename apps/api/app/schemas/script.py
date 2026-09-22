from datetime import datetime
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

QuestionType = Literal[
    "text",
    "number",
    "boolean",
    "single_choice",
    "multiple_choice",
    "date",
    "time",
    "phone",
    "email",
    "rating"
]


class QuestionConditionSchema(BaseModel):
    depends_on_question_id: str
    operator: Literal["equals", "not_equals", "greater_than", "less_than", "in"] = "equals"
    expected_value: Any


class QuestionValidationSchema(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    regex: Optional[str] = None


class ScriptQuestionSchema(BaseModel):
    id: str = Field(..., description="Unique question identifier, e.g. q1_interest")
    text: str = Field(..., min_length=2, description="The prompt or question spoken by the AI")
    type: QuestionType = "text"
    required: bool = True
    options: Optional[List[str]] = Field(default=None, description="Allowed choices for choice question types")
    validation: Optional[QuestionValidationSchema] = None
    condition: Optional[QuestionConditionSchema] = None
    description: Optional[str] = Field(default=None, description="Context guidance for the AI agent")


class ScriptBase(BaseModel):
    persona: str = Field(
        default="Professional, empathetic, concise, and courteous representative.",
        description="Persona and behavioral directives for the AI voice agent"
    )
    voice_name: str = Field(default="Aoede", description="Voice profile name")
    opening: str = Field(..., min_length=5, description="Greeting and introductory statement")
    objective: str = Field(..., min_length=5, description="High level goal of the conversation")
    questions: List[ScriptQuestionSchema] = Field(default_factory=list)
    closing: str = Field(..., min_length=5, description="Sign-off statement")
    fallback_response: Optional[str] = "I understand. Let me make a note of that for our specialist team."
    ai_disclosure: Optional[str] = "This is an automated AI assistant calling on behalf of our team."


class ScriptCreate(ScriptBase):
    pass


class ScriptUpdate(BaseModel):
    persona: Optional[str] = None
    voice_name: Optional[str] = None
    opening: Optional[str] = None
    objective: Optional[str] = None
    questions: Optional[List[ScriptQuestionSchema]] = None
    closing: Optional[str] = None
    fallback_response: Optional[str] = None
    ai_disclosure: Optional[str] = None


class ScriptResponse(ScriptBase):
    id: str
    campaign_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
