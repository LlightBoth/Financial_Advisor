"""
Financial Consultant Fact & Rule Engine (Step 7E).

Deterministic, transparent, and explainable advisory rule evaluation based on the approved
Step 7D Personal Financial Consultant Knowledge Model.

Key Architectural Guarantees:
1. Purely Advisory: No loan underwriting, credit scores, mortgage qualification, or product advice.
2. Fact Values Matter: Conditions evaluate actual boolean and numeric metric values, not tag existence.
3. Decoupled Certainty: Certainty represents Knowledge Grounding Strength metadata (0.50-1.00)
   and is NEVER used as an arithmetic threshold, filter, or tie-breaker.
4. Deterministic Priority: Rule conflicts are resolved strictly by Priority (100 -> 20),
   then specificity, then deterministic rule identifier.
5. Zero eval(): All predicates are parsed through a safe, deterministic comparator.
6. Bilingual: Full English and Khmer support for conclusions and advice.
"""

from typing import Dict, Any, List, Optional, Tuple
from app.services.consultant_metrics import calculate_metrics

# Step 7F: Canonical Knowledge Base Identifiers
CANONICAL_KB_VERSION = "financial-kb-v1.0"

CANONICAL_RULE_IDS = frozenset([
    "DEFICIT_WITH_DEBT",
    "DEFICIT_NO_DEBT",
    "INCOME_ZERO_UNEMPLOYED",
    "BREAK_EVEN_ZERO_MARGIN",
    "TIGHT_MARGIN_HIGH_EXPENSE",
    "SURPLUS_WITH_DEBT_SERVICING",
    "BALANCED_BUDGET_BUFFER_BUILDING",
    "FLEXIBLE_BUDGET_CAPITAL_GROWTH",
])


class ConsultantAdviceResult:
    """
    Standardized advisory output object compatible with templates and history services.
    """
    def __init__(
        self,
        rule_id: str,
        name: str,
        category: str,
        priority: int,
        certainty: float,
        conclusion_en: str,
        conclusion_km: str,
        advice_en: Any,
        advice_km: Any,
        knowledge_refs: List[str],
        active_lang: str = "en",
        db_id: Optional[int] = None,
        kb_version: str = CANONICAL_KB_VERSION,
        selection_reason: Optional[str] = None
    ):
        self.id = db_id
        self.rule_id = rule_id
        self.name = name
        self.category = category
        self.priority = priority
        self.certainty = certainty
        self.conclusion_en = conclusion_en
        self.conclusion_km = conclusion_km
        self.advice_en = advice_en
        self.advice_km = advice_km
        self.knowledge_refs = knowledge_refs or []
        self.active_lang = active_lang
        self.kb_version = kb_version
        self.selection_reason = selection_reason

    @property
    def conclusion(self) -> str:
        """Returns the conclusion text in the active language."""
        if self.active_lang == "km" and self.conclusion_km:
            return self.conclusion_km
        return self.conclusion_en or self.conclusion_km or "No conclusion"

    @property
    def advice(self) -> str:
        """Returns the advice text formatted for UI display in the active language."""
        content = self.advice_km if (self.active_lang == "km" and self.advice_km) else self.advice_en
        if isinstance(content, list):
            return " ".join(content)
        return str(content or "No advice available")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "name": self.name,
            "category": self.category,
            "priority": self.priority,
            "certainty": self.certainty,
            "conclusion": self.conclusion,
            "advice": self.advice,
            "conclusion_en": self.conclusion_en,
            "conclusion_km": self.conclusion_km,
            "advice_en": self.advice_en,
            "advice_km": self.advice_km,
            "knowledge_refs": self.knowledge_refs,
            "kb_version": self.kb_version,
            "selection_reason": self.selection_reason,
        }

    def __repr__(self) -> str:
        return f"<ConsultantAdviceResult {self.rule_id} (Priority: {self.priority}, Certainty: {self.certainty})>"


