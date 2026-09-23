import json
import os

ORIGINAL_PATH = r"d:\Year3\Finance\Financial_Advisor\datasets\sft_financial_advisor_v1.jsonl"
PDF_PATH = r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_pdf_v1.jsonl"
COMBINED_PATH = r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_v2_combined.jsonl"

def build_combined_dataset():
    print("=" * 65)
    print("BUILDING COMBINED SFT DATASET (340 EXAMPLES)")
    print("=" * 65)

    if not os.path.exists(ORIGINAL_PATH):
        raise FileNotFoundError(f"Original dataset not found: {ORIGINAL_PATH}")
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(f"PDF-derived dataset not found: {PDF_PATH}")

    combined_records = []

    # 1. Read original 240 examples
    orig_count = 0
    with open(ORIGINAL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                assert set(item.keys()) == {"instruction", "input", "output"}
                combined_records.append(item)
                orig_count += 1

    print(f"Read {orig_count} original records from: {ORIGINAL_PATH}")
    assert orig_count == 240, f"Expected 240 original records, got {orig_count}"

    # 2. Read PDF-derived 100 examples
    pdf_count = 0
    with open(PDF_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                assert set(item.keys()) == {"instruction", "input", "output"}
                combined_records.append(item)
                pdf_count += 1

    print(f"Read {pdf_count} PDF-derived records from: {PDF_PATH}")
    assert pdf_count == 100, f"Expected 100 PDF-derived records, got {pdf_count}"

    # Total check
    assert len(combined_records) == 340, f"Expected 340 total records, got {len(combined_records)}"

    # 3. Save combined dataset
    os.makedirs(os.path.dirname(COMBINED_PATH), exist_ok=True)
    with open(COMBINED_PATH, "w", encoding="utf-8") as f:
        for record in combined_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Successfully wrote {len(combined_records)} records to: {COMBINED_PATH}")
    print("=" * 65)

if __name__ == "__main__":
    build_combined_dataset()
