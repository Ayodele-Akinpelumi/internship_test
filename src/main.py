import json
import os
from src.grouper import group_transactions, validate_output

def main():
    # Load sample data
    data_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "sample_input.json"
    )

    with open(data_path) as f:
        data = json.load(f)

    transactions = data["transactions"]
    print(f"🔹 Processing {len(transactions)} transactions...\n")

    # Run grouping
    result = group_transactions(transactions)

    # Validate
    warnings = validate_output(result, transactions)
    if warnings:
        print("Validation warnings:")
        for w in warnings:
            print(f"   - {w}")
        print()
    else:
        print("Validation passed — all transactions accounted for.\n")

    # Print output
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Summary
 
    print(f"Groups found: {result['summary']['total_groups']}")
    print(f"Ungrouped:    {result['summary']['ungrouped_count']}")

if __name__ == "__main__":
    main()