class ConsultantEngine:
    """
    Core Deterministic Expert System Engine for Personal Financial Consultation.
    """

    @staticmethod
    def derive_facts(metrics: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates the Step 7D deterministic Fact namespace from calculated metrics and raw inputs.
        """
        income = metrics.get("monthly_income", 0.0)
        net_cashflow = metrics.get("net_cashflow", 0.0)
        expense_ratio = metrics.get("expense_ratio")
        goal_cost = metrics.get("goal_cost", 0.0)

        # Normalize raw categorical inputs
        emp_raw = str(user_data.get("employment_status") or user_data.get("is_employed") or "not employed").strip().lower()
        if emp_raw in ("true", "1", "employed", "yes"):
            employment_status = "employed"
        else:
            employment_status = "not employed"

        debt_raw = str(user_data.get("debt_status") or user_data.get("is_debt") or "no debt").strip().lower()
        if debt_raw in ("true", "1", "debt", "yes"):
            debt_present = True
            debt_status = "debt"
        else:
            debt_present = False
            debt_status = "no debt"

        spend_raw = str(user_data.get("spending_habit") or user_data.get("is_spending") or "average spend").strip().lower()
        if spend_raw in ("true", "1", "big spend", "high"):
            spending_habit = "big spend"
        else:
            spending_habit = "average spend"

        marital_status = str(user_data.get("martial_status") or user_data.get("marital_status") or "Single").strip()

        # Step 7D Fact Taxonomy
        facts = {
            # Inflow Facts
            "income_positive": bool(income > 0.0),
            "income_zero": bool(income == 0.0),
            "employment_status": employment_status,

            # Cash Flow Facts
            "cashflow_deficit": bool(net_cashflow < 0.0),
            "cashflow_balanced": bool(net_cashflow == 0.0),
            "cashflow_surplus": bool(net_cashflow > 0.0),

            # Expenditure Facts
            "expense_tier_tight": bool(expense_ratio is not None and expense_ratio >= 0.80 and net_cashflow > 0.0),
            "expense_tier_balanced": bool(expense_ratio is not None and 0.50 <= expense_ratio < 0.80),
            "expense_tier_flexible": bool(expense_ratio is not None and expense_ratio < 0.50 and net_cashflow > 0.0),
            "spending_habit": spending_habit,

            # Liability Facts
            "debt_present": debt_present,
            "debt_free": not debt_present,
            "debt_status": debt_status,

            # Milestone Facts
            "goal_cost_present": bool(goal_cost > 0.0),
            "marital_status": marital_status,

            # Numeric Metric Bindings (for quantitative condition checks)
            "monthly_income": income,
            "monthly_expense": metrics.get("monthly_expense", 0.0),
            "net_cashflow": net_cashflow,
            "expense_ratio": expense_ratio,
            "surplus_ratio": metrics.get("surplus_ratio"),
            "goal_cost": goal_cost,
            "natural_goal_months": metrics.get("natural_goal_months"),
        }

        return facts

    @staticmethod
    def evaluate_condition(condition: Dict[str, Any], fact_namespace: Dict[str, Any]) -> bool:
        """
        Evaluates a single predicate condition against the runtime fact namespace.
        NEVER uses eval(). Supports both symbolic and text operators safely.
        """
        field = condition.get("field") or condition.get("fact")
        operator = str(condition.get("operator", "==")).strip().lower()

        # Determine target value: literal "value" or dynamic "value_fact"
        if "value_fact" in condition and condition["value_fact"]:
            target_value = fact_namespace.get(condition["value_fact"])
        else:
            target_value = condition.get("value")

        actual_value = fact_namespace.get(field)

        # Equal
        if operator in ("==", "eq", "equals", "equal"):
            return actual_value == target_value

        # Not Equal
        if operator in ("!=", "ne", "not_equals", "not_equal"):
            return actual_value != target_value

        # Comparison operators require both values to be numeric non-None
        if actual_value is None or target_value is None:
            return False

        try:
            act_num = float(actual_value)
            tgt_num = float(target_value)
        except (ValueError, TypeError):
            # Non-numeric comparison fallback
            act_num = None
            tgt_num = None

        if operator in ("<", "lt", "less_than"):
            if act_num is not None and tgt_num is not None:
                return act_num < tgt_num
            return actual_value < target_value

        if operator in ("<=", "lte", "less_than_or_equal", "less_than_or_equals"):
            if act_num is not None and tgt_num is not None:
                return act_num <= tgt_num
            return actual_value <= target_value

        if operator in (">", "gt", "greater_than"):
            if act_num is not None and tgt_num is not None:
                return act_num > tgt_num
            return actual_value > target_value

        if operator in (">=", "gte", "greater_than_or_equal", "greater_than_or_equals"):
            if act_num is not None and tgt_num is not None:
                return act_num >= tgt_num
            return actual_value >= target_value

        if operator in ("in", "contains"):
            if isinstance(target_value, (list, tuple, set)):
                return actual_value in target_value
            return str(actual_value) in str(target_value)

        if operator in ("not in", "not_in"):
            if isinstance(target_value, (list, tuple, set)):
                return actual_value not in target_value
            return str(actual_value) not in str(target_value)

        return False

    @staticmethod
    def rule_matches(rule_conditions: List[Dict[str, Any]], match_operator: str, fact_namespace: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Evaluates all conditions of a rule against the runtime fact namespace.
        Returns (is_match, evaluation_details).
        """
        if not rule_conditions:
            return False, []

        eval_details = []
        mode = match_operator.upper() if match_operator else "ALL"

        for cond in rule_conditions:
            cond_res = ConsultantEngine.evaluate_condition(cond, fact_namespace)
            field = cond.get("field") or cond.get("fact")
            operator = cond.get("operator", "==")
            expected = cond.get("value") if "value" in cond else cond.get("value_fact")
            actual = fact_namespace.get(field)
            eval_details.append({
                "fact_key": field,
                "field": field,
                "operator": operator,
                "expected_value": expected,
                "expected": expected,
                "actual_value": actual,
                "actual": actual,
                "matched": cond_res,
                "passed": cond_res
            })

        if mode == "ANY":
            matched = any(d["matched"] for d in eval_details)
        else:  # ALL
            matched = all(d["matched"] for d in eval_details)

        return matched, eval_details

    @staticmethod
    def select_rule(rules: List[Any], fact_namespace: Dict[str, Any], lang: str = "en") -> Tuple[Optional[ConsultantAdviceResult], List[Dict[str, Any]]]:
        """
        Deterministically selects the single best consultant rule.

        Resolution Hierarchy:
        1. Condition match (must satisfy match_operator)
        2. Priority (Descending: 100 -> 20)
        3. Specificity (Number of conditions, Descending)
        4. Deterministic Identifier (rule_id ASC, then id ASC)

        Explicit Invariant:
        Rule.certainty is NEVER used as a tie-breaker or filter.
        """
        matched_candidates = []
        rule_evaluations = []

        for r in rules:
            # Extract basic identifiers
            if isinstance(r, dict):
                r_id = r.get("id")
                rule_key = r.get("rule_id") or f"RULE_{r_id}"
                r_kb = r.get("kb_version")
                is_active = r.get("is_active", True)
            else:
                r_id = getattr(r, "id", None)
                rule_key = getattr(r, "rule_id", None) or f"RULE_{r_id}"
                r_kb = getattr(r, "kb_version", None)
                is_active = getattr(r, "is_active", True)

            # 1. Active state guard
            if not is_active:
                continue

            # 2. Strict Canonical Knowledge Base Membership Guard (Step 7F)
            if rule_key not in CANONICAL_RULE_IDS:
                continue
            if r_kb != CANONICAL_KB_VERSION:
                continue

            # Extract condition definitions (from conditions_json, conditions list, or dict)
            if isinstance(r, dict):
                name = r.get("name", "Financial Rule")
                category = r.get("category", "ADVISORY")
                priority = int(r.get("priority", 50))
                certainty = float(r.get("certainty", 0.85))
                conditions = r.get("conditions", [])
                match_op = r.get("match_operator", "ALL")
                conclusion_en = r.get("conclusion_en") or r.get("conclusion", "")
                conclusion_km = r.get("conclusion_km") or conclusion_en
                advice_en = r.get("advice_en") or r.get("advice", "")
                advice_km = r.get("advice_km") or advice_en
                knowledge_refs = r.get("knowledge_refs", [])
            else:
                name = getattr(r, "name", "Financial Rule")
                category = getattr(r, "category", "ADVISORY")
                priority = getattr(r, "priority", 50)
                certainty = getattr(r, "certainty", 0.85)
                match_op = getattr(r, "match_operator", "ALL")
                knowledge_refs = getattr(r, "knowledge_refs", []) or []

                # Conditions can come from conditions_json or related RuleCondition records
                if hasattr(r, "conditions_json") and r.conditions_json:
                    conditions = r.conditions_json
                elif hasattr(r, "conditions") and r.conditions:
                    conditions = []
                    for c in r.conditions:
                        conditions.append({
                            "field": getattr(c, "fact", None),
                            "operator": getattr(c, "operator", "=="),
                            "value": getattr(c, "value", None),
                            "value_fact": getattr(c, "value_fact", None)
                        })
                else:
                    conditions = []

                conclusion_en = getattr(r, "conclusion_en", None) or getattr(r, "conclusion", "")
                conclusion_km = getattr(r, "conclusion_km", None) or conclusion_en
                advice_en = getattr(r, "advice_en", None) or getattr(r, "advice", "")
                advice_km = getattr(r, "advice_km", None) or advice_en

            # Evaluate rule
            is_match, cond_trace = ConsultantEngine.rule_matches(conditions, match_op, fact_namespace)

            eval_entry = {
                "rule_id": rule_key,
                "name": name,
                "category": category,
                "priority": priority,
                "specificity": len(conditions),
                "certainty": certainty,
                "matched": is_match,
                "condition_results": cond_trace,
                "conditions": cond_trace,
                "failure_reason": None,
            }
            rule_evaluations.append(eval_entry)

            if is_match:
                candidate = ConsultantAdviceResult(
                    rule_id=rule_key,
                    name=name,
                    category=category,
                    priority=priority,
                    certainty=certainty,
                    conclusion_en=conclusion_en,
                    conclusion_km=conclusion_km,
                    advice_en=advice_en,
                    advice_km=advice_km,
                    knowledge_refs=knowledge_refs,
                    active_lang=lang,
                    db_id=r_id,
                    kb_version=CANONICAL_KB_VERSION
                )
                # Store sorting keys: (priority, condition_count, rule_key, db_id, candidate)
                matched_candidates.append((priority, len(conditions), str(rule_key), r_id or 0, candidate))

        # Explain rejected rules that failed conditions
        for eval_entry in rule_evaluations:
            if not eval_entry["matched"]:
                failed_conds = [c for c in eval_entry["condition_results"] if not c["matched"]]
                failed_strs = [
                    f"{c['fact_key']} {c['operator']} {c['expected_value']} was false (actual: {c['actual_value']})"
                    for c in failed_conds
                ]
                if len(failed_strs) == 1:
                    eval_entry["failure_reason"] = f"Condition failed: {failed_strs[0]}"
                elif len(failed_strs) > 1:
                    eval_entry["failure_reason"] = f"Conditions failed: {', '.join(failed_strs)}"
                else:
                    eval_entry["failure_reason"] = "Rule conditions did not match"

        if not matched_candidates:
            return None, rule_evaluations

        # Deterministic sort:
        # 1. priority DESC
        # 2. condition count DESC
        # 3. rule_id ASC (for stable deterministic secondary order)
        # 4. db_id ASC
        matched_candidates.sort(key=lambda x: (-x[0], -x[1], x[2], x[3]))
        winning_tuple = matched_candidates[0]
        winning_priority = winning_tuple[0]
        winning_specificity = winning_tuple[1]
        winning_rule_id = winning_tuple[2]
        winning_candidate = winning_tuple[4]

        # Explain matched rules that were superseded by higher priority or specificity
        for eval_entry in rule_evaluations:
            if eval_entry["matched"]:
                if eval_entry["rule_id"] == winning_rule_id:
                    eval_entry["failure_reason"] = None
                else:
                    r_priority = eval_entry["priority"]
                    r_spec = eval_entry["specificity"]
                    if winning_priority > r_priority:
                        eval_entry["failure_reason"] = (
                            f"Matched conditions, but superseded by higher-priority rule "
                            f"{winning_rule_id} (priority {winning_priority} > {r_priority})"
                        )
                    elif winning_specificity > r_spec:
                        eval_entry["failure_reason"] = (
                            f"Matched conditions with equal priority ({r_priority}), but superseded by "
                            f"{winning_rule_id} with higher specificity ({winning_specificity} > {r_spec} conditions)"
                        )
                    else:
                        eval_entry["failure_reason"] = (
                            f"Matched conditions with equal priority ({r_priority}) and specificity ({r_spec}), "
                            f"but superseded by {winning_rule_id} by deterministic rule ID ordering"
                        )

        # Build factual deterministic selection_reason
        other_matching_ids = [m[2] for m in matched_candidates if m[2] != winning_rule_id]
        if not other_matching_ids:
            selection_reason = (
                f"Matched canonical rule. Priority = {winning_priority}. "
                f"Specificity = {winning_specificity} conditions. "
                "No higher-priority matching canonical rule existed."
            )
        else:
            lower_priority_ids = [m[2] for m in matched_candidates[1:] if m[0] < winning_priority]
            lower_spec_ids = [m[2] for m in matched_candidates[1:] if m[0] == winning_priority and m[1] < winning_specificity]
            if lower_priority_ids:
                selection_reason = (
                    f"Matched canonical rule. Priority = {winning_priority}. "
                    f"Specificity = {winning_specificity} conditions. "
                    f"Higher priority than other matching rule(s): {', '.join(other_matching_ids)}."
                )
            elif lower_spec_ids:
                selection_reason = (
                    f"Matched canonical rule. Priority = {winning_priority}. "
                    f"Specificity = {winning_specificity} conditions. "
                    f"Higher specificity than equal-priority matching rule(s): {', '.join(lower_spec_ids)}."
                )
            else:
                selection_reason = (
                    f"Matched canonical rule. Priority = {winning_priority}. "
                    f"Specificity = {winning_specificity} conditions. "
                    f"Selected over {', '.join(other_matching_ids)} by deterministic rule identifier ordering."
                )

        winning_candidate.selection_reason = selection_reason
        return winning_candidate, rule_evaluations

    @staticmethod
    def evaluate(user_data: Dict[str, Any], rules: Optional[List[Any]] = None, lang: str = "en") -> Dict[str, Any]:
        """
        Orchestrates full expert system consultation pipeline:
        Inputs -> Metrics -> Facts -> Evaluated Rules -> Selected Rule -> Bilingual Result -> Decision Trace.
        """
        # Step 1: Deterministic Metrics Calculation
        income = user_data.get("income") or user_data.get("monthly_income") or 0.0
        expense = user_data.get("expense") or user_data.get("monthly_expense") or 0.0
        goal_cost = user_data.get("goal_cost", 0.0)

        metrics = calculate_metrics(income, expense, goal_cost)

        # Step 2: Deterministic Facts Derivation
        facts = ConsultantEngine.derive_facts(metrics, user_data)

        # Step 3: Load rules if not provided
        # Production query strictly filters active canonical rules with canonical kb_version
        if rules is None:
            try:
                from app.models.rule import Rule
                rules = Rule.query.filter(
                    Rule.is_active.is_(True),
                    Rule.kb_version == CANONICAL_KB_VERSION,
                    Rule.rule_id.in_(CANONICAL_RULE_IDS)
                ).all()
            except Exception:
                rules = []

        # Step 4: Rule Evaluation and Deterministic Priority Selection
        selected_advice, rule_evaluations = ConsultantEngine.select_rule(rules, facts, lang=lang)

        # Fallback if no rules exist in database
        if selected_advice is None:
            selected_advice = ConsultantEngine._create_default_fallback(facts, metrics, lang)
            selection_reason = (
                "No canonical rule conditions matched fact namespace. "
                "Default deterministic financial triage fallback activated."
            )
            selected_advice.selection_reason = selection_reason
        else:
            selection_reason = getattr(selected_advice, "selection_reason", "Matched canonical rule.")

        def _format_advice(adv: Any) -> str:
            if isinstance(adv, list):
                return " ".join(str(x) for x in adv)
            return str(adv or "")

        candidate_rule_ids = [r["rule_id"] for r in rule_evaluations]

        input_summary = {
            "income": metrics["monthly_income"],
            "expense": metrics["monthly_expense"],
            "goal_cost": metrics["goal_cost"],
            "employment_status": facts["employment_status"],
            "debt_status": facts["debt_status"],
            "spending_habit": facts["spending_habit"],
            "marital_status": facts["marital_status"],
        }

        decision_trace = {
            "knowledge_base_version": CANONICAL_KB_VERSION,
            "input_summary": input_summary,
            "metrics": metrics,
            "derived_facts": facts,
            "candidate_rules": candidate_rule_ids,
            "rule_evaluations": rule_evaluations,
            "selected_rule": selected_advice.rule_id if selected_advice else None,
            "selection_reason": selection_reason,
            "conclusion_en": selected_advice.conclusion_en or "",
            "conclusion_km": selected_advice.conclusion_km or "",
            "advice_en": _format_advice(selected_advice.advice_en),
            "advice_km": _format_advice(selected_advice.advice_km),
        }

        return {
            "inputs": input_summary,
            "metrics": metrics,
            "facts": facts,
            "selected_advice": selected_advice,
            "audit_trace": rule_evaluations,
            "decision_trace": decision_trace,
            "kb_version": CANONICAL_KB_VERSION,
        }

    @staticmethod
    def explain(user_data: Dict[str, Any], rules: Optional[List[Any]] = None, lang: str = "en") -> Dict[str, Any]:
        """
        Public explainability API: returns the complete structured decision trace.
        """
        eval_result = ConsultantEngine.evaluate(user_data, rules=rules, lang=lang)
        return eval_result["decision_trace"]

    @staticmethod
    def _create_default_fallback(facts: Dict[str, Any], metrics: Dict[str, Any], lang: str) -> ConsultantAdviceResult:
        """
        Guaranteed fallback when database rules are empty or missing.
        """
        net = metrics.get("net_cashflow", 0.0)
        has_debt = facts.get("debt_present", False)

        if net < 0.0:
            return ConsultantAdviceResult(
                rule_id="FALLBACK_DEFICIT",
                name="Operating Cashflow Deficit",
                category="CASHFLOW_DEFICIT_MANAGEMENT",
                priority=100,
                certainty=1.00,
                conclusion_en="Operating Cashflow Deficit",
                conclusion_km="ឱនភាពលំហូរសាច់ប្រាក់ប្រតិបត្តិការ",
                advice_en="Monthly expenses exceed income. Review recurring living expenditures to restore cash flow to a positive balance before committing to new financial goals.",
                advice_km="ការចំណាយប្រចាំខែលើសពីប្រាក់ចំណូល។ ពិនិត្យឡើងវិញនូវការចំណាយប្រចាំថ្ងៃ ដើម្បីស្តារលំហូរសាច់ប្រាក់ឱ្យមានតុល្យភាពវិជ្ជមាន មុនពេលប្តេជ្ញាចិត្តចំពោះគោលដៅហិរញ្ញវត្ថុថ្មីៗ។",
                knowledge_refs=["K001", "K002"],
                active_lang=lang
            )
        elif net == 0.0:
            return ConsultantAdviceResult(
                rule_id="FALLBACK_BREAK_EVEN",
                name="Break-Even Cashflow with Zero Operating Margin",
                category="OPERATING_BREAK_EVEN",
                priority=80,
                certainty=1.00,
                conclusion_en="Break-Even Cashflow with Zero Operating Margin",
                conclusion_km="លំហូរសាច់ប្រាក់ស្មើចំណាយ (គ្មានរឹមសល់)",
                advice_en="Exactly 100% of income is consumed by expenses. While not in deficit, any unexpected cost poses a borrowing risk. Seek minor spending adjustments to establish an initial cash buffer.",
                advice_km="ប្រាក់ចំណូល ១០០% ត្រូវបានចំណាយអស់។ ទោះបីជាមិនមានឱនភាពក៏ដោយ ការចំណាយមិនរំពឹងទុកណាមួយអាចបង្កហានិភ័យនៃការខ្ចីបុល។ សូមកែសម្រួលការចំណាយបន្តិចបន្តួចដើម្បីបង្កើតសតិបណ្ដោះអាសន្ន។",
                knowledge_refs=["K001", "K003"],
                active_lang=lang
            )
        else:
            if has_debt:
                return ConsultantAdviceResult(
                    rule_id="FALLBACK_SURPLUS_DEBT",
                    name="Positive Cashflow with Active Debt Obligations",
                    category="DEBT_SERVICING_ACCELERATION",
                    priority=60,
                    certainty=0.85,
                    conclusion_en="Positive Cashflow with Active Debt Obligations",
                    conclusion_km="លំហូរសាច់ប្រាក់វិជ្ជមាន ជាមួយកាតព្វកិច្ចបំណុលសកម្ម",
                    advice_en="A sustainable cash flow surplus exists. Consider dedicating a significant portion of this surplus toward structured debt payoff.",
                    advice_km="មានអតិរេកលំហូរសាច់ប្រាក់ប្រកបដោយនិរន្តរភាព។ ពិចារណាបែងចែកផ្នែកធំនៃអតិរេកនេះឆ្ពោះទៅរកការទូទាត់បំណុលដែលមានរចនាសម្ព័ន្ធ។",
                    knowledge_refs=["K004", "K008", "K014"],
                    active_lang=lang
                )
            else:
                return ConsultantAdviceResult(
                    rule_id="FALLBACK_SURPLUS_STABLE",
                    name="Balanced Operating Budget",
                    category="STABLE_BUFFER_BUILDING",
                    priority=40,
                    certainty=0.85,
                    conclusion_en="Balanced Operating Budget",
                    conclusion_km="ថវិកាប្រតិបត្តិការមានតុល្យភាព",
                    advice_en="Your living expenses are well-balanced. Prioritize building 3 to 6 months of essential living expenses as an emergency reserve.",
                    advice_km="ការចំណាយប្រចាំថ្ងៃរបស់អ្នកមានតុល្យភាពល្អ។ សូមផ្តល់អាទិភាពដល់ការសន្សំប្រាក់សម្រាប់ ៣ ទៅ ៦ ខែនៃការចំណាយចាំបាច់។",
                    knowledge_refs=["K004", "K008", "K013"],
                    active_lang=lang
                )
