import json

def build_grouping_prompt(transactions: list[str]) -> str:
    """
    Builds the prompt sent to the LLM.
    Keeps prompt logic separate from API call logic.
    """
    return f"""
You are a financial transaction classifier for a Nigerian tax system.

Your job is to group the transactions below into meaningful semantic categories.

STRICT RULES:
1. Group by MEANING not spelling. "Uber trip" and "uber ride lagos" are the same category.
2. Every transaction MUST appear in exactly one group.
3. Do NOT include an ungrouped list — put everything in a group.
4. Confidence levels:
   - "high": obvious match, no doubt
   - "medium": reasonable but not certain
   - "low": best guess, could be wrong
5. Return ONLY valid JSON. No markdown, no explanation outside the JSON.

Return ONLY this structure:
{{
  "groups": [
    {{
      "label": "string",
      "items": ["string"],
      "confidence": "high | medium | low",
      "explanation": "string"
    }}
  ]
}}

Transactions:
{json.dumps(transactions, indent=2)}
"""