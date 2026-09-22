from typing import Any, Dict, List, Optional
from app.agents.script_engine import ScriptEngine


class ConversationState:
    def __init__(
        self,
        campaign_id: str,
        lead_id: str,
        language: str = "en",
        lead_name: Optional[str] = None,
        company_name: Optional[str] = None,
    ):
        self.campaign_id = campaign_id
        self.lead_id = lead_id
        self.language = language
        self.lead_name = lead_name or "Valued Contact"
        self.company_name = company_name or ""
        self.current_question_idx: int = 0
        self.answers: Dict[str, Any] = {}
        self.status: str = "active"
        self.history: List[Dict[str, str]] = []


class ConversationManager:
    """
    Maintains explicit conversation state and builds dynamic prompts for the AI agent.
    Never lets the LLM invent missing customer data.
    """

    def __init__(self, script: dict, state: ConversationState):
        self.script = script
        self.state = state

    def get_system_instruction(self) -> str:
        persona = self.script.get(
            "persona", "Professional, empathetic, concise, and courteous representative."
        )
        objective = self.script.get("objective", "Conduct outbound discovery.")
        questions = self.script.get("questions", [])
        ai_disclosure = self.script.get(
            "ai_disclosure", "This is an automated AI assistant calling on behalf of our team."
        )
        opening = self.script.get("opening", "Hello!")

        customer_info = f"Customer Name: {self.state.lead_name}"
        if self.state.company_name:
            customer_info += f", Company: {self.state.company_name}"

        return (
            f"You are an AI voice agent conducting an outbound phone call.\n"
            f"Persona: {persona}\n"
            f"AI Disclosure: {ai_disclosure}\n"
            f"Target Customer: {customer_info}\n"
            f"Primary Language: {self.state.language}\n"
            f"Campaign Objective: {objective}\n"
            f"Opening Line: '{opening}'\n\n"
            "CRITICAL RULES:\n"
            "1. Be natural, polite, and brief. Never speak long monologues.\n"
            "2. Listen actively to the user. Answer clarifying questions directly before asking the next script question.\n"
            "3. If the user indicates they are busy or not interested, politely thank them and end the call.\n"
            "4. NEVER invent or assume customer details not provided in context.\n"
            "5. If user speaks in another supported language (e.g. Hindi, Telugu), adapt gracefully.\n"
        )

    def get_next_prompt_direction(self) -> Optional[dict]:
        """Returns the next question to be asked based on condition evaluation."""
        questions = self.script.get("questions", [])
        return ScriptEngine.get_next_question(questions, self.state.answers)

    def record_answer(self, question_id: str, value: Any) -> None:
        self.state.answers[question_id] = value

    def to_dict(self) -> dict:
        return {
            "campaign_id": self.state.campaign_id,
            "lead_id": self.state.lead_id,
            "language": self.state.language,
            "answers": self.state.answers,
            "status": self.state.status,
        }
