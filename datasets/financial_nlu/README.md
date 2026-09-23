# Financial Advisor NLU Dataset — English Only (Phase 1)

**Project**: Personal Financial Advisor Expert System  
**Knowledge Base**: `financial-kb-v1.0`  
**Language Scope**: **ENGLISH ONLY**  
**Dataset Schema Version**: `nlu_schema_v1`

---

## Purpose

This directory contains the machine-readable schema, controlled template library, and future dataset assets for training an English Natural Language Understanding (NLU) slot-extraction model.

The NLU model's sole responsibility is **information extraction**: parsing free-form English text into structured financial slots. It does **NOT** make financial decisions.

**Architecture**:
```
English User Text
       ↓
 NLU Model (Future)
       ↓
 Intent + Canonical Slots
       ↓
 ConsultantValidator
       ↓
 ConsultantMetrics
       ↓
 ConsultantEngine
       ↓
 Deterministic Rule + Advice
```

The deterministic `ConsultantEngine` remains the sole, authoritative financial decision-maker.

---

## Canonical Slots (7 Required Keys)

Every dataset record must include all 7 keys. Missing information is `null`, never omitted.

| Slot | Type | Valid Values |
|:---|:---|:---|
| `monthly_income` | `float ≥ 0` or `null` | Non-negative number or null |
| `monthly_expense` | `float ≥ 0` or `null` | Non-negative number or null |
| `employment_status` | `string` or `null` | `"employed"`, `"not employed"`, or null |
| `debt_status` | `string` or `null` | `"debt"`, `"no debt"`, or null |
| `spending_habit` | `string` or `null` | `"average spend"`, `"big spend"`, or null |
| `goal_cost` | `float ≥ 0` or `null` | Non-negative number or null |
| `marital_status` | `string` or `null` | `"Single"`, `"Married"`, or null |

---

## Intent Taxonomy (9 Intents)

| Intent | Routes to Engine? |
|:---|:---:|
| `financial_consultation` | YES |
| `budget_analysis` | YES |
| `cashflow_question` | YES |
| `savings_question` | YES |
| `debt_management` | YES |
| `financial_goal` | YES |
| `financial_education` | NO |
| `out_of_scope_investment` | NO |
| `out_of_scope_loan` | NO |

---

## Critical Safety Invariants

### The Null Invariant
```
Unknown ≠ 0.0
```
- Omission of information → `null`
- Explicit declaration of zero → `0.0`
- Explicit absence of debt → `"no debt"`
- Unmentioned debt → `null`

### Annual/Monthly Safety
The NLU model must **NEVER** silently convert annual figures to monthly figures. If the user states an annual amount without explicit monthly cadence, the slot must be `null`.

### Template-Grouped Splitting
All examples sharing the same `template_id` must reside in the **same** train/val/test split to prevent data leakage.

### Near-Duplicate Detection
The pipeline must detect exact duplicates, punctuation-only differences, and semantic near-duplicates before approving any dataset split.

### Expected Rule ID Computation
The `expected_rule_id` field must be computed by running slots through `ConsultantValidator` → `ConsultantMetrics` → `ConsultantEngine`. Human annotators must NOT manually invent rule IDs.

---

## Canonical Rule IDs (from `consultant_engine.py`)

```
DEFICIT_WITH_DEBT
DEFICIT_NO_DEBT
INCOME_ZERO_UNEMPLOYED
BREAK_EVEN_ZERO_MARGIN
TIGHT_MARGIN_HIGH_EXPENSE
SURPLUS_WITH_DEBT_SERVICING
BALANCED_BUDGET_BUFFER_BUILDING
FLEXIBLE_BUDGET_CAPITAL_GROWTH
```

---

## PDF Copyright & Provenance Policy

The CFA and Wiley reference PDFs under `pdf_data/` are conceptual references **only**.
- **No text, paragraphs, definitions, or practice questions** may be copied verbatim.
- All training utterances must be **100% original**.
- When a concept inspired a template, use provenance tags: `CFA_LM2_TVM`, `WILEY_CH15_BUFFER`, etc.

---

## Dataset Size Targets

These are **project planning targets**, not guarantees of model performance.

| Tier | Size |
|:---|:---|
| Minimum | ~1,400 examples |
| Recommended | ~3,000 examples |

---

## Directory Structure

```
datasets/financial_nlu/
├── README.md                   ← This file
├── schemas/
│   └── nlu_schema_v1.json      ← Formal JSON Schema contract
├── templates/
│   ├── budget_templates.json
│   ├── cashflow_templates.json
│   ├── debt_templates.json
│   ├── savings_templates.json
│   ├── employment_templates.json
│   ├── household_templates.json
│   ├── missing_info_templates.json
│   └── out_of_scope_templates.json
├── raw/                        ← (Future) Generated unverified records
├── reviewed/                   ← (Future) Human-reviewed records
├── final/                      ← (Future) Approved dataset
├── splits/                     ← (Future) Train/Val/Test JSONL files
└── reports/                    ← (Future) Automated audit reports
```

---

## Multilingual Roadmap

| Phase | Scope |
|:---|:---|
| **Phase 1** (Current) | English only |
| Phase 2 (Future) | Khmer (Native script) |
| Phase 3 (Future) | Mixed Khmer-English code-switching |

---

## Current Status

```
TRAINING STATUS: NOT STARTED
MODEL CREATION STATUS: NOT STARTED
MODEL NAME: USER WILL DEFINE LATER
LANGUAGE SCOPE: ENGLISH ONLY
STEP 8C STATUS: COMPLETE
NEXT STEP: REVIEW TEMPLATE FOUNDATION
```
