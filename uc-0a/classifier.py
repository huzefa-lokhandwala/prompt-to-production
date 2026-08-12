"""
UC-0A — Complaint Classifier
RICE-Enforced Implementation
"""
import argparse
import csv
import re

ALLOWED_CATEGORIES = [
    "Pothole",
    "Flooding",
    "Streetlight",
    "Waste",
    "Noise",
    "Road Damage",
    "Heritage Damage",
    "Heat Hazard",
    "Drain Blockage",
    "Other",
]

SEVERITY_KEYWORDS = [
    "injury",
    "child",
    "school",
    "hospital",
    "ambulance",
    "fire",
    "hazard",
    "fell",
    "collapse",
]

def classify_complaint(row: dict) -> dict:
    """
    Classifies a single citizen complaint row adhering strictly to RICE rules.
    """
    desc = row.get("description", "").strip()
    desc_lower = desc.lower()

    # 1. Priority Determination (Severity Keyword Rule)
    priority = "Standard"
    for kw in SEVERITY_KEYWORDS:
        # Check for keyword as word boundary or substring
        if re.search(r'\b' + re.escape(kw), desc_lower) or kw in desc_lower:
            priority = "Urgent"
            break

    # 2. Category & Ambiguity Flag Determination
    category = "Other"
    flag = ""

    # Specific category matching rules
    if "pothole" in desc_lower:
        category = "Pothole"
    elif "heritage" in desc_lower:
        category = "Heritage Damage"
        if "light" in desc_lower or "dark" in desc_lower:
            flag = "NEEDS_REVIEW"  # Overlaps Heritage Damage and Streetlight
    elif "drain" in desc_lower:
        category = "Drain Blockage"
    elif "flood" in desc_lower or "inundated" in desc_lower:
        category = "Flooding"
    elif "light" in desc_lower or "dark" in desc_lower or "lamp" in desc_lower:
        category = "Streetlight"
    elif "music" in desc_lower or "noise" in desc_lower or "loudspeaker" in desc_lower:
        category = "Noise"
    elif "garbage" in desc_lower or "waste" in desc_lower or "dump" in desc_lower or "dead animal" in desc_lower:
        category = "Waste"
        if "dead animal" in desc_lower:
            flag = "NEEDS_REVIEW"  # Non-standard sanitation waste complaint
    elif "heat" in desc_lower or "sunstroke" in desc_lower:
        category = "Heat Hazard"
    elif "road" in desc_lower or "footpath" in desc_lower or "manhole" in desc_lower or "tiles" in desc_lower:
        category = "Road Damage"
    else:
        category = "Other"
        flag = "NEEDS_REVIEW"

    # 3. Reason Generation (One sentence citing specific verbatim words)
    # Extract the first sentence or meaningful clause from description
    first_clause = desc.split(".")[0].strip() if "." in desc else desc
    reason = f"Cited '{first_clause}' from the complaint description."

    return {
        "complaint_id": row.get("complaint_id"),
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str):
    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
    results = []
    
    with open(input_path, mode="r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            classified = classify_complaint(row)
            results.append(classified)
            
    with open(output_path, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")


