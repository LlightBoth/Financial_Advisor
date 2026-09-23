"""
Provenance-Aware Boundary Layer (PABL) - Step 8H.

Authoritative boundary service bridging the Natural Language Understanding (NLU)
perception layer and the deterministic ConsultantEngine.

Architectural Principles:
1. Perception Integrity: Unmentioned or missing slots remain 'unknown' (value=None).
   The NLU layer must never hallucinate defaults as confirmed user facts.
2. Legacy Compatibility: For Knowledge Base financial-kb-v1.0, safe defaults are
   injected into the legacy evaluation payload ('defaulted_legacy') to prevent
   predicate crashes and unintended fallback drops.
3. Decision Authority: The boundary layer never selects rules, computes metrics,
   or makes financial recommendations. ConsultantEngine remains the sole authority.
4. Explainability & Auditability: Structured provenance metadata accompanies every
   consultation, explicitly identifying defaulted fields and assumption caveats.
5. Inferred Limitation: In Phase 1, automatic inference is strictly disabled to
   prevent false certainty.
"""

from typing import Dict, Any, Optional, List, Tuple, Set


class ProvenanceState:
    """
    Canonical Provenance States (Step 8G / 8H).
    """
    EXPLICIT = "explicit"                  # Direct user/text affirmation
    UNKNOWN = "unknown"                    # Unmentioned or missing in session
    DEFAULTED_LEGACY = "defaulted_legacy"  # Injected strictly for legacy engine compatibility
    INFERRED = "inferred"                  # Synthesized from other facts (disabled in Phase 1)


