# Step 8E — Controlled NLU Dataset Expansion Plan (Batch 1: 100 Records Target)

**Project**: Personal Financial Advisor Expert System  
**Knowledge Base Version**: `financial-kb-v1.0`  
**Language Scope**: **ENGLISH ONLY** (Phase 1)  
**Status**: Specification & Planning Document Only (No Training, No Model Creation, No External APIs)

---

## 1. Executive Summary & Objective

Step 8D successfully established and validated an initial 22-record annotation dry run (`datasets/financial_nlu/raw/annotation_dry_run.jsonl`). Quality review (Step 8E) verified that all 22 records strictly conform to the NLU schema contract and achieve 100% deterministic alignment with the authoritative `ConsultantEngine`.

This plan specifies the parameters for **Controlled Expansion Batch 1**: scaling from the initial 22 dry-run records to a total milestone target of **100 high-quality, verified English records** (78 new records).

---

## 2. Target Batch Size & Split Allocation

### 2.1 Batch Sizing
* **Current verified records**: 22
* **Target total records**: 100
* **New records to author**: 78
* **Batch ceiling**: Exactly 100 records maximum (no mass-generation).

### 2.2 Template-Grouped Split Policy (Zero-Leakage Invariant)
To prevent data leakage, dataset partitioning is assigned at the **template level**, never at the record level. All examples generated from a given `template_id` must reside in the exact same split:

| Split | Target Proportion | Target Record Count | Template Families Assigned |
|:---|:---:|:---:|:---|
| **Train** | ~70% | 70 | `TF_BUDGET` (subset), `TF_DEBT` (subset), `TF_SAVINGS` (subset), `TF_HOUSEHOLD` (subset), `TF_EMPLOYMENT` (subset), `TF_MISSING_INFO` (subset) |
| **Validation** | ~15% | 15 | `TF_BUDGET` (subset), `TF_CASHFLOW` (subset), `TF_MISSING_INFO` (subset) |
| **Test** | ~15% | 15 | `TF_EMPLOYMENT` (subset), `TF_MISSING_INFO` (subset), `TF_OUT_OF_SCOPE` (subset) |

---

## 3. Balanced Intent Distribution (100 Records)

The expansion guarantees proportional representation across all **9 canonical intents**, eliminating the dry-run gap where `savings_question` had 0 examples:

| Intent | Current (Dry Run) | Expansion Additions | Final Batch Target | Routes to ConsultantEngine? |
|:---|:---:|:---:|:---:|:---:|
| `financial_consultation` | 9 | +11 | **20** | YES |
| `budget_analysis` | 3 | +11 | **14** | YES |
| `debt_management` | 3 | +11 | **14** | YES |
| `cashflow_question` | 1 | +9 | **10** | YES |
| `savings_question` | 0 | +10 | **10** | YES |
| `financial_goal` | 1 | +9 | **10** | YES |
| `financial_education` | 1 | +5 | **6** | NO |
| `out_of_scope_investment` | 2 | +6 | **8** | NO |
| `out_of_scope_loan` | 2 | +6 | **8** | NO |
| **TOTAL** | **22** | **+78** | **100** | — |

---

## 4. Slot Balance & Coverage Requirements

The quality audit identified that `spending_habit` had 0% non-null coverage and `marital_status: "Single"` was unrepresented. The expansion enforces explicit representation floors:

| Slot Key | Valid Non-Null Values | Expansion Target Floor | Rationale |
|:---|:---|:---:|:---|
| `monthly_income` | Non-negative float | ≥ 55% non-null | Balanced income statements vs. missing/cadence edge-cases |
| `monthly_expense` | Non-negative float | ≥ 65% non-null | Balanced expense statements vs. unknown expense queries |
| `employment_status` | `"employed"`, `"not employed"` | ≥ 50% non-null | Ensure robust representation of both active employment and unemployment |
| `debt_status` | `"debt"`, `"no debt"` | ≥ 35% non-null | Explicit presence vs. explicit absence; unmentioned remains `null` |
| `spending_habit` | `"average spend"`, `"big spend"` | **≥ 15% non-null** | **New**: Discretionary spending tiers must be actively learned |
| `goal_cost` | Non-negative float | ≥ 12% non-null | Savings goals and capital accumulation targets |
| `marital_status` | `"Single"`, `"Married"` | **≥ 15% non-null** | **New**: Balanced representation of single individuals and married couples |

