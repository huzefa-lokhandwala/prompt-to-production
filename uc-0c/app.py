"""
UC-0C app.py — Municipal Budget Growth Auditor
RICE-Enforced Implementation
"""
import argparse
import csv
import sys

FORMULA_MOM_STR = "((actual_spend_current - actual_spend_prev) / actual_spend_prev) * 100"

def load_dataset(input_path: str):
    """
    Loads CSV dataset, identifies null actual_spend rows, and prints audit report.
    Returns list of parsed row dicts.
    """
    rows = []
    null_rows = []

    with open(input_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # Line number including header
            raw_spend = row["actual_spend"].strip()
            if not raw_spend:
                parsed_spend = None
                null_rows.append({
                    "line": i,
                    "period": row["period"],
                    "ward": row["ward"],
                    "category": row["category"],
                    "notes": row["notes"]
                })
            else:
                parsed_spend = float(raw_spend)

            rows.append({
                "period": row["period"],
                "ward": row["ward"],
                "category": row["category"],
                "budgeted_amount": float(row["budgeted_amount"]),
                "actual_spend": parsed_spend,
                "notes": row["notes"]
            })

    print(f"Loaded {len(rows)} budget rows from {input_path}.")
    print(f"Audit Flag: Found {len(null_rows)} deliberate null actual_spend rows:")
    for nr in null_rows:
        print(f"  - Line {nr['line']} [{nr['period']}] {nr['ward']} | {nr['category']} -> Reason: '{nr['notes']}'")

    return rows, null_rows


def compute_growth(rows: list, ward: str, category: str, growth_type: str) -> list:
    """
    Computes per-period growth for a specific ward and category.
    Refuses cross-ward aggregation or missing growth type.
    """
    # 1. Parameter Enforcement Rules
    if not growth_type:
        raise ValueError("REFUSAL: Growth calculation type (--growth-type) is required. Please specify 'MoM' or 'YoY'.")
    
    if growth_type.upper() not in ["MOM", "YOY"]:
        raise ValueError(f"REFUSAL: Unsupported growth_type '{growth_type}'. Allowed values: 'MoM', 'YoY'.")

    if not ward or not category or "ALL" in ward.upper() or "ALL" in category.upper():
        raise ValueError("REFUSAL: All-ward or cross-category aggregation is strictly prohibited. You must specify a single ward and single category.")

    # 2. Filter dataset for target ward and category, ordered by period
    filtered = [r for r in rows if r["ward"] == ward and r["category"] == category]
    filtered.sort(key=lambda x: x["period"])

    if not filtered:
        raise ValueError(f"No records found for Ward '{ward}' and Category '{category}'.")

    results = []
    
    for i, curr in enumerate(filtered):
        curr_spend = curr["actual_spend"]
        
        if curr_spend is None:
            growth_str = "N/A"
            formula_used = "N/A (Null spend)"
            display_spend = "NULL"
        elif i == 0:
            growth_str = "N/A"
            formula_used = "N/A (Initial Period)"
            display_spend = f"{curr_spend:.1f}"
        else:
            prev_spend = filtered[i-1]["actual_spend"]
            display_spend = f"{curr_spend:.1f}"
            
            if prev_spend is None or prev_spend == 0:
                growth_str = "N/A"
                formula_used = "N/A (Previous Period Null or Zero)"
            else:
                pct = ((curr_spend - prev_spend) / prev_spend) * 100
                growth_str = f"{pct:+.1f}%"
                formula_used = FORMULA_MOM_STR

        results.append({
            "period": curr["period"],
            "ward": curr["ward"],
            "category": curr["category"],
            "budgeted_amount": f"{curr['budgeted_amount']:.1f}",
            "actual_spend": display_spend,
            "growth_pct": growth_str,
            "formula": formula_used,
            "notes": curr["notes"]
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="UC-0C Municipal Budget Growth Auditor")
    parser.add_argument("--input", required=True, help="Path to ward_budget.csv")
    parser.add_argument("--ward", required=False, help="Ward name (e.g. 'Ward 1 – Kasba')")
    parser.add_argument("--category", required=False, help="Category name")
    parser.add_argument("--growth-type", required=False, help="Growth type: MoM or YoY")
    parser.add_argument("--output", required=False, help="Output CSV path")
    args = parser.parse_args()

    # Load dataset & run null audit
    dataset, null_rows = load_dataset(args.input)

    # Compute growth with strict RICE checks
    try:
        results = compute_growth(dataset, args.ward, args.category, args.growth_type)
    except ValueError as e:
        print(f"\n[ERROR/REFUSAL] {e}", file=sys.stderr)
        sys.exit(1)

    # Write output CSV if requested
    output_file = args.output or "growth_output.csv"
    fieldnames = ["period", "ward", "category", "budgeted_amount", "actual_spend", "growth_pct", "formula", "notes"]
    
    with open(output_file, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSuccessfully generated {output_file} with {len(results)} rows.")


if __name__ == "__main__":
    main()


