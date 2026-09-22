from typing import Any, Dict, List, Optional
from app.agents.script_engine import ScriptEngine
from app.core.logging import logger


class ExtractionResult:
    def __init__(
        self,
        question_id: str,
        question_text: str,
        raw_answer: str,
        extracted_value: Any,
        is_valid: bool,
        confidence: float,
    ):
        self.question_id = question_id
        self.question_text = question_text
        self.raw_answer = raw_answer
        self.extracted_value = extracted_value
        self.is_valid = is_valid
        self.confidence = confidence


class DataExtractor:
    """
    Extracts and validates structured information from call transcripts.
    Ensures answers adhere to expected types and schema.
    """

    @classmethod
    def process_extracted_dict(
        cls,
        raw_extracted: Dict[str, Any],
        questions: List[dict],
        transcript_history: List[dict],
    ) -> List[ExtractionResult]:
        results: List[ExtractionResult] = []

        q_map = {q["id"]: q for q in questions}

        for q_id, q_def in q_map.items():
            val = raw_extracted.get(q_id)
            if val is None:
                continue

            q_text = q_def.get("text", "")
            is_valid = ScriptEngine.validate_answer(q_def, val)
            confidence = 0.95 if is_valid else 0.40

            results.append(
                ExtractionResult(
                    question_id=q_id,
                    question_text=q_text,
                    raw_answer=str(val),
                    extracted_value=val,
                    is_valid=is_valid,
                    confidence=confidence,
                )
            )

        return results
