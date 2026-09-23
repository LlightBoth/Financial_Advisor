"""
Financial Consultant Input Validator & Contract Hardening (Step 7H).

Authoritative schema validation, explicit alias normalization, and deterministic
boundary protection for the personal financial consultant expert system.
"""

from typing import Dict, Any, Optional, Tuple


class ConsultantInputValidator:
    """
    Validates and normalizes raw input dictionaries before inference.
    
    Guarantees:
    - Requires monthly_income and monthly_expense.
    - Zero income is valid and preserved.
    - Negative numeric values are strictly rejected with structured error messages.
    - Non-numeric or boolean-as-number types are rejected for numeric fields.
    - Enumerations are strictly validated; arbitrary values produce validation errors.
    - Only documented aliases are normalized.
    - Deterministic boundary protection: client-supplied control fields
      (rule_id, priority, certainty, conditions, kb_version, is_active) are strictly dropped.
    """

    # Explicitly documented aliases for categorical fields
    _EMPLOYED_TRUE_ALIASES = frozenset({"employed", "yes", "true", "1"})
    _EMPLOYED_FALSE_ALIASES = frozenset({"not employed", "no", "false", "0", "prefer_not_say"})

    _DEBT_TRUE_ALIASES = frozenset({"debt", "active", "yes", "true", "1"})
    _DEBT_FALSE_ALIASES = frozenset({"no debt", "none", "no", "false", "0", "prefer_not_say"})

    _SPENDING_HIGH_ALIASES = frozenset({"big spend", "high", "true", "1"})
    _SPENDING_AVG_ALIASES = frozenset({"average spend", "moderate", "low", "false", "0", "prefer_not_say"})

    _MARITAL_SINGLE_ALIASES = frozenset({"single"})
    _MARITAL_MARRIED_ALIASES = frozenset({"married"})

    _SUPPORTED_LANGUAGES = frozenset({"en", "km"})

    # Protected decision-control fields that must never be set by clients
    PROTECTED_CONTROL_FIELDS = frozenset({
        "rule_id",
        "priority",
        "certainty",
        "conditions",
        "kb_version",
        "is_active",
    })

    @classmethod
    def validate(
        cls,
        raw_data: Any,
        default_lang: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Validates and normalizes raw client input.

        Returns:
            (normalized_dict, None) if validation succeeds.
            (None, error_dict) if validation fails.
        """
        if not isinstance(raw_data, dict):
            return None, {
                "code": "VALIDATION_ERROR",
                "message": "Input payload must be a key-value object.",
                "fields": {
                    "payload": "Expected JSON object or form dictionary."
                }
            }

        field_errors: Dict[str, str] = {}

        # 1. monthly_income / income
        income_val = raw_data.get("monthly_income")
        if income_val is None:
            income_val = raw_data.get("income")

        if income_val is None or income_val == "":
            field_errors["monthly_income"] = "Field is required."
            norm_income = None
        elif isinstance(income_val, bool):
            field_errors["monthly_income"] = "Must be a valid number."
            norm_income = None
        else:
            try:
                norm_income = float(income_val)
                if norm_income < 0.0:
                    field_errors["monthly_income"] = "Must be greater than or equal to 0."
                    norm_income = None
            except (ValueError, TypeError):
                field_errors["monthly_income"] = "Must be a valid number."
                norm_income = None

        # 2. monthly_expense / expense
        expense_val = raw_data.get("monthly_expense")
        if expense_val is None:
            expense_val = raw_data.get("expense")

        if expense_val is None or expense_val == "":
            field_errors["monthly_expense"] = "Field is required."
            norm_expense = None
        elif isinstance(expense_val, bool):
            field_errors["monthly_expense"] = "Must be a valid number."
            norm_expense = None
        else:
            try:
                norm_expense = float(expense_val)
                if norm_expense < 0.0:
                    field_errors["monthly_expense"] = "Must be greater than or equal to 0."
                    norm_expense = None
            except (ValueError, TypeError):
                field_errors["monthly_expense"] = "Must be a valid number."
                norm_expense = None

        # 3. goal_cost (optional, defaults to 0.0)
        goal_val = raw_data.get("goal_cost")
        if goal_val is None or goal_val == "":
            norm_goal = 0.0
        elif isinstance(goal_val, bool):
            field_errors["goal_cost"] = "Must be a valid number."
            norm_goal = None
        else:
            try:
                norm_goal = float(goal_val)
                if norm_goal < 0.0:
                    field_errors["goal_cost"] = "Must be greater than or equal to 0."
                    norm_goal = None
            except (ValueError, TypeError):
                field_errors["goal_cost"] = "Must be a valid number."
                norm_goal = None

        # 4. employment_status / is_employed
        emp_val = raw_data.get("employment_status")
        if emp_val is None:
            emp_val = raw_data.get("is_employed")

        if emp_val is None or emp_val == "":
            norm_emp = "not employed"
        elif isinstance(emp_val, bool):
            norm_emp = "employed" if emp_val else "not employed"
        elif isinstance(emp_val, (int, float)):
            if emp_val == 1:
                norm_emp = "employed"
            elif emp_val == 0:
                norm_emp = "not employed"
            else:
                field_errors["employment_status"] = (
                    "Invalid employment status. Expected one of: 'employed', 'not employed'."
                )
                norm_emp = None
        else:
            emp_str = str(emp_val).strip().lower()
            if emp_str in cls._EMPLOYED_TRUE_ALIASES:
                norm_emp = "employed"
            elif emp_str in cls._EMPLOYED_FALSE_ALIASES:
                norm_emp = "not employed"
            else:
                field_errors["employment_status"] = (
                    "Invalid employment status. Expected one of: 'employed', 'not employed'."
                )
                norm_emp = None

        # 5. debt_status / is_debt
        debt_val = raw_data.get("debt_status")
        if debt_val is None:
            debt_val = raw_data.get("is_debt")

        if debt_val is None or debt_val == "":
            norm_debt = "no debt"
        elif isinstance(debt_val, bool):
            norm_debt = "debt" if debt_val else "no debt"
        elif isinstance(debt_val, (int, float)):
            if debt_val == 1:
                norm_debt = "debt"
            elif debt_val == 0:
                norm_debt = "no debt"
            else:
                field_errors["debt_status"] = (
                    "Invalid debt status. Expected one of: 'debt', 'no debt' (or 'active', 'none')."
                )
                norm_debt = None
        else:
            debt_str = str(debt_val).strip().lower()
            if debt_str in cls._DEBT_TRUE_ALIASES:
                norm_debt = "debt"
            elif debt_str in cls._DEBT_FALSE_ALIASES:
                norm_debt = "no debt"
            else:
                field_errors["debt_status"] = (
                    "Invalid debt status. Expected one of: 'debt', 'no debt' (or 'active', 'none')."
                )
                norm_debt = None

        # 6. spending_habit / is_spending
        spend_val = raw_data.get("spending_habit")
        if spend_val is None:
            spend_val = raw_data.get("is_spending")

        if spend_val is None or spend_val == "":
            norm_spend = "average spend"
        elif isinstance(spend_val, bool):
            norm_spend = "big spend" if spend_val else "average spend"
        elif isinstance(spend_val, (int, float)):
            if spend_val == 1:
                norm_spend = "big spend"
            elif spend_val == 0:
                norm_spend = "average spend"
            else:
                field_errors["spending_habit"] = (
                    "Invalid spending habit. Expected one of: 'average spend', 'big spend' (or 'moderate', 'high')."
                )
                norm_spend = None
        else:
            spend_str = str(spend_val).strip().lower()
            if spend_str in cls._SPENDING_HIGH_ALIASES:
                norm_spend = "big spend"
            elif spend_str in cls._SPENDING_AVG_ALIASES:
                norm_spend = "average spend"
            else:
                field_errors["spending_habit"] = (
                    "Invalid spending habit. Expected one of: 'average spend', 'big spend' (or 'moderate', 'high')."
                )
                norm_spend = None

        # 7. marital_status / martial_status
        mar_val = raw_data.get("marital_status")
        if mar_val is None:
            mar_val = raw_data.get("martial_status")

        if mar_val is None or mar_val == "":
            norm_marital = "Single"
        else:
            mar_str = str(mar_val).strip().lower()
            if mar_str in cls._MARITAL_SINGLE_ALIASES:
                norm_marital = "Single"
            elif mar_str in cls._MARITAL_MARRIED_ALIASES:
                norm_marital = "Married"
            else:
                field_errors["marital_status"] = (
                    "Invalid marital status. Expected 'Single' or 'Married'."
                )
                norm_marital = None

        # 8. language / lang
        lang_val = raw_data.get("language")
        if lang_val is None:
            lang_val = raw_data.get("lang")
        if lang_val is None or lang_val == "":
            lang_val = default_lang or "en"

        lang_str = str(lang_val).strip().lower()
        if lang_str in cls._SUPPORTED_LANGUAGES:
            norm_lang = lang_str
        else:
            field_errors["language"] = (
                f"Invalid language '{lang_val}'. Supported languages: 'en', 'km'."
            )
            norm_lang = None

        if field_errors:
            return None, {
                "code": "VALIDATION_ERROR",
                "message": "Invalid consultant input.",
                "fields": field_errors
            }

        # Deterministic Boundary Protection:
        # Build normalized dictionary containing strictly validated fields.
        # Protected control fields (rule_id, priority, certainty, conditions,
        # kb_version, is_active) are completely excluded.
        normalized = {
            "monthly_income": norm_income,
            "monthly_expense": norm_expense,
            "goal_cost": norm_goal,
            "employment_status": norm_emp,
            "debt_status": norm_debt,
            "spending_habit": norm_spend,
            "marital_status": norm_marital,
            "language": norm_lang,
            # Backwards compatibility aliases for engine consumers
            "income": norm_income,
            "expense": norm_expense,
            "is_employed": norm_emp,
            "is_debt": norm_debt,
            "is_spending": norm_spend,
            "martial_status": norm_marital,
        }

        return normalized, None
