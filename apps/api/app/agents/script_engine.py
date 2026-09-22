from typing import Any, Dict, List, Optional
from app.core.logging import logger
from app.schemas.script import ScriptQuestionSchema


class ScriptEngine:
    """
    Evaluates structured call scripts, condition branching, and answer validation.
    Never relies on unstructured single prompts.
    """

    @staticmethod
    def evaluate_condition(condition: Optional[dict], collected_answers: Dict[str, Any]) -> bool:
        """
        Determines whether a question condition is satisfied based on collected answers.
        Example: IF interested == true THEN ask callback_time
        """
        if not condition:
            return True

        depends_on = condition.get("depends_on_question_id")
        operator = condition.get("operator", "equals")
        expected_value = condition.get("expected_value")

        if not depends_on or depends_on not in collected_answers:
            return False

        actual_value = collected_answers[depends_on]

        if operator == "equals":
            return actual_value == expected_value
        elif operator == "not_equals":
            return actual_value != expected_value
        elif operator == "greater_than":
            try:
                return float(actual_value) > float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                return float(actual_value) < float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "in":
            if isinstance(expected_value, list):
                return actual_value in expected_value
            return str(actual_value) in str(expected_value)

        return False

    @classmethod
    def get_next_question(
        cls,
        questions: List[dict],
        collected_answers: Dict[str, Any],
    ) -> Optional[dict]:
        """
        Finds the next unanswered question whose conditions are satisfied.
        """
        for q in questions:
            q_id = q.get("id")
            if q_id in collected_answers:
                continue

            condition = q.get("condition")
            if condition:
                if not cls.evaluate_condition(condition, collected_answers):
                    continue

            return q

        return None

    @staticmethod
    def validate_answer(question: dict, value: Any) -> bool:
        """
        Validates value matches the required question type.
        """
        q_type = question.get("type", "text")

        if value is None:
            return not question.get("required", False)

        if q_type == "boolean":
            return isinstance(value, bool)

        elif q_type == "number":
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False

        elif q_type == "rating":
            try:
                num = int(value)
                return 1 <= num <= 10
            except (ValueError, TypeError):
                return False

        elif q_type == "single_choice":
            options = question.get("options") or []
            if options:
                return str(value).strip().lower() in [o.lower() for o in options]
            return True

        elif q_type == "email":
            val = str(value).strip()
            return "@" in val and "." in val

        elif q_type == "phone":
            val = str(value).strip()
            return len(val) >= 7 and any(c.isdigit() for c in val)

        return True