class SlotProvenance:
    """
    Provenance container for an individual financial slot.
    """

    def __init__(
        self,
        field_name: str,
        value: Any,
        provenance: str,
        legacy_default: Optional[Any] = None,
        source: str = "unmentioned",
        raw_input: Optional[Any] = None,
    ):
        self.field_name = field_name
        self.value = value  # The unpolluted user value (None if unknown)
        self.provenance = provenance  # EXPLICIT, UNKNOWN, DEFAULTED_LEGACY, INFERRED
        self.legacy_default = legacy_default
        self.source = source
        self.raw_input = raw_input

    @property
    def is_explicit(self) -> bool:
        return self.provenance == ProvenanceState.EXPLICIT

    @property
    def is_unknown(self) -> bool:
        return self.provenance == ProvenanceState.UNKNOWN

    @property
    def is_defaulted(self) -> bool:
        return self.provenance == ProvenanceState.DEFAULTED_LEGACY or (
            self.provenance == ProvenanceState.UNKNOWN and self.legacy_default is not None
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Emits structured slot-level provenance.
        """
        res: Dict[str, Any] = {
            "value": self.value,
            "original_value": self.value,
            "provenance": self.provenance,
            "engine_state": ProvenanceState.DEFAULTED_LEGACY if (self.is_unknown and self.legacy_default is not None) else self.provenance,
            "is_defaulted": bool(self.legacy_default is not None and not self.is_explicit),
        }
        if self.legacy_default is not None:
            res["legacy_default"] = self.legacy_default
            res["legacy_value"] = self.legacy_default
        else:
            res["legacy_value"] = self.value
        if self.source:
            res["source"] = self.source
        return res

    def __repr__(self) -> str:
        return f"<SlotProvenance {self.field_name}={self.value} [{self.provenance}]>"


class BoundaryContext:
    """
    Structured context returned by ProvenanceBoundaryLayer.
    Encapsulates slot-level provenance, legacy engine payload, and advisory disclosures.
    """

    def __init__(
        self,
        fields: Dict[str, SlotProvenance],
        legacy_payload: Dict[str, Any],
        language: str = "en",
        conflicts: Optional[List[Dict[str, Any]]] = None,
    ):
        self.fields = fields
        self.legacy_payload = legacy_payload
        self.language = language
        self.conflicts: List[Dict[str, Any]] = conflicts or []
        self.conflicts_present: bool = len(self.conflicts) > 0

        # Categorize fields
        self.explicit_fields: List[str] = [
            k for k, sp in fields.items() if sp.is_explicit
        ]
        self.unknown_fields: List[str] = [
            k for k, sp in fields.items() if sp.is_unknown
        ]
        self.defaulted_fields: List[str] = [
            k for k, sp in fields.items() if sp.legacy_default is not None and not sp.is_explicit
        ]

        self.assumptions_present: bool = len(self.defaulted_fields) > 0
        self.assumptions: List[Dict[str, Any]] = self._build_assumptions()
        self.advisory_caveats: List[Dict[str, Any]] = self._build_advisory_caveats()
        self.decision_used_defaulted_field: Optional[bool] = None

    def _build_assumptions(self) -> List[Dict[str, Any]]:
        """
        Constructs explainable assumption records for defaulted fields.
        """
        assumptions = []
        for f in self.defaulted_fields:
            sp = self.fields[f]
            if f == "debt_status":
                assumptions.append({
                    "field": "debt_status",
                    "assumed_value": sp.legacy_default,
                    "impact": "Advice assumes zero active debt. High-interest debt repayment is not factored into recommendations."
                })
            elif f == "employment_status":
                assumptions.append({
                    "field": "employment_status",
                    "assumed_value": sp.legacy_default,
                    "impact": "Employment stability not factored into recommendations; emergency buffer assumes income instability."
                })
            elif f == "spending_habit":
                assumptions.append({
                    "field": "spending_habit",
                    "assumed_value": sp.legacy_default,
                    "impact": "Assumes standard average expenditure behavior."
                })
            elif f == "goal_cost":
                assumptions.append({
                    "field": "goal_cost",
                    "assumed_value": sp.legacy_default,
                    "impact": "Assumes no active target savings milestone."
                })
            elif f == "marital_status":
                assumptions.append({
                    "field": "marital_status",
                    "assumed_value": sp.legacy_default,
                    "impact": "Assumes single tax and household baseline."
                })
            else:
                assumptions.append({
                    "field": f,
                    "assumed_value": sp.legacy_default,
                    "impact": f"Assumed default value '{sp.legacy_default}' for legacy rule compatibility."
                })
        return assumptions

    def _build_advisory_caveats(self) -> List[Dict[str, Any]]:
        """
        Constructs safe advisory caveats for user-facing disclosure.
        Structured metadata prevents misleading advice when critical fields were omitted.
        """
        caveats = []
        if "debt_status" in self.defaulted_fields:
            caveats.append({
                "field": "debt_status",
                "code": "CAVEAT_DEBT_UNSPECIFIED",
                "message_en": "Debt status was not specified. Recommendations assume zero active debt. If you carry debt, prioritize debt servicing before allocating funds to capital investments.",
                "message_km": "ស្ថានភាពបំណុលមិនត្រូវបានបញ្ជាក់ទេ។ អនុសាសន៍សន្មត់ថាគ្មានបំណុលសកម្ម។ ប្រសិនបើអ្នកមានបំណុល សូមផ្តល់អាទិភាពដល់ការសងបំណុលជាមុន។",
            })
        if "employment_status" in self.defaulted_fields:
            caveats.append({
                "field": "employment_status",
                "code": "CAVEAT_EMPLOYMENT_UNSPECIFIED",
                "message_en": "Employment status was not specified. Recommendations assume non-guaranteed employment stability.",
                "message_km": "ស្ថានភាពការងារមិនត្រូវបានបញ្ជាក់ទេ។ អនុសាសន៍សន្មត់ថាមិនមានស្ថិរភាពការងារដែលធានា។",
            })
        for c in self.conflicts:
            caveats.append({
                "field": c["field"],
                "code": f"CAVEAT_CONFLICT_{c['field'].upper()}",
                "message_en": f"Conflicting values were detected for {c['field'].replace('_', ' ')}. Kept as unknown to prevent false certainty.",
                "message_km": f"ព័ត៌មានដែលផ្ទុយគ្នាត្រូវបានរកឃើញសម្រាប់ {c['field']}។ តម្លៃត្រូវបានរក្សាទុកថាមិនស្គាល់ ដើម្បីការពារភាពមិនច្បាស់លាស់។",
            })
        return caveats

    def check_decision_used_defaulted_field(self, selected_advice: Any) -> bool:
        """
        Determines whether the selected canonical rule condition evaluated a defaulted field.
        """
        if not selected_advice:
            self.decision_used_defaulted_field = False
            return False

        rule_id = getattr(selected_advice, "rule_id", None)
        if not rule_id:
            self.decision_used_defaulted_field = False
            return False

        # Canonical rule dependencies in financial-kb-v1.0
        rule_dependencies: Dict[str, Set[str]] = {
            "INCOME_ZERO_UNEMPLOYED": {"monthly_income", "employment_status"},
            "BALANCED_BUDGET_BUFFER_BUILDING": {"monthly_income", "monthly_expense", "debt_status"},
            "FLEXIBLE_BUDGET_CAPITAL_GROWTH": {"monthly_income", "monthly_expense", "debt_status"},
            "TIGHT_MARGIN_HIGH_EXPENSE": {"monthly_income", "monthly_expense", "debt_status"},
            "SURPLUS_WITH_DEBT_SERVICING": {"monthly_income", "monthly_expense", "debt_status"},
            "DEFICIT_NO_DEBT": {"monthly_income", "monthly_expense", "debt_status"},
            "DEFICIT_WITH_DEBT": {"monthly_income", "monthly_expense", "debt_status"},
            "BREAK_EVEN_ZERO_MARGIN": {"monthly_income", "monthly_expense"},
        }

        deps = rule_dependencies.get(rule_id, set())
        used = any(f in self.defaulted_fields for f in deps)
        self.decision_used_defaulted_field = used
        return used

    def get_caveat_messages(self, lang: str = "en") -> List[str]:
        """
        Returns flat list of caveat messages in the requested language.
        """
        msg_key = f"message_{lang}" if lang in ("en", "km") else "message_en"
        return [c.get(msg_key, c.get("message_en", "")) for c in self.advisory_caveats]

    def to_dict(self, decision_used_defaulted_field: Optional[bool] = None) -> Dict[str, Any]:
        """
        Renders authoritative, backward-compatible provenance section for API response.
        """
        if decision_used_defaulted_field is not None:
            self.decision_used_defaulted_field = decision_used_defaulted_field

        fields_dict = {k: sp.to_dict() for k, sp in self.fields.items()}

        return {
            "fields": fields_dict,
            "explicit_fields": list(self.explicit_fields),
            "unknown_fields": list(self.unknown_fields),
            "defaulted_fields": list(self.defaulted_fields),
            "assumptions_present": self.assumptions_present,
            "assumptions": self.assumptions,
            "conflicts_present": self.conflicts_present,
            "conflicts": self.conflicts,
            "decision_used_defaulted_field": (
                self.decision_used_defaulted_field
                if self.decision_used_defaulted_field is not None
                else False
            ),
            "advisory_caveats": self.advisory_caveats,
        }


class ProvenanceBoundaryLayer:
    """
    Authoritative boundary service between NLU extraction and ConsultantEngine.
    """

    # Legacy default values strictly required by financial-kb-v1.0
    LEGACY_DEFAULTS: Dict[str, Any] = {
        "debt_status": "no debt",
        "employment_status": "not employed",
        "spending_habit": "average spend",
        "goal_cost": 0.0,
        "marital_status": "Single",
        "language": "en",
    }

    # Canonical aliases matching ConsultantInputValidator
    _DEBT_TRUE_ALIASES = {"true", "1", "debt", "yes", "active", "has debt", "have debt"}
    _DEBT_FALSE_ALIASES = {"false", "0", "no debt", "none", "no", "debt-free", "debt free"}

    _EMPLOYED_TRUE_ALIASES = {"true", "1", "employed", "yes", "working", "job"}
    _EMPLOYED_FALSE_ALIASES = {"false", "0", "not employed", "no", "unemployed", "none"}

    _SPENDING_HIGH_ALIASES = {"true", "1", "big spend", "high", "yes"}
    _SPENDING_AVG_ALIASES = {"false", "0", "average spend", "moderate", "no", "average", "avg"}

    _MARITAL_SINGLE_ALIASES = {"single", "unmarried", "divorced", "widowed", "false", "0"}
    _MARITAL_MARRIED_ALIASES = {"married", "partnered", "true", "1"}

    @classmethod
    def process(
        cls,
        raw_data: Any,
        normalized_data: Optional[Dict[str, Any]] = None,
        default_lang: str = "en",
    ) -> BoundaryContext:
        """
        Main ingress boundary method.

        Analyzes raw inputs, extracts unpolluted slot values, determines provenance states,
        and provides safe defaults for the legacy engine payload.

        Args:
            raw_data: Raw JSON payload, web form dictionary, or NLU extraction result.
            normalized_data: Pre-validated dictionary from ConsultantInputValidator if available.
            default_lang: Default language string ('en' or 'km').

        Returns:
            BoundaryContext with slot provenance and legacy evaluation payload.
        """
        # 1. Unpack NLU container if nested
        data_dict: Dict[str, Any] = {}
        metadata: Dict[str, Any] = {}
        if isinstance(raw_data, dict):
            if isinstance(raw_data.get("slots"), dict):
                # NLU record format: { "slots": { ... }, "slot_spans": [...], "metadata": { ... } }
                data_dict = dict(raw_data["slots"])
                metadata = raw_data.get("metadata") or {}
                # Carry top-level overrides if present
                for k in ("language", "lang"):
                    if k in raw_data:
                        data_dict[k] = raw_data[k]
            else:
                data_dict = dict(raw_data)
                metadata = raw_data.get("metadata") or {}

        # 2. Check for third-party entity indicators
        third_party_keys = ("spouse_income", "partner_income", "parent_income", "other_income", "third_party_income")
        has_third_party_income = any(data_dict.get(k) is not None for k in third_party_keys)
        is_third_party = bool(
            metadata.get("is_third_party")
            or data_dict.get("is_third_party")
            or data_dict.get("third_party_entity")
            or metadata.get("subject") in ("spouse", "partner", "parent", "other", "third_party")
            or data_dict.get("entity_owner") == "third_party"
            or metadata.get("entity_owner") == "third_party"
        )

        conflicts: List[Dict[str, Any]] = []
        fields: Dict[str, SlotProvenance] = {}
        legacy_payload: Dict[str, Any] = dict(normalized_data) if normalized_data else {}

        # ─────────────────────────────────────────────────────────────
        # 3. Process Slot: monthly_income
        # ─────────────────────────────────────────────────────────────
        raw_inc1 = data_dict.get("monthly_income")
        raw_inc2 = data_dict.get("income")
        has_inc_conflict = False
        if raw_inc1 is not None and raw_inc2 is not None and raw_inc1 != "" and raw_inc2 != "":
            try:
                if float(raw_inc1) != float(raw_inc2):
                    has_inc_conflict = True
            except (ValueError, TypeError):
                has_inc_conflict = True
        if metadata.get("has_conflict") or metadata.get("ambiguity_type") in ("conflicting_income", "conflict") or data_dict.get("conflicting_income"):
            has_inc_conflict = True

        income_val = raw_inc1 if raw_inc1 is not None else raw_inc2

        # Third-party income protection: third-party income must never become user's income
        if is_third_party or (has_third_party_income and raw_inc1 is None and raw_inc2 is None):
            fields["monthly_income"] = SlotProvenance(
                field_name="monthly_income",
                value=None,
                provenance=ProvenanceState.UNKNOWN,
                legacy_default=None,
                source="third_party_input_ignored",
                raw_input=income_val or next((data_dict.get(k) for k in third_party_keys if data_dict.get(k) is not None), None),
            )
            if "monthly_income" not in legacy_payload:
                legacy_payload["monthly_income"] = None
        elif has_inc_conflict:
            # Conflicting income: do not resolve silently into false certainty
            fields["monthly_income"] = SlotProvenance(
                field_name="monthly_income",
                value=None,
                provenance=ProvenanceState.UNKNOWN,
                legacy_default=None,
                source="conflicting_inputs",
                raw_input={"monthly_income": raw_inc1, "income": raw_inc2},
            )
            conflicts.append({
                "field": "monthly_income",
                "type": "conflicting_income",
                "description": "Conflicting income values provided; preserved as unknown to avoid false certainty.",
                "raw_values": [raw_inc1, raw_inc2],
            })
            if "monthly_income" not in legacy_payload:
                legacy_payload["monthly_income"] = None
        elif income_val is None or income_val == "":
            # Missing income remains unknown, NEVER converted to 0.0 in provenance
            fields["monthly_income"] = SlotProvenance(
                field_name="monthly_income",
                value=None,
                provenance=ProvenanceState.UNKNOWN,
                legacy_default=None,  # Income is required; no silent default
                source="unmentioned",
                raw_input=income_val,
            )
            if "monthly_income" not in legacy_payload:
                legacy_payload["monthly_income"] = None
        else:
            try:
                # Explicit zero is valid and preserved
                norm_inc = float(income_val)
                fields["monthly_income"] = SlotProvenance(
                    field_name="monthly_income",
                    value=norm_inc,
                    provenance=ProvenanceState.EXPLICIT,
                    legacy_default=None,
                    source="user_input",
                    raw_input=income_val,
                )
                legacy_payload["monthly_income"] = norm_inc
                legacy_payload["income"] = norm_inc
            except (ValueError, TypeError):
                fields["monthly_income"] = SlotProvenance(
                    field_name="monthly_income",
                    value=None,
                    provenance=ProvenanceState.UNKNOWN,
                    legacy_default=None,
                    source="invalid_format",
                    raw_input=income_val,
                )

        # ─────────────────────────────────────────────────────────────
        # 4. Process Slot: monthly_expense
        # ─────────────────────────────────────────────────────────────
        expense_val = data_dict.get("monthly_expense")
        if expense_val is None:
            expense_val = data_dict.get("expense")

        if expense_val is None or expense_val == "":
            fields["monthly_expense"] = SlotProvenance(
                field_name="monthly_expense",
                value=None,
                provenance=ProvenanceState.UNKNOWN,
                legacy_default=None,
                source="unmentioned",
                raw_input=expense_val,
            )
            if "monthly_expense" not in legacy_payload:
                legacy_payload["monthly_expense"] = None
        else:
            try:
                norm_exp = float(expense_val)
                fields["monthly_expense"] = SlotProvenance(
                    field_name="monthly_expense",
                    value=norm_exp,
                    provenance=ProvenanceState.EXPLICIT,
                    legacy_default=None,
                    source="user_input",
                    raw_input=expense_val,
                )
                legacy_payload["monthly_expense"] = norm_exp
                legacy_payload["expense"] = norm_exp
            except (ValueError, TypeError):
                fields["monthly_expense"] = SlotProvenance(
                    field_name="monthly_expense",
                    value=None,
                    provenance=ProvenanceState.UNKNOWN,
                    legacy_default=None,
                    source="invalid_format",
                    raw_input=expense_val,
                )

        # ─────────────────────────────────────────────────────────────
        # 5. Process Slot: debt_status
        # ─────────────────────────────────────────────────────────────
        raw_debt1 = data_dict.get("debt_status")
        raw_debt2 = data_dict.get("is_debt")
        has_debt_conflict = False
        if raw_debt1 is not None and raw_debt2 is not None and raw_debt1 != "" and raw_debt2 != "":
            norm_d1 = cls._normalize_debt(raw_debt1)
            norm_d2 = cls._normalize_debt(raw_debt2)
            if norm_d1 is not None and norm_d2 is not None and norm_d1 != norm_d2:
                has_debt_conflict = True
        if metadata.get("ambiguity_type") in ("conflicting_debt", "conflict") or (metadata.get("conflicting_slots") and "debt_status" in metadata.get("conflicting_slots")):
            has_debt_conflict = True

        debt_val = raw_debt1 if raw_debt1 is not None else raw_debt2

        if has_debt_conflict:
            fields["debt_status"] = SlotProvenance(
                field_name="debt_status",
                value=None,
                provenance=ProvenanceState.UNKNOWN,
                legacy_default=cls.LEGACY_DEFAULTS["debt_status"],
                source="conflicting_inputs",
                raw_input={"debt_status": raw_debt1, "is_debt": raw_debt2},
            )
            legacy_payload["debt_status"] = cls.LEGACY_DEFAULTS["debt_status"]
            legacy_payload["is_debt"] = cls.LEGACY_DEFAULTS["debt_status"]
            conflicts.append({
                "field": "debt_status",
                "type": "conflicting_debt",
                "description": "Conflicting debt status values provided; preserved as unknown to avoid false certainty.",
                "raw_values": [raw_debt1, raw_debt2],
            })
        elif debt_val is None or debt_val == "":
            # Missing debt remains UNKNOWN; defaulted only in legacy_payload
            fields["debt_status"] = SlotProvenance(
                field_name="debt_status",
                value=None,
                provenance=ProvenanceState.UNKNOWN,
                legacy_default=cls.LEGACY_DEFAULTS["debt_status"],
                source="unmentioned",
                raw_input=debt_val,
            )
            legacy_payload["debt_status"] = cls.LEGACY_DEFAULTS["debt_status"]
            legacy_payload["is_debt"] = cls.LEGACY_DEFAULTS["debt_status"]
        else:
            # Parse explicit debt
            norm_debt = cls._normalize_debt(debt_val)
            if norm_debt is not None:
                fields["debt_status"] = SlotProvenance(
                    field_name="debt_status",
                    value=norm_debt,
                    provenance=ProvenanceState.EXPLICIT,
                    legacy_default=None,
                    source="user_input",
                    raw_input=debt_val,
                )
                legacy_payload["debt_status"] = norm_debt
                legacy_payload["is_debt"] = norm_debt
            else:
                fields["debt_status"] = SlotProvenance(
                    field_name="debt_status",
                    value=None,
                    provenance=ProvenanceState.UNKNOWN,
                    legacy_default=cls.LEGACY_DEFAULTS["debt_status"],
                    source="invalid_value",
                    raw_input=debt_val,
                )
                legacy_payload["debt_status"] = cls.LEGACY_DEFAULTS["debt_status"]

        # ─────────────────────────────────────────────────────────────
        # 6. Process Slot: employment_status
        # ─────────────────────────────────────────────────────────────
        raw_emp1 = data_dict.get("employment_status")
        raw_emp2 = data_dict.get("is_employed")
        has_emp_conflict = False
        if raw_emp1 is not None and raw_emp2 is not None and raw_emp1 != "" and raw_emp2 != "":
            norm_e1 = cls._normalize_employment(raw_emp1)
            norm_e2 = cls._normalize_employment(raw_emp2)
            if norm_e1 is not None and norm_e2 is not None and norm_e1 != norm_e2:
                has_emp_conflict = True
        if metadata.get("ambiguity_type") in ("conflicting_employment", "conflict") or (metadata.get("conflicting_slots") and "employment_status" in metadata.get("conflicting_slots")):
            has_emp_conflict = True

        emp_val = raw_emp1 if raw_emp1 is not None else raw_emp2

        if has_emp_conflict:
            fields["employment_status"] = SlotProvenance(
                field_name="employment_status",
                value=None,
                provenance=ProvenanceState.UNKNOWN,
                legacy_default=cls.LEGACY_DEFAULTS["employment_status"],
                source="conflicting_inputs",
                raw_input={"employment_status": raw_emp1, "is_employed": raw_emp2},
            )
            legacy_payload["employment_status"] = cls.LEGACY_DEFAULTS["employment_status"]
            legacy_payload["is_employed"] = cls.LEGACY_DEFAULTS["employment_status"]
            conflicts.append({
                "field": "employment_status",
                "type": "conflicting_employment",
                "description": "Conflicting employment status values provided; preserved as unknown to avoid false certainty.",
                "raw_values": [raw_emp1, raw_emp2],
            })
        elif emp_val is None or emp_val == "":
            # Missing employment remains UNKNOWN; defaulted only in legacy_payload
            fields["employment_status"] = SlotProvenance(
                field_name="employment_status",
                value=None,
                provenance=ProvenanceState.UNKNOWN,
                legacy_default=cls.LEGACY_DEFAULTS["employment_status"],
                source="unmentioned",
                raw_input=emp_val,
            )
            legacy_payload["employment_status"] = cls.LEGACY_DEFAULTS["employment_status"]
            legacy_payload["is_employed"] = cls.LEGACY_DEFAULTS["employment_status"]
        else:
            norm_emp = cls._normalize_employment(emp_val)
            if norm_emp is not None:
                fields["employment_status"] = SlotProvenance(
                    field_name="employment_status",
                    value=norm_emp,
                    provenance=ProvenanceState.EXPLICIT,
                    legacy_default=None,
                    source="user_input",
                    raw_input=emp_val,
                )
                legacy_payload["employment_status"] = norm_emp
                legacy_payload["is_employed"] = norm_emp
            else:
                fields["employment_status"] = SlotProvenance(
                    field_name="employment_status",
                    value=None,
                    provenance=ProvenanceState.UNKNOWN,
                    legacy_default=cls.LEGACY_DEFAULTS["employment_status"],
                    source="invalid_value",
                    raw_input=emp_val,
                )
                legacy_payload["employment_status"] = cls.LEGACY_DEFAULTS["employment_status"]

        # ─────────────────────────────────────────────────────────────
        # 7. Process Slot: spending_habit
        # ─────────────────────────────────────────────────────────────
        spend_val = data_dict.get("spending_habit")
        if spend_val is None:
            spend_val = data_dict.get("is_spending")

        if spend_val is None or spend_val == "":
            fields["spending_habit"] = SlotProvenance(
                field_name="spending_habit",
                value=None,
                provenance=ProvenanceState.UNKNOWN,
                legacy_default=cls.LEGACY_DEFAULTS["spending_habit"],
                source="unmentioned",
                raw_input=spend_val,
            )
            legacy_payload["spending_habit"] = cls.LEGACY_DEFAULTS["spending_habit"]
            legacy_payload["is_spending"] = cls.LEGACY_DEFAULTS["spending_habit"]
        else:
            norm_spend = cls._normalize_spending(spend_val)
            if norm_spend is not None:
                fields["spending_habit"] = SlotProvenance(
                    field_name="spending_habit",
                    value=norm_spend,
                    provenance=ProvenanceState.EXPLICIT,
                    legacy_default=None,
                    source="user_input",
                    raw_input=spend_val,
                )
                legacy_payload["spending_habit"] = norm_spend
                legacy_payload["is_spending"] = norm_spend
            else:
                fields["spending_habit"] = SlotProvenance(
                    field_name="spending_habit",
                    value=None,
                    provenance=ProvenanceState.UNKNOWN,
                    legacy_default=cls.LEGACY_DEFAULTS["spending_habit"],
                    source="invalid_value",
                    raw_input=spend_val,
                )
                legacy_payload["spending_habit"] = cls.LEGACY_DEFAULTS["spending_habit"]

        # ─────────────────────────────────────────────────────────────
        # 8. Process Slot: goal_cost
        # ─────────────────────────────────────────────────────────────
        goal_val = data_dict.get("goal_cost")
        if goal_val is None or goal_val == "":
            fields["goal_cost"] = SlotProvenance(
                field_name="goal_cost",
                value=None,
                provenance=ProvenanceState.UNKNOWN,
                legacy_default=cls.LEGACY_DEFAULTS["goal_cost"],
                source="unmentioned",
                raw_input=goal_val,
            )
            legacy_payload["goal_cost"] = cls.LEGACY_DEFAULTS["goal_cost"]
        else:
            try:
                norm_goal = float(goal_val)
                fields["goal_cost"] = SlotProvenance(
                    field_name="goal_cost",
                    value=norm_goal,
                    provenance=ProvenanceState.EXPLICIT,
                    legacy_default=None,
                    source="user_input",
                    raw_input=goal_val,
                )
                legacy_payload["goal_cost"] = norm_goal
            except (ValueError, TypeError):
                fields["goal_cost"] = SlotProvenance(
                    field_name="goal_cost",
                    value=None,
                    provenance=ProvenanceState.UNKNOWN,
                    legacy_default=cls.LEGACY_DEFAULTS["goal_cost"],
                    source="invalid_format",
                    raw_input=goal_val,
                )
                legacy_payload["goal_cost"] = cls.LEGACY_DEFAULTS["goal_cost"]

        # ─────────────────────────────────────────────────────────────
        # 9. Process Slot: marital_status
        # ─────────────────────────────────────────────────────────────
        mar_val = data_dict.get("marital_status")
        if mar_val is None:
            mar_val = data_dict.get("martial_status")

        if mar_val is None or mar_val == "":
            fields["marital_status"] = SlotProvenance(
                field_name="marital_status",
                value=None,
                provenance=ProvenanceState.UNKNOWN,
                legacy_default=cls.LEGACY_DEFAULTS["marital_status"],
                source="unmentioned",
                raw_input=mar_val,
            )
            legacy_payload["marital_status"] = cls.LEGACY_DEFAULTS["marital_status"]
            legacy_payload["martial_status"] = cls.LEGACY_DEFAULTS["marital_status"]
        else:
            norm_mar = cls._normalize_marital(mar_val)
            if norm_mar is not None:
                fields["marital_status"] = SlotProvenance(
                    field_name="marital_status",
                    value=norm_mar,
                    provenance=ProvenanceState.EXPLICIT,
                    legacy_default=None,
                    source="user_input",
                    raw_input=mar_val,
                )
                legacy_payload["marital_status"] = norm_mar
                legacy_payload["martial_status"] = norm_mar
            else:
                fields["marital_status"] = SlotProvenance(
                    field_name="marital_status",
                    value=None,
                    provenance=ProvenanceState.UNKNOWN,
                    legacy_default=cls.LEGACY_DEFAULTS["marital_status"],
                    source="invalid_value",
                    raw_input=mar_val,
                )
                legacy_payload["marital_status"] = cls.LEGACY_DEFAULTS["marital_status"]

        # 10. Language resolution
        lang_val = data_dict.get("language") or data_dict.get("lang") or default_lang
        lang_clean = str(lang_val).strip().lower() if lang_val else default_lang
        active_lang = "km" if lang_clean in ("km", "khmer", "kh") else "en"
        legacy_payload["language"] = active_lang
        legacy_payload["lang"] = active_lang

        return BoundaryContext(
            fields=fields,
            legacy_payload=legacy_payload,
            language=active_lang,
            conflicts=conflicts,
        )

    # ─────────────────────────────────────────────────────────────
    # Internal Normalization Helpers
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def _normalize_debt(cls, val: Any) -> Optional[str]:
        if isinstance(val, bool):
            return "debt" if val else "no debt"
        if isinstance(val, (int, float)):
            if val == 1:
                return "debt"
            if val == 0:
                return "no debt"
            return None
        v_str = str(val).strip().lower()
        if v_str in cls._DEBT_TRUE_ALIASES:
            return "debt"
        if v_str in cls._DEBT_FALSE_ALIASES:
            return "no debt"
        return None

    @classmethod
    def _normalize_employment(cls, val: Any) -> Optional[str]:
        if isinstance(val, bool):
            return "employed" if val else "not employed"
        if isinstance(val, (int, float)):
            if val == 1:
                return "employed"
            if val == 0:
                return "not employed"
            return None
        v_str = str(val).strip().lower()
        if v_str in cls._EMPLOYED_TRUE_ALIASES:
            return "employed"
        if v_str in cls._EMPLOYED_FALSE_ALIASES:
            return "not employed"
        return None

    @classmethod
    def _normalize_spending(cls, val: Any) -> Optional[str]:
        if isinstance(val, bool):
            return "big spend" if val else "average spend"
        if isinstance(val, (int, float)):
            if val == 1:
                return "big spend"
            if val == 0:
                return "average spend"
            return None
        v_str = str(val).strip().lower()
        if v_str in cls._SPENDING_HIGH_ALIASES:
            return "big spend"
        if v_str in cls._SPENDING_AVG_ALIASES:
            return "average spend"
        return None

    @classmethod
    def _normalize_marital(cls, val: Any) -> Optional[str]:
        v_str = str(val).strip().lower()
        if v_str in cls._MARITAL_SINGLE_ALIASES:
            return "Single"
        if v_str in cls._MARITAL_MARRIED_ALIASES:
            return "Married"
        return None
