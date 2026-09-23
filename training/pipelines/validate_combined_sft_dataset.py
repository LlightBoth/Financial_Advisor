import json
import os
import re
import sys

COMBINED_PATH = r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_v2_combined.jsonl"
ORIGINAL_PATH = r"d:\Year3\Finance\Financial_Advisor\datasets\sft_financial_advisor_v1.jsonl"
PDF_PATH = r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_pdf_v1.jsonl"

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

def validate_combined_dataset():
    print("=" * 65)
    print("VALIDATING COMBINED SFT DATASET (340 RECORDS)")
    print("=" * 65)

    errors = []

    if not os.path.exists(COMBINED_PATH):
        print(f"[FAIL] Combined file not found: {COMBINED_PATH}")
        return False

    # 1. Load source datasets for exact preservation checks
    with open(ORIGINAL_PATH, "r", encoding="utf-8") as f:
        orig_records = [json.loads(line) for line in f if line.strip()]

    with open(PDF_PATH, "r", encoding="utf-8") as f:
        pdf_records = [json.loads(line) for line in f if line.strip()]

    assert len(orig_records) == 240, f"Expected 240 original records, got {len(orig_records)}"
    assert len(pdf_records) == 100, f"Expected 100 PDF records, got {len(pdf_records)}"

    # 2. Read combined records
    combined_records = []
    with open(COMBINED_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                errors.append(f"Line {line_num}: Empty line found")
                continue
            try:
                rec = json.loads(line_str)
                combined_records.append(rec)
            except Exception as e:
                errors.append(f"Line {line_num}: Malformed JSON - {e}")

    total_records = len(combined_records)
    print(f"Total records loaded: {total_records}")
    if total_records != 340:
        errors.append(f"Expected exactly 340 records, found {total_records}")

    # 3. Check exact preservation of first 240 and next 100
    orig_preserved_count = 0
    pdf_preserved_count = 0

    for i in range(min(len(orig_records), total_records)):
        if combined_records[i] == orig_records[i]:
            orig_preserved_count += 1
        else:
            errors.append(f"Record {i+1}: Does not match original baseline record")

    for j in range(min(len(pdf_records), max(0, total_records - 240))):
        comb_idx = 240 + j
        if comb_idx < total_records and combined_records[comb_idx] == pdf_records[j]:
            pdf_preserved_count += 1
        else:
            errors.append(f"Record {comb_idx+1}: Does not match PDF-derived record {j+1}")

    # 4. Check schema, duplicates, forbidden terms, and slot constraints
    seen_inputs = set()
    duplicate_count = 0
    categories = {
        "Original: Structured Slot Extraction": 0,
        "Original: Missing Information Diagnosis": 0,
        "Original: Recommendation Explanations": 0,
        "Original: Safe Financial Education": 0,
        "Original: Guardrails & Professional Boundaries": 0,
        "PDF-Derived: Client Fact Discovery": 0,
        "PDF-Derived: Missing Information": 0,
        "PDF-Derived: Cash Flow & Savings Capacity": 0,
        "PDF-Derived: Emergency Reserve Education": 0,
        "PDF-Derived: Financial Education": 0,
        "PDF-Derived: Goals & Priorities": 0,
        "PDF-Derived: Communication Style": 0,
        "PDF-Derived: Risk Education": 0,
        "PDF-Derived: Professional Boundaries & Safety": 0,
    }

    for idx, rec in enumerate(combined_records, 1):
        # Schema check
        if set(rec.keys()) != {"instruction", "input", "output"}:
            errors.append(f"Record {idx}: Keys mismatch: {set(rec.keys())}")

        instr = rec.get("instruction", "")
        inp = rec.get("input", "")
        out = rec.get("output", "")

        if not instr.strip() or not inp.strip() or not out.strip():
            errors.append(f"Record {idx}: Empty instruction, input, or output")

        # Duplicate check across entire 340
        inp_norm = inp.strip().lower()
        if inp_norm in seen_inputs:
            duplicate_count += 1
            errors.append(f"Record {idx}: Duplicate input: '{inp[:50]}...'")
        seen_inputs.add(inp_norm)

        # Forbidden internal terms
        for term_pat in FORBIDDEN_INTERNAL_TERMS:
            if re.search(term_pat, out, re.IGNORECASE):
                errors.append(f"Record {idx}: Output contains forbidden internal term '{term_pat}'")

        # Speculative recommendations
        for spec_pat in FORBIDDEN_SPECULATIVE_TERMS:
            if re.search(spec_pat, out, re.IGNORECASE):
                if "cannot" not in out.lower() and "refuse" not in out.lower() and "do not" not in out.lower():
                    errors.append(f"Record {idx}: Output contains speculative/guaranteed recommendation: '{spec_pat}'")

        # Structured extraction checks
        if "Extract the user's financial profile" in instr:
            try:
                slots = json.loads(out)
                canonical_keys = {"monthly_income", "monthly_expense", "goal_cost", "employment_status", "debt_status", "spending_habit", "marital_status"}
                if set(slots.keys()) != canonical_keys:
                    errors.append(f"Record {idx}: Canonical slot keys mismatch: {set(slots.keys())}")

                # Ensure currency values are numeric float/int or null
                for num_key in ["monthly_income", "monthly_expense", "goal_cost"]:
                    val = slots.get(num_key)
                    if val is not None and not isinstance(val, (int, float)):
                        errors.append(f"Record {idx}: Slot '{num_key}' is not numeric float/int: {repr(val)}")

                # Check explicit zero
                if "no income" in inp.lower() or "zero income" in inp.lower():
                    if slots.get("monthly_income") != 0.0:
                        errors.append(f"Record {idx}: Explicit zero income not preserved: {slots.get('monthly_income')}")

            except Exception as e:
                errors.append(f"Record {idx}: Failed parsing JSON slot output: {e}")

        # Tally categories
        is_original = (idx <= 240)
        if is_original:
            if "Extract the user's financial profile" in instr:
                categories["Original: Structured Slot Extraction"] += 1
            elif "critical information is missing or ambiguous" in instr:
                categories["Original: Missing Information Diagnosis"] += 1
            elif "Understanding Your Recommendation" in instr:
                categories["Original: Recommendation Explanations"] += 1
            elif "Explain the personal finance concept" in instr:
                categories["Original: Safe Financial Education"] += 1
            elif "maintaining strict professional boundaries" in instr:
                categories["Original: Guardrails & Professional Boundaries"] += 1
        else:
            if "Extract the user's financial profile" in instr:
                categories["PDF-Derived: Client Fact Discovery"] += 1
            elif "client discovery principles" in instr:
                categories["PDF-Derived: Missing Information"] += 1
            elif "personal cash flow" in instr:
                if "emergency" in inp.lower():
                    categories["PDF-Derived: Emergency Reserve Education"] += 1
                else:
                    categories["PDF-Derived: Cash Flow & Savings Capacity"] += 1
            elif "foundational financial planning concept" in instr:
                categories["PDF-Derived: Financial Education"] += 1
            elif "goal setting and milestone prioritization" in instr:
                categories["PDF-Derived: Goals & Priorities"] += 1
            elif "empathetic, and jargon-free language" in instr:
                categories["PDF-Derived: Communication Style"] += 1
            elif "personal finance risk concept" in instr:
                categories["PDF-Derived: Risk Education"] += 1
            elif "maintaining strict professional boundaries" in instr:
                categories["PDF-Derived: Professional Boundaries & Safety"] += 1

    # 5. Output Summary
    print(f"\n--- Dataset Source Counts ---")
    print(f"Original Baseline Records: {orig_preserved_count}/240 preserved")
    print(f"PDF-Derived Records: {pdf_preserved_count}/100 preserved")
    print(f"Total Records: {total_records}/340")
    print(f"Duplicate Inputs Found: {duplicate_count}")

    print(f"\n--- Category Distribution across 340 Examples ---")
    for cat, count in categories.items():
        print(f"  - {cat}: {count} examples")

    passed = (len(errors) == 0 and total_records == 340 and orig_preserved_count == 240 and pdf_preserved_count == 100 and duplicate_count == 0)

    if errors:
        print(f"\n[FAIL] Found {len(errors)} validation errors:")
        for err in errors[:10]:
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors.")
    else:
        print("\n[PASS] All 340 records verified successfully with zero errors and zero duplicates!")

    return passed

if __name__ == "__main__":
    success = validate_combined_dataset()
    sys.exit(0 if success else 1)
