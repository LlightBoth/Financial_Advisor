from urllib.parse import urlsplit, urljoin
from flask import Blueprint, session, abort, redirect, request, url_for
from flask_login import current_user
from app.utils.i18n import SUPPORTED_LANGUAGES

lang_bp = Blueprint("lang", __name__)


def is_safe_url(target: str) -> bool:
    """Validates that target redirect URL is safe and points to the same application host.
    Rejects missing, external, malformed, or script-based URLs (open redirect prevention).
    """
    if not target or not isinstance(target, str):
        return False

    target_cleaned = target.strip()
    target_lower = target_cleaned.lower()

    # Reject dangerous protocols and schemes
    if target_lower.startswith(("javascript:", "data:", "vbscript:", "\\\\")):
        return False

    # Check host matching against request.host_url
    try:
        host_url = request.host_url
        ref_url = urlsplit(host_url)
        test_url = urlsplit(urljoin(host_url, target_cleaned))
        return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc
    except Exception:
        return False


@lang_bp.route("/set-language/<path:language>", methods=["GET", "POST"])
def set_language(language: str):
    """Sets active language in user session and safely redirects back."""
    # Strict whitelist validation
    if language not in SUPPORTED_LANGUAGES:
        abort(400, description=f"Unsupported language code: {language}")

    # Persist in session
    session["lang"] = language

    # Safe redirect to previous page if safe, otherwise safe internal fallback
    target = request.args.get("next") or request.referrer
    if target and is_safe_url(target):
        return redirect(target)

    # Safe internal fallback
    if current_user.is_authenticated:
        return redirect(url_for("dashboards.userIndex"))
    return redirect(url_for("home"))