---

## 5. Required Edge Cases & Semantic Invariants

Controlled Expansion Batch 1 must explicitly include the following required edge cases:

### 5.1 Non-Monthly Cadence Ambiguity (Cadence Invariant)
* **Rule**: Never convert annual salaries ($/year), hourly wages ($/hour), or weekly pay ($/week) into monthly amounts.
* **Target**: At least 8 examples.
* **Required Behavior**: `monthly_income: null`, metadata: `{"ambiguity_type": "non_monthly_cadence"}`.

### 5.2 Range and Overtime Uncertainty (Range Ambiguity)
* **Rule**: Sentences with uncertainty ("between 2000 and 2500") cannot produce a single deterministic value.
* **Target**: At least 4 examples.
* **Required Behavior**: `monthly_income: null`, metadata: `{"ambiguity_type": "range_ambiguity"}`.

### 5.3 Third-Party Financial Figures (Entity Isolation)
* **Rule**: Financial amounts declared for spouses, siblings, parents, or roommates must not be extracted as the user's personal financial slots.
* **Target**: At least 6 examples.
* **Required Behavior**: Non-user income isolated; user slot set to `null` or user's own stated amount only.

### 5.4 Explicit Zero vs. Null (Null Invariant)
* **Rule**: `Unknown != 0.0`. Omission of information results in `null`. Explicit declaration ("0 income", "no debt") results in `0.0` or `"no debt"`.
* **Target**: At least 6 explicit zero examples across income, expenses, and debt.

### 5.5 Out-of-Scope Advisory Refusals
* **Rule**: Non-advisory queries (stock recommendations, crypto speculation, forex leverage, loan underwriting, mortgage approvals) must be classified into `out_of_scope_investment` or `out_of_scope_loan`.
* **Target**: Exactly 16 out-of-scope examples (8 investment + 8 loan).
* **Required Behavior**: All 7 slots `null`, `expected_rule_id: null`.

---

## 6. Deduplication & Leakage Prevention Rules

To prevent trivial duplicates and maintain semantic quality:
1. **Exact String Match Filter**: Automatically reject any candidate sentence that exactly matches an existing sentence.
2. **Normalized Hash Comparison**: Strip punctuation, convert to lowercase, collapse whitespace, and hash. Duplicates are immediately discarded.
3. **Template Grouping Integrity**: Automated check before dataset approval verifying that no `template_id` has examples in more than one partition (`train`, `val`, `test`).

---

## 7. Quality Assurance & Verification Pipeline

Every record in the 100-example expanded dataset must pass three automated gates before approval:
1. **Gate 1 — Schema Validation**: Validated against `datasets/financial_nlu/schemas/nlu_schema_v1.json`.
2. **Gate 2 — Span Verification**:
   - `input_text[start:end] == raw_text` for every span.
   - No spans pointing to third-party financial numbers.
3. **Gate 3 — Deterministic Engine Alignment**:
   - For all routable records with complete income and expenses, execute:
     $$\text{ConsultantInputValidator} \longrightarrow \text{ConsultantMetrics} \longrightarrow \text{ConsultantEngine}$$
   - The computed rule must exactly match `expected_rule_id`.
   - For non-routable or incomplete records, `expected_rule_id` must be strictly `null`.

---

## 8. Safety & Scope Guardrails

* **Zero Model Training**: No model training will occur during expansion authoring.
* **Zero Model Creation**: No weights, checkpoints, or LoRA adapters.
* **Model Name**: Remains `USER WILL DEFINE LATER`.
* **Language**: Strictly English only (`en`).
* **Database & Engine**: Production database and `ConsultantEngine` remain completely untouched.
