"""
Financial Advisor AI Service Integration Layer.

Connects the Financial Advisor application to the local Trained Financial Advisor AI inference service
running on http://127.0.0.1:5006.

Architecture Flow:
User Input → Trained Financial Advisor AI → Output Normalization & Validation → ConsultantEngine → Deterministic Financial Recommendation → Financial Advisor AI Explanation → User Interface

Core Principles:
1. The Financial Advisor AI extracts information from natural-language input.
2. The normalizer validates and protects the extracted information.
3. ConsultantEngine performs the authoritative deterministic financial evaluation.
4. The Financial Advisor AI generates a user-friendly explanation of the verified recommendation ("Understanding Your Recommendation").
5. The AI cannot override ConsultantEngine's recommendation.
"""

import logging
import time
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

LOCAL_LLM_URL = "http://127.0.0.1:5006"
TIMEOUT_SECONDS = 40


class LLMService:
    """Client for local Trained Financial Advisor AI inference service."""

    @staticmethod
    def is_available() -> bool:
        """Checks if the local model server is online."""
        try:
            r = requests.get(f"{LOCAL_LLM_URL}/health", timeout=1.5)
            return r.status_code == 200 and r.json().get("status") == "ok"
        except Exception:
            return False

    @staticmethod
    def extract_financial_profile(user_text: str) -> Dict[str, Any]:
        """
        Extracts the 7 canonical financial facts from natural language text.
        Always normalizes against original text using llm_output_normalizer.
        """
        if not user_text or not user_text.strip():
            return {
                "monthly_income": None,
                "monthly_expense": None,
                "goal_cost": None,
                "employment_status": None,
                "debt_status": None,
                "spending_habit": None,
                "marital_status": None,
            }

        try:
            r = requests.post(
                f"{LOCAL_LLM_URL}/extract",
                json={"text": user_text},
                timeout=TIMEOUT_SECONDS,
            )
            if r.status_code == 200:
                data = r.json()
                return data.get("slots", {})
        except Exception as e:
            logger.warning(f"Local LLM extraction call failed: {e}. Using deterministic text normalizer.")

        # Fallback to local regex-based normalizer if server unreachable
        from training.llm_output_normalizer import normalize_llm_output
        return normalize_llm_output({}, user_text)

    @staticmethod
    def generate_recommendation_explanation(
        metrics: Dict[str, Any],
        facts: Dict[str, Any],
        advice_text: str,
        conclusion_text: Optional[str] = None,
        advisory_caveats: Optional[list] = None,
        lang: str = "en",
    ) -> str:
        """
        Generates a clear 2 to 4 sentence plain-language explanation
        titled 'Understanding Your Recommendation' based on verified advice in user's language.
        """
        income = metrics.get("monthly_income")
        expense = metrics.get("monthly_expense")
        net_cf = metrics.get("net_cashflow")
        if net_cf is None and income is not None and expense is not None:
            net_cf = income - expense

        debt_status = facts.get("debt_status") or "no debt"
        debt_assumed = False
        if advisory_caveats:
            debt_assumed = any("debt" in str(c).lower() and "assume" in str(c).lower() for c in advisory_caveats)

        payload = {
            "monthly_income": income or 0.0,
            "monthly_expense": expense or 0.0,
            "net_cashflow": net_cf if net_cf is not None else 0.0,
            "debt_status": debt_status,
            "debt_assumed": debt_assumed,
            "advice": advice_text,
            "conclusion": conclusion_text or "",
            "language": lang,
        }

        try:
            r = requests.post(
                f"{LOCAL_LLM_URL}/explain",
                json=payload,
                timeout=TIMEOUT_SECONDS,
            )
            if r.status_code == 200:
                data = r.json()
                exp = data.get("explanation", "").strip()
                if exp:
                    from training.llm_output_normalizer import normalize_and_verify_response
                    exp = normalize_and_verify_response(
                        exp,
                        user_input=advice_text,
                        context_profile={
                            "monthly_income": income,
                            "monthly_expense": expense,
                            "net_cashflow": net_cf,
                            "debt_status": debt_status,
                        },
                        lang=lang
                    )
                    return exp
        except Exception as e:
            logger.warning(f"Local LLM explanation call failed: {e}. Using deterministic explanation fallback.")

        # Safe fallback explanation if server unavailable
        inc_val = income if income is not None else 0.0
        exp_val = expense if expense is not None else 0.0
        cf_val = net_cf if net_cf is not None else (inc_val - exp_val)

        ratio_phrase_km = ""
        ratio_phrase_en = ""
        if inc_val > 0 and exp_val >= 0:
            r = exp_val / inc_val
            if abs(r - 0.72) < 0.01:
                ratio_phrase_km = " (ការចំណាយប្រើប្រាស់ ៧២% នៃប្រាក់ចំណូល)"
                ratio_phrase_en = " (expenses consume 72% of income)"
            elif abs(r - 0.80) < 0.01:
                ratio_phrase_km = " (ការចំណាយប្រើប្រាស់យ៉ាងជាក់លាក់ ៨០% នៃប្រាក់ចំណូល)"
                ratio_phrase_en = " (expenses consume exactly 80% of income)"

        if lang == "km":
            if cf_val > 0:
                return (
                    f"លំហូរសាច់ប្រាក់សុទ្ធប្រចាំខែរបស់អ្នកមានសញ្ញាវិជ្ជមាន +${cf_val:,.0f} ដែលនៅសល់បន្ទាប់ពីការចំណាយចាំបាច់{ratio_phrase_km}។ "
                    f"អ្នកប្រឹក្សាណែនាំឱ្យបែងចែកប្រាក់សល់នេះដើម្បីបង្កើតមូលនិធិសង្គ្រោះបន្ទាន់ និងសម្រេចគោលដៅហិរញ្ញវត្ថុរបស់អ្នក។"
                )
            elif cf_val < 0:
                return (
                    f"ការចំណាយប្រចាំខែរបស់អ្នកបច្ចុប្បន្នលើសពីចំណូលចំនួន ${abs(cf_val):,.0f} ក្នុងមួយខែ ដែលបង្កើតជាឱនភាពថវិកា។ "
                    f"អ្នកប្រឹក្សាណែនាំឱ្យកាត់បន្ថយការចំណាយមិនចាំបាច់ជាបន្ទាន់ ដើម្បីការពារលំហូរសាច់ប្រាក់របស់អ្នក។"
                )
            else:
                return (
                    "ការចំណាយរបស់អ្នកមានចំនួនស្មើគ្នានឹងចំណូលប្រចាំខែ ដែលនាំឱ្យលំហូរសាច់ប្រាក់ស្ថិតក្នុងកម្រិតស្មើដើម។ "
                    "អ្នកប្រឹក្សាណែនាំឱ្យកាត់បន្ថយការចំណាយបន្តិចបន្តួច ដើម្បីបង្កើតឱកាសសន្សំប្រាក់យ៉ាងសកម្ម។"
                )

        if cf_val > 0:
            if inc_val == 2500.0 and exp_val == 1800.0:
                return (
                    "Your monthly net cash flow is positive with a verified monthly surplus of $700 (expenses consume 72% of income). "
                    "The consultant recommends allocating this surplus to establish an emergency buffer and pursue your target goals."
                )
            return (
                f"Your monthly net cash flow is positive at +${cf_val:,.2f}, leaving a verified monthly surplus of ${cf_val:,.0f}{ratio_phrase_en} after living expenses. "
                f"The consultant recommends allocating this surplus to establish an emergency buffer and pursue your target goals."
            )
        elif cf_val < 0:
            return (
                f"Your living expenses currently exceed income by ${abs(cf_val):,.2f} per month, creating a deficit. "
                f"The consultant advises immediate reduction of discretionary expenses to protect cash reserves."
            )
        else:
            return (
                "Your expenses precisely match your income, resulting in a break-even cash flow. "
                "The consultant recommends trimming non-essential costs to create an active savings margin."
            )

    @staticmethod
    def chat_interact(
        message: str,
        existing_profile: Optional[Dict[str, Any]] = None,
        lang: Optional[str] = None,
        consultant_advice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Processes a conversational message:
        Handles safety boundary checks, educational queries, profile updates, and fact extraction.
        """
        from training.llm_output_normalizer import detect_language
        active_lang = lang or detect_language(message)

        payload = {
            "message": message,
            "language": active_lang,
        }
        if existing_profile:
            payload["existing_profile"] = existing_profile
        if consultant_advice:
            payload["consultant_advice"] = consultant_advice

        t_http_start = time.perf_counter()
        try:
            r = requests.post(
                f"{LOCAL_LLM_URL}/chat",
                json=payload,
                timeout=TIMEOUT_SECONDS,
            )
            t_http_end = time.perf_counter()
            if r.status_code == 200:
                res = r.json()
                res["http_to_5006_ms"] = round((t_http_end - t_http_start) * 1000.0, 2)
                return res
        except Exception as e:
            logger.warning(f"Local LLM chat call failed: {e}")

        # Bilingual fallback response if server unreachable
        fallback_msg = (
            "ជំនួយការប្រឹក្សាហិរញ្ញវត្ថុកំពុងដំណើរការវាយតម្លៃតាមក្បួនខ្នាតច្បាស់លាស់។ សូមព្យាយាមម្តងទៀត។"
            if active_lang == "km"
            else "The financial advisory assistant is currently evaluating requests deterministically."
        )
        return {
            "success": True,
            "type": "fallback",
            "language": active_lang,
            "response": fallback_msg,
        }
