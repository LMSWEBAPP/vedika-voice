import pytest
from app.agents.script_engine import ScriptEngine


def test_evaluate_condition():
    # Condition: depends on 'interested' == True
    cond = {
        "depends_on_question_id": "interested",
        "operator": "equals",
        "expected_value": True,
    }
    assert ScriptEngine.evaluate_condition(cond, {"interested": True}) is True
    assert ScriptEngine.evaluate_condition(cond, {"interested": False}) is False
    assert ScriptEngine.evaluate_condition(cond, {}) is False


def test_get_next_question():
    questions = [
        {"id": "q1", "text": "Are you interested?", "type": "boolean"},
        {
            "id": "q2",
            "text": "What is your team size?",
            "type": "number",
            "condition": {
                "depends_on_question_id": "q1",
                "operator": "equals",
                "expected_value": True,
            },
        },
        {"id": "q3", "text": "What is your email?", "type": "email"},
    ]

    # Initially should pick q1
    next_q = ScriptEngine.get_next_question(questions, {})
    assert next_q["id"] == "q1"

    # If q1 answered False, q2 condition fails, so skip to q3
    next_q_skipped = ScriptEngine.get_next_question(questions, {"q1": False})
    assert next_q_skipped["id"] == "q3"

    # If q1 answered True, q2 should be picked
    next_q_branch = ScriptEngine.get_next_question(questions, {"q1": True})
    assert next_q_branch["id"] == "q2"


def test_validate_answer():
    assert ScriptEngine.validate_answer({"type": "boolean"}, True) is True
    assert ScriptEngine.validate_answer({"type": "boolean"}, "not-a-bool") is False
    assert ScriptEngine.validate_answer({"type": "number"}, 42) is True
    assert ScriptEngine.validate_answer({"type": "number"}, "42") is True
    assert ScriptEngine.validate_answer({"type": "number"}, "abc") is False
    assert ScriptEngine.validate_answer({"type": "email"}, "test@example.com") is True
    assert ScriptEngine.validate_answer({"type": "email"}, "invalid-email") is False
    assert ScriptEngine.validate_answer({"type": "rating"}, 7) is True
    assert ScriptEngine.validate_answer({"type": "rating"}, 15) is False
