import json
import os
import re
import sys

NEW_DATASET_PATH = r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_pdf_v1.jsonl"
EXISTING_DATASET_PATHS = [
    r"d:\Year3\Finance\Financial_Advisor\datasets\sft_financial_advisor_v1.jsonl",
    r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_v1.jsonl"
]

FORBIDDEN_INTERNAL_TERMS = [
    r"\bRULE_\w+\b",
    r"\bR00\d\b",
    r"\bConsultantEngine\b",
    r"\bPABL\b",
    r"\bprovenance\b",
    r"\bdecision_trace\b",
    r"\bspecificity\b",
    r"\bLoRA\b",
    r"\bQLoRA\b",
    r"\bdatabase\b",
    r"\bsqlite\b",
    r"\bmysql\b",
    r"\bpostgres\b"
]

FORBIDDEN_SPECULATIVE_TERMS = [
    r"\bbuy\s+(bitcoin|btc|eth|ethereum|doge|solana|crypto|stock|tesla|apple)\b",
    r"\bguaranteed\s+(return|profit|yield|rate)\b",
    r"\bguarantee\s+\d+%\b",
    r"\brisk-free\s+(return|investment)\b",
    r"\b100%\s+guaranteed\b"
]

def validate_dataset():
    print("=" * 65)
    print("PDF-DERIVED SFT DATASET VALIDATION")
    print("=" * 65)

    if not os.path.exists(NEW_DATASET_PATH):
        print(f"[FAIL] Dataset file does not exist: {NEW_DATASET_PATH}")
        return False

    # 1. Load existing 240-example dataset to check for duplicates
    existing_inputs = set()
    found_existing = False
    for p in EXISTING_DATASET_PATHS:
        if os.path.exists(p):
            found_existing = True
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            item = json.loads(line)
                            inp = item.get("input", "").strip().lower()
                            if inp:
                                existing_inputs.add(inp)
                        except Exception:
                            pass
            print(f"Loaded existing baseline inputs ({len(existing_inputs)}) from: {p}")
            break

    if not found_existing:
        print("[WARNING] Existing 240-example dataset was not found at standard paths.")

    # 2. Process and Validate New Dataset
    total_records = 0
    seen_new_inputs = set()
    duplicate_with_existing = 0
    safety_violations = 0
    errors = []
    category_counts = {
        "Client Fact Discovery": 0,
        "Missing Information": 0,
        "Cash Flow & Savings Capacity": 0,
        "Emergency Reserve Education": 0,
        "Financial Education": 0,
        "Goals & Priorities": 0,
        "Communication Style": 0,
        "Risk Education": 0,
        "Professional Boundaries": 0,
        "Safe Financial Guidance": 0
    }

    with open(NEW_DATASET_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                errors.append(f"Line {line_num}: Empty line found in JSONL")
                continue

            # Check valid JSON
            try:
                record = json.loads(line_str)
            except Exception as e:
                errors.append(f"Line {line_num}: Malformed JSON - {e}")
                continue

            total_records += 1

            # Exact required fields
            required_keys = {"instruction", "input", "output"}
            if set(record.keys()) != required_keys:
                errors.append(f"Line {line_num}: Keys mismatch. Expected {required_keys}, got {set(record.keys())}")

            instr = record.get("instruction", "")
            inp = record.get("input", "")
            out = record.get("output", "")

            if not isinstance(instr, str) or not instr.strip():
                errors.append(f"Line {line_num}: Empty instruction")
            if not isinstance(inp, str) or not inp.strip():
                errors.append(f"Line {line_num}: Empty input")
            if not isinstance(out, str) or not out.strip():
                errors.append(f"Line {line_num}: Empty output")

            # Check text length to avoid textbook-length verbatim passages
            if len(out) > 1500:
                errors.append(f"Line {line_num}: Output is excessively long ({len(out)} chars) - potential uncurated passage")

            # Check duplicate within new dataset
            inp_norm = inp.strip().lower()
            if inp_norm in seen_new_inputs:
                errors.append(f"Line {line_num}: Duplicate input within new dataset: '{inp[:50]}...'")
            seen_new_inputs.add(inp_norm)

            # Check duplicate with existing 240-example dataset
            if inp_norm in existing_inputs:
                duplicate_with_existing += 1
                errors.append(f"Line {line_num}: Exact duplicate of existing baseline dataset input: '{inp[:50]}...'")

            # Check forbidden internal terms in user-facing output
            for term_pat in FORBIDDEN_INTERNAL_TERMS:
                if re.search(term_pat, out, re.IGNORECASE):
                    errors.append(f"Line {line_num}: Output contains internal software/engine term matching '{term_pat}'")

            # Check safety violations in output
            for spec_pat in FORBIDDEN_SPECULATIVE_TERMS:
                # Check if model is recommending this in output (not just refusing it)
                if re.search(spec_pat, out, re.IGNORECASE):
                    # Check if output is a refusal or an actual recommendation
                    if "cannot" not in out.lower() and "refuse" not in out.lower() and "do not" not in out.lower():
                        safety_violations += 1
                        errors.append(f"Line {line_num}: Output contains speculative/guaranteed recommendation: '{spec_pat}'")

            # Check structured extraction constraints
            if "Extract the user's financial profile" in instr:
                category_counts["Client Fact Discovery"] += 1
                try:
                    slot_dict = json.loads(out)
                    expected_slots = {
                        "monthly_income", "monthly_expense", "goal_cost",
                        "employment_status", "debt_status", "spending_habit", "marital_status"
                    }
                    if set(slot_dict.keys()) != expected_slots:
                        errors.append(f"Line {line_num}: Structured slot keys mismatch: {set(slot_dict.keys())}")
                    
                    # Verify numeric currency values are float/int or null (never strings like "$5,000")
                    for num_field in ["monthly_income", "monthly_expense", "goal_cost"]:
                        val = slot_dict.get(num_field)
                        if val is not None and not isinstance(val, (int, float)):
                            errors.append(f"Line {line_num}: Structured {num_field} is not numeric float/null: {repr(val)}")

                except Exception as e:
                    errors.append(f"Line {line_num}: Structured extraction output failed JSON parsing: {e}")

            elif "client discovery principles" in instr:
                category_counts["Missing Information"] += 1
            elif "personal cash flow" in instr:
                if "emergency reserve" in inp.lower() or "emergency" in inp.lower():
                    category_counts["Emergency Reserve Education"] += 1
                else:
                    category_counts["Cash Flow & Savings Capacity"] += 1
            elif "foundational financial planning concept" in instr:
                category_counts["Financial Education"] += 1
            elif "goal setting and milestone prioritization" in instr:
                category_counts["Goals & Priorities"] += 1
            elif "empathetic, and jargon-free language" in instr:
                category_counts["Communication Style"] += 1
            elif "personal finance risk concept" in instr:
                category_counts["Risk Education"] += 1
            elif "maintaining strict professional boundaries" in instr:
                if "guarantee" in inp.lower() or "profit" in inp.lower() or "overriding" in inp.lower():
                    category_counts["Safe Financial Guidance"] += 1
                else:
                    category_counts["Professional Boundaries"] += 1
            else:
                category_counts["Financial Education"] += 1

    print(f"Total PDF-derived examples validated: {total_records}")
    print("\nCategory Distribution:")
    for cat, count in category_counts.items():
        print(f"  - {cat}: {count} examples")

    print(f"\nDuplicates with existing 240-example dataset: {duplicate_with_existing}")
    print(f"Safety violations found: {safety_violations}")

    passed = (len(errors) == 0 and total_records >= 80 and duplicate_with_existing == 0 and safety_violations == 0)

    if errors:
        print(f"\n[FAIL] Found {len(errors)} validation errors:")
        for err in errors[:10]:
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors.")
    else:
        print("\n[PASS] All validation checks passed with zero errors, zero duplicates, and zero safety violations!")

    return passed

if __name__ == "__main__":
    success = validate_dataset()
    sys.exit(0 if success else 1)
