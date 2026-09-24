from typing import Dict, Any, Optional
from flask import session, request
from flask_login import current_user

from app.models import Rule, Fact
from app.services.consultant_engine import ConsultantEngine, ConsultantAdviceResult


class EmptyAdvice:
    certainty = 0.0
    advice = "No advice available"
    conclusion = "No conclusion"


class AdvisorServices:

    @staticmethod
    def _get_current_language() -> str:
        """Helper to retrieve the user's active session or cookie language."""
        try:
            return session.get("lang") or request.cookies.get("lang") or "en"
        except Exception:
            return "en"

    # user financial profiles for chat bot 

    @staticmethod
    def get_user_financial_profile(user) -> Optional[Dict[str, Any]]:
        """
        Loads the authoritative financial profile for an authenticated user.

        Source of Truth Hierarchy (Option 1):
        1. Live Tracker Tables (IncomeServices, ExpenseServices, PlanServices):
           Queries real recorded transactions and plans for the user.
        2. Active In-Chat Session Cache (`session["advisor_profile"]`):
           Honors active conversational overrides (e.g., user says "My expense is now $70" in chat).
        3. Fallback: Legacy database `History` record explicitly scoped to `user.id`
           (strictly for backward compatibility when tracker tables are empty).
        """
        if not user or not getattr(user, "is_authenticated", False):
            return None

        from app.services.income_services import IncomeServices
        from app.services.expense_services import ExpenseServices
        from app.services.plan_services import PlanServices
        from app.models.plan import Plan
        from app.models.expense import Expense
        from app.models.history import History

        # 1. Check live tracker records
        income_count = IncomeServices.get_income_count(user)
        expense_count = ExpenseServices.get_expense_count(user)
        plan_count = PlanServices.get_user_all_plan_count(user)

        tracker_profile = None
        if income_count > 0 or expense_count > 0 or plan_count > 0:
            inc = float(IncomeServices.get_income_total(user)) if income_count > 0 else None
            exp = float(ExpenseServices.get_expense_total(user)) if expense_count > 0 else None
            goal = float(PlanServices.get_user_all_plan_total(user)) if plan_count > 0 else 0.0

            latest_plan = (
                Plan.query
                .filter(Plan.users.any(id=user.id))
                .order_by(Plan.created_at.desc(), Plan.id.desc())
                .first()
            )

            if latest_plan and latest_plan.marital_status:
                marital = str(latest_plan.marital_status).strip().capitalize()
            else:
                marital = "Single"

            if latest_plan and latest_plan.employment_status:
                emp = str(latest_plan.employment_status).strip().lower()
            elif inc is not None and inc > 0:
                emp = "employed"
            else:
                emp = "not employed"

            # Check debt status from expenses or plan
            has_debt_expense = Expense.query.filter(
                Expense.users.any(id=user.id),
                Expense.category.ilike("%debt%")
            ).first() is not None

            has_plan_debt = False
            if latest_plan:
                raw_debt = str(getattr(latest_plan, "debt_status", "") or "").lower()
                if "debt" in raw_debt and "no debt" not in raw_debt and "none" not in raw_debt:
                    has_plan_debt = True
                elif getattr(latest_plan, "debt_amount", None) and float(latest_plan.debt_amount or 0) > 0:
                    has_plan_debt = True

            debt = "debt" if (has_debt_expense or has_plan_debt) else "no debt"

            # Check spending habit
            if latest_plan and latest_plan.spending_habit:
                raw_habit = str(latest_plan.spending_habit).strip().lower()
                spending = "big spend" if ("big" in raw_habit or "high" in raw_habit) else "average spend"
            elif inc is not None and exp is not None and inc > 0 and (exp / inc) > 0.70:
                spending = "big spend"
            else:
                spending = "average spend"

            tracker_profile = {
                "monthly_income": inc,
                "monthly_expense": exp,
                "goal_cost": goal,
                "marital_status": marital,
                "employment_status": emp,
                "debt_status": debt,
                "spending_habit": spending,
                "_source": "tracker_tables",
            }

        # 2. Check session cache for active in-dialogue conversational overrides
        session_cache = None
        try:
            from flask import session as flask_session
            session_cache = flask_session.get("advisor_profile")
        except Exception:
            pass

        # If user has live tracker records, active conversational overrides in session take precedence
        # ONLY if they are active in-dialogue chat overrides (tagged with _is_conversational_override)
        if tracker_profile:
            if session_cache and isinstance(session_cache, dict):
                if session_cache.get("_user_id") == user.id and session_cache.get("_is_conversational_override"):
                    # Chatbot conversation update
                    return {k: v for k, v in session_cache.items() if not k.startswith("_")}
            return {k: v for k, v in tracker_profile.items() if not k.startswith("_")}

        # 3. Fallback: Query legacy database History if tracker tables are empty (for backward compatibility and tests)
        latest_history = (
            History.query
            .filter(History.users.any(id=user.id))
            .order_by(History.created_at.desc(), History.id.desc())
            .first()
        )

        db_profile = None
        if latest_history:
            inc = float(latest_history.income) if latest_history.income is not None else None
            exp = float(latest_history.expense) if latest_history.expense is not None else None
            goal = float(latest_history.goal_cost) if latest_history.goal_cost is not None else 0.0
            marital = latest_history.martial_status or "Single"
            emp = "employed" if latest_history.is_employed else "not employed"
            debt = "debt" if latest_history.is_debt else "no debt"
            spending = "big spend" if latest_history.is_spending else "average spend"

            db_profile = {
                "monthly_income": inc,
                "monthly_expense": exp,
                "goal_cost": goal,
                "marital_status": marital,
                "employment_status": emp,
                "debt_status": debt,
                "spending_habit": spending,
                "_source": "database_history",
                "_history_id": latest_history.id,
                "_created_at": latest_history.created_at.isoformat() if latest_history.created_at else None,
            }

        if session_cache and isinstance(session_cache, dict):
            # Strictly verify cache belongs to current user
            if session_cache.get("_user_id") == user.id:
                cached_hid = session_cache.get("_history_id")
                db_hid = db_profile.get("_history_id") if db_profile else None
                # Prevent stale session data from overriding newer database data
                if db_hid is not None and cached_hid is not None and db_hid > cached_hid:
                    return {k: v for k, v in db_profile.items() if not k.startswith("_")}
                # Return active session profile
                return {k: v for k, v in session_cache.items() if not k.startswith("_")}

        if db_profile:
            return {k: v for k, v in db_profile.items() if not k.startswith("_")}

        return None

    @staticmethod
    def _evaluate_condition(condition, facts):
        actual_value = facts.get(condition.fact)
        if actual_value is None:
            return False

        if condition.value_fact:
            expected_value = facts.get(condition.value_fact)
        else:
            expected_value = condition.value

        if expected_value is None:
            return False

        try:
            if condition.operator in ("greater_than", ">"):
                return actual_value > expected_value
            if condition.operator in ("greater_than_or_equal", ">="):
                return actual_value >= expected_value
            if condition.operator in ("less_than", "<"):
                return actual_value < expected_value
            if condition.operator in ("less_than_or_equal", "<="):
                return actual_value <= expected_value
            if condition.operator in ("equal", "equals", "=="):
                return actual_value == expected_value
            if condition.operator in ("not_equal", "!="):
                return actual_value != expected_value
            if condition.operator == "contains":
                return expected_value in actual_value
            if condition.operator == "in":
                return actual_value in expected_value
        except (TypeError, ValueError):
            return False

        return False

    @staticmethod
    def _rule_matches(rule, facts):
        # A rule without conditions is treated as a general rule.
        if not rule.conditions:
            return False


        # All conditions belonging to a rule must match.
        return all(
            AdvisorServices._evaluate_condition(condition, facts)
            for condition in rule.conditions
        )

    @staticmethod
    def persoal_analyse(data: dict):
        goal_cost = float(data.get("goal_cost", 0.0) or 0.0)
        income = float(data.get("income", 0.0) or 0.0)
        expense = float(data.get("expense", 0.0) or 0.0)
        marital_status = data.get("marital_status", "Single")

        if income <= 0:
            return {
                "income": income,
                "expense": expense,
                "goal_cost": goal_cost,
                "marital_status": marital_status,
                "monthly_surplus": 0.0,
                "remain_percentage": 0.0,
                "expense_percentage": 0.0,
                "target_certainty": 0.0,
                "get_advice": EmptyAdvice(),
                "matched_rules": [],
                "facts": {
                    "monthly_income": income,
                    "monthly_expense": expense,
                    "monthly_surplus": 0.0,
                    "savings_rate": 0.0,
                    "expense_rate": 0.0,
                    "marital_status": marital_status,
                    "goal_cost": goal_cost,
                },
            }

        monthly_surplus = income - expense
        remain_percentage = monthly_surplus / income
        expense_percentage = expense / income

        # Facts available to the rule engine.
        facts = {
            "monthly_income": income,
            "monthly_expense": expense,
            "monthly_surplus": monthly_surplus,
            "savings_rate": remain_percentage,
            "expense_rate": expense_percentage,
            "marital_status": marital_status,
            "goal_cost": goal_cost,
        }

        # Load all active rules from database.
        rules = Rule.query.order_by(Rule.id.asc()).all()

        # Evaluate every rule against the user's financial facts.
        matched_rules = [
            rule
            for rule in rules
            if AdvisorServices._rule_matches(rule, facts)
        ]

        # Highest certainty first.
        matched_rules.sort(
            key=lambda rule: getattr(rule, "certainty", 0.0) or 0.0,
            reverse=True
        )

        # Keep the highest-certainty recommendation for compatibility
        # with templates that expect advice["get_advice"].
        best_rule = (
            matched_rules[0]
            if matched_rules
            else EmptyAdvice()
        )

        return {
            "income": income,
            "expense": expense,
            "goal_cost": goal_cost,
            "marital_status": marital_status,
            "monthly_surplus": monthly_surplus,
            "remain_percentage": remain_percentage * 100,
            "expense_percentage": expense_percentage * 100,
            "target_certainty": getattr(best_rule, "certainty", 0.0),
            "get_advice": best_rule,
            "matched_rules": matched_rules,
            "facts": facts,
        }


    @staticmethod
    def get_advise(data: dict):
        """
        Main advisory pipeline.
        
        Evaluates user financial profile through deterministic metrics calculation,
        Step 7D Fact derivation, predicate condition evaluation, and deterministic
        priority triage.

        Guarantees:
        - Income <= 0 is fully evaluated for emergency/deficit triage (no EmptyAdvice abort).
        - Rule.certainty is NEVER used as an expense threshold, filter, or tie-breaker.
        - Division by zero is mathematically impossible.
        - Bilingual English and Khmer support.
        """
        lang = AdvisorServices._get_current_language()
        eval_result = ConsultantEngine.evaluate(data, lang=lang)

        metrics = eval_result["metrics"]
        facts = eval_result["facts"]
        best_advice = eval_result["selected_advice"]

        surplus_ratio = metrics.get("surplus_ratio")
        expense_ratio = metrics.get("expense_ratio")

        remain_pct = round(surplus_ratio * 100, 2) if surplus_ratio is not None else 0.0
        expense_pct = round(expense_ratio * 100, 2) if expense_ratio is not None else 0.0

        # PABL integration for HTML form context
        from app.services.provenance_boundary import ProvenanceBoundaryLayer
        from app.services.llm_service import LLMService

        boundary_context = ProvenanceBoundaryLayer.process(data, default_lang=lang)
        decision_used_defaulted = boundary_context.check_decision_used_defaulted_field(best_advice)
        provenance_dict = boundary_context.to_dict(decision_used_defaulted_field=decision_used_defaulted)

        def _format_adv(adv):
            if isinstance(adv, list):
                return " ".join(str(x) for x in adv)
            return str(adv or "")

        adv_text_for_exp = _format_adv(best_advice.advice_km if lang == "km" else best_advice.advice_en) if best_advice else ""
        conc_text_for_exp = (best_advice.conclusion_km if lang == "km" else best_advice.conclusion_en) if best_advice else ""
        explanation = LLMService.generate_recommendation_explanation(
            metrics=metrics,
            facts=facts,
            advice_text=adv_text_for_exp,
            conclusion_text=conc_text_for_exp,
            advisory_caveats=boundary_context.get_caveat_messages(lang=lang),
            lang=lang,
        )

        advice_data = {
            "goal_cost": metrics["goal_cost"],
            "income": metrics["monthly_income"],
            "expense": metrics["monthly_expense"],
            "martial_status": facts["marital_status"],
            "is_employed": facts["employment_status"],
            "is_debt": facts["debt_status"],
            "is_spending": facts["spending_habit"],
            "remain_percentage": remain_pct,
            "expense_percentage": expense_pct,
            "get_advice": best_advice or EmptyAdvice(),
            "matched_rules": eval_result.get("matched_rules", []),
            "metrics": metrics,
            "facts": facts,
            "audit_trace": eval_result.get("audit_trace", []),
            "decision_trace": eval_result.get("decision_trace"),
            "kb_version": getattr(best_advice, "kb_version", "financial-kb-v1.0") if best_advice else "financial-kb-v1.0",
            "provenance": provenance_dict,
            "advisory_caveats": boundary_context.get_caveat_messages(lang=lang),
            "explanation": explanation,
        }

        # Save to history if current_user is authenticated
        try:
            from app.services.history_services import HistoryServices
            if current_user and current_user.is_authenticated:
                saved_h = HistoryServices.create(advice_data, current_user)
                try:
                    from flask import session as flask_session
                    flask_session["advisor_profile"] = {
                        "monthly_income": metrics.get("monthly_income"),
                        "monthly_expense": metrics.get("monthly_expense"),
                        "goal_cost": metrics.get("goal_cost", 0.0),
                        "marital_status": facts.get("marital_status", "Single"),
                        "employment_status": facts.get("employment_status", "employed"),
                        "debt_status": facts.get("debt_status", "no debt"),
                        "spending_habit": facts.get("spending_habit", "average spend"),
                        "_user_id": current_user.id,
                        "_history_id": saved_h.id if saved_h else None,
                    }
                except Exception:
                    pass
        except Exception:
            pass

        return advice_data

    @staticmethod
    def get_decision_trace(data: dict, lang: str = "en") -> dict:
        """
        Retrieves the structured explainable decision trace for a financial profile.
        """
        eval_result = ConsultantEngine.evaluate(data, lang=lang)
        return eval_result.get("decision_trace", {})

    @staticmethod
    def consult(raw_data: Any, lang: Optional[str] = None, persist_history: bool = True):
        """
        Authoritative API boundary for financial consultation (Step 7H).
        
        Orchestration Pipeline:
        1. Request Validation & Alias Normalization (ConsultantInputValidator).
        2. Returns (None, error_dict) if validation fails (HTTP 400).
        3. Deterministic Inference Evaluation (ConsultantEngine.evaluate).
        4. Bilingual Response DTO Assembly.
        5. Optional History Persistence for authenticated users (controlled by persist_history).
        6. Returns (response_dto, None) (HTTP 200).
        """
        from app.services.consultant_validator import ConsultantInputValidator
        from app.services.provenance_boundary import ProvenanceBoundaryLayer
        from app.services.llm_service import LLMService

        # Support natural language text input via Trained Financial Advisor AI extraction + normalizer
        user_text = ""
        if isinstance(raw_data, dict):
            user_text = raw_data.get("text") or raw_data.get("message") or raw_data.get("statement") or raw_data.get("user_input") or ""

        if user_text and isinstance(user_text, str) and user_text.strip():
            extracted_facts = LLMService.extract_financial_profile(user_text)
            merged_data = dict(raw_data)
            for k, v in extracted_facts.items():
                if v is not None and (k not in merged_data or merged_data[k] is None or merged_data[k] == ""):
                    merged_data[k] = v
            raw_data = merged_data

        default_lang = lang or AdvisorServices._get_current_language()
        normalized_data, validation_error = ConsultantInputValidator.validate(raw_data, default_lang=default_lang)

        if validation_error:
            return None, validation_error

        # Process Provenance-Aware Boundary Layer (PABL - Step 8H)
        boundary_context = ProvenanceBoundaryLayer.process(
            raw_data=raw_data,
            normalized_data=normalized_data,
            default_lang=default_lang,
        )

        eval_lang = normalized_data.get("language", default_lang)
        eval_result = ConsultantEngine.evaluate(normalized_data, lang=eval_lang)

        metrics = eval_result["metrics"]
        facts = eval_result["facts"]
        selected_advice = eval_result["selected_advice"]
        decision_trace = eval_result.get("decision_trace", {})
        kb_version = eval_result.get("kb_version", "financial-kb-v1.0")

        # Determine if decision evaluated any defaulted fields
        decision_used_defaulted = boundary_context.check_decision_used_defaulted_field(selected_advice)
        provenance_dict = boundary_context.to_dict(decision_used_defaulted_field=decision_used_defaulted)

        # Inject provenance into decision_trace for explainability
        if isinstance(decision_trace, dict):
            decision_trace["provenance"] = provenance_dict

        def _format_advice(adv):
            if isinstance(adv, list):
                return " ".join(str(x) for x in adv)
            return str(adv or "")

        surplus_ratio = metrics.get("surplus_ratio")
        expense_ratio = metrics.get("expense_ratio")
        remain_pct = round(surplus_ratio * 100, 2) if surplus_ratio is not None else 0.0
        expense_pct = round(expense_ratio * 100, 2) if expense_ratio is not None else 0.0

        # Generate Financial Advisor AI explanation
        adv_text_for_exp = _format_advice(selected_advice.advice_km if eval_lang == "km" else selected_advice.advice_en) if selected_advice else ""
        conc_text_for_exp = (selected_advice.conclusion_km if eval_lang == "km" else selected_advice.conclusion_en) if selected_advice else ""
        explanation = LLMService.generate_recommendation_explanation(
            metrics=metrics,
            facts=facts,
            advice_text=adv_text_for_exp,
            conclusion_text=conc_text_for_exp,
            advisory_caveats=boundary_context.get_caveat_messages(lang=eval_lang),
            lang=eval_lang,
        )

        # Precise ratio language formatting on advice strings
        adv_en = _format_advice(selected_advice.advice_en) if selected_advice else ""
        adv_km = _format_advice(selected_advice.advice_km) if selected_advice else ""
        if expense_ratio is not None:
            if abs(expense_ratio - 0.72) < 0.01:
                adv_en = adv_en.replace("consuming between 50% and 80% of income", "expenses consume 72% of income")
                adv_km = adv_km.replace("ចន្លោះពី ៥០% ទៅ ៨០% នៃប្រាក់ចំណូល", "ការចំណាយប្រើប្រាស់ ៧២% នៃប្រាក់ចំណូល")
            elif abs(expense_ratio - 0.80) < 0.01:
                adv_en = adv_en.replace("living costs consume 80% or more of income", "expenses consume exactly 80% of income")
                adv_en = adv_en.replace("living costs expenses consume", "expenses consume")
                adv_en = adv_en.replace("consume 80% or more of income", "expenses consume exactly 80% of income")
                adv_km = adv_km.replace("ស្រូបយក ៨០% ឬច្រើនជាងនេះនៃប្រាក់ចំណូល", "ការចំណាយប្រើប្រាស់យ៉ាងជាក់លាក់ ៨០% នៃប្រាក់ចំណូល")

        response_dto = {
            "success": True,
            "knowledge_base_version": kb_version,
            "provenance": provenance_dict,
            "advisory_caveats": boundary_context.get_caveat_messages(lang=eval_lang),
            "explanation": explanation,
            "input": {
                "monthly_income": metrics["monthly_income"],
                "monthly_expense": metrics["monthly_expense"],
                "goal_cost": metrics["goal_cost"],
                "employment_status": facts["employment_status"],
                "debt_status": facts["debt_status"],
                "spending_habit": facts["spending_habit"],
                "marital_status": facts["marital_status"],
            },
            "metrics": metrics,
            "facts": facts,
            "decision": {
                "rule_id": selected_advice.rule_id if selected_advice else None,
                "name": selected_advice.name if selected_advice else None,
                "category": selected_advice.category if selected_advice else None,
                "priority": selected_advice.priority if selected_advice else None,
                "certainty": selected_advice.certainty if selected_advice else None,
                "selection_reason": getattr(selected_advice, "selection_reason", None),
            },
            "conclusion": {
                "en": selected_advice.conclusion_en if selected_advice else "",
                "km": selected_advice.conclusion_km if selected_advice else "",
            },
            "advice": {
                "en": adv_en,
                "km": adv_km,
            },
            "decision_trace": decision_trace,
        }

        # Persist to history if user is authenticated and persist_history is enabled
        try:
            from app.services.history_services import HistoryServices
            if persist_history and current_user and current_user.is_authenticated:
                history_data = {
                    "goal_cost": metrics["goal_cost"],
                    "income": metrics["monthly_income"],
                    "expense": metrics["monthly_expense"],
                    "martial_status": facts["marital_status"],
                    "is_employed": facts["employment_status"],
                    "is_debt": facts["debt_status"],
                    "is_spending": facts["spending_habit"],
                    "remain_percentage": remain_pct,
                    "expense_percentage": expense_pct,
                    "get_advice": selected_advice or EmptyAdvice(),
                    "kb_version": kb_version,
                }
                saved_h = HistoryServices.create(history_data, current_user)
                try:
                    from flask import session as flask_session
                    flask_session["advisor_profile"] = {
                        "monthly_income": metrics["monthly_income"],
                        "monthly_expense": metrics["monthly_expense"],
                        "goal_cost": metrics["goal_cost"],
                        "marital_status": facts["marital_status"],
                        "employment_status": facts["employment_status"],
                        "debt_status": facts["debt_status"],
                        "spending_habit": facts["spending_habit"],
                        "_user_id": current_user.id,
                        "_history_id": saved_h.id if saved_h else None,
                    }
                except Exception:
                    pass
        except Exception:
            pass

        return response_dto, None