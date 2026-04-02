import pytest
from src.grouper import clean_llm_response, validate_output


"""
Unit tests for parsing and post-processing logic.
Run with: pytest tests/test_grouper.py -v
"""

# Tests for clean_llm_response 

def test_clean_response_strips_json_markdown():
    """LLM sometimes wraps response in ```json ... ``` — we must strip it"""
    raw = "```json\n{\"groups\": []}\n```"
    result = clean_llm_response(raw)
    assert result == '{"groups": []}'


def test_clean_response_leaves_plain_json_unchanged():
    """Plain JSON should pass through untouched"""
    raw = '{"groups": []}'
    result = clean_llm_response(raw)
    assert result == '{"groups": []}'


def test_clean_response_strips_whitespace():
    """Leading and trailing whitespace should be stripped"""
    raw = '   {"groups": []}   '
    result = clean_llm_response(raw)
    assert result == '{"groups": []}'


# Tests for validate_output 

def test_validate_output_passes_when_all_items_grouped():
    """No warnings when all transactions are accounted for"""
    result = {
        "groups": [
            {
                "label": "Ride-hailing",
                "items": ["Uber trip 1200", "Bolt ride 900"],
                "confidence": "high",
                "explanation": "Both are ride services"
            }
        ],
        "ungrouped": [],
        "summary": {
            "total_input": 2,
            "total_groups": 1,
            "ungrouped_count": 0
        }
    }
    original = ["Uber trip 1200", "Bolt ride 900"]
    warnings = validate_output(result, original)
    assert warnings == []


def test_validate_output_catches_missing_transaction():
    """Warning raised when a transaction is missing from output"""
    result = {
        "groups": [
            {
                "label": "Ride-hailing",
                "items": ["Uber trip 1200"],
                "confidence": "high",
                "explanation": "Ride service"
            }
        ],
        "ungrouped": [],
        "summary": {
            "total_input": 2,
            "total_groups": 1,
            "ungrouped_count": 0
        }
    }
    original = ["Uber trip 1200", "Bolt ride 900"]
    warnings = validate_output(result, original)
    assert any("MISSING" in w for w in warnings)


def test_validate_output_catches_unexpected_item():
    """Warning raised when output contains item not in original input"""
    result = {
        "groups": [
            {
                "label": "Ride-hailing",
                "items": ["Uber trip 1200", "FAKE TRANSACTION"],
                "confidence": "high",
                "explanation": "Ride service"
            }
        ],
        "ungrouped": [],
        "summary": {
            "total_input": 1,
            "total_groups": 1,
            "ungrouped_count": 0
        }
    }
    original = ["Uber trip 1200"]
    warnings = validate_output(result, original)
    assert any("UNEXPECTED" in w for w in warnings)


def test_validate_output_catches_missing_field():
    """Warning raised when a group is missing a required field"""
    result = {
        "groups": [
            {
                "label": "Ride-hailing",
                "items": ["Uber trip 1200"],
                "confidence": "high",
                # explanation is missing
            }
        ],
        "ungrouped": [],
        "summary": {
            "total_input": 1,
            "total_groups": 1,
            "ungrouped_count": 0
        }
    }
    original = ["Uber trip 1200"]
    warnings = validate_output(result, original)
    assert any("explanation" in w for w in warnings)