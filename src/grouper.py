import os
import json
from typing import TypedDict
from dotenv import load_dotenv
from groq import Groq
from src.prompt_templates import build_grouping_prompt

load_dotenv(dotenv_path=".env", override=True)

# Types 
class TransactionGroup(TypedDict):
    label: str
    items: list[str]
    confidence: str   # "high" | "medium" | "low"
    explanation: str

class GroupingSummary(TypedDict):
    total_input: int
    total_groups: int
    ungrouped_count: int

class GroupingResult(TypedDict):
    groups: list[TransactionGroup]
    ungrouped: list[str]
    summary: GroupingSummary

# Client setup
def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file")
    return Groq(api_key=api_key)

#  JSON cleaning 
def clean_llm_response(raw: str) -> str:
    """
    Strip markdown code fences if the LLM wraps response in ```json ... ```
    """
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()

# Core grouping function
def group_transactions(transactions: list[str]) -> GroupingResult:
    """
    Sends transactions to Groq LLM, parses response,
    and returns a structured GroupingResult.
    """
    client = get_client()
    prompt = build_grouping_prompt(transactions)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        raw_output = response.choices[0].message.content
    except Exception as e:
        print(f"LLM call failed: {e}")
        raise

    # Clean and parse
    cleaned = clean_llm_response(raw_output)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        print("Failed to parse LLM response as JSON. Raw output:")
        print(raw_output)
        raise

    # Calculate summary ourselves — never trust LLM for counts
    all_grouped_items = [
        item
        for group in parsed["groups"]
        for item in group["items"]
    ]
    ungrouped = [t for t in transactions if t not in all_grouped_items]

    return {
        "groups": parsed["groups"],
        "ungrouped": ungrouped,
        "summary": {
            "total_input": len(transactions),
            "total_groups": len(parsed["groups"]),
            "ungrouped_count": len(ungrouped),
        }
    }

# Output validation 
def validate_output(result: GroupingResult, original_input: list[str]) -> list[str]:
    """
    Sanity check the output before returning.
    Returns a list of warnings — empty means valid.
    """
    warnings = []

    all_grouped = [item for group in result["groups"] for item in group["items"]]
    all_items = all_grouped + result["ungrouped"]

    # Check nothing is missing
    for txn in original_input:
        if txn not in all_items:
            warnings.append(f"MISSING from output: '{txn}'")

    # Check nothing unexpected appeared
    for item in all_items:
        if item not in original_input:
            warnings.append(f"UNEXPECTED item in output: '{item}'")

    # Check all required fields exist
    for i, group in enumerate(result["groups"]):
        for field in ["label", "items", "confidence", "explanation"]:
            if field not in group or not group[field]:
                warnings.append(f"Group {i} missing field: '{field}'")

    return warnings