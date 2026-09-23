import os
import json
from flask import session, has_request_context, request

SUPPORTED_LANGUAGES = {
    "en": "English",
    "km": "ខ្មែរ",
}

DEFAULT_LANGUAGE = "en"

_TRANSLATIONS_CACHE = {}
_TRANSLATIONS_MTIMES = {}
_TRANSLATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "translations")


def _load_translation_file(lang: str) -> dict:
    """Safely loads translation file for a given language code.
    Guarantees no KeyError, FileNotFoundError, or JSONDecodeError is raised.
    Auto-refreshes if translation file is modified on disk.
    """
    file_path = os.path.join(_TRANSLATIONS_DIR, f"{lang}.json")
    if not os.path.isfile(file_path):
        _TRANSLATIONS_CACHE[lang] = {}
        return _TRANSLATIONS_CACHE[lang]

    try:
        mtime = os.path.getmtime(file_path)
    except OSError:
        mtime = 0

    if lang in _TRANSLATIONS_CACHE and _TRANSLATIONS_CACHE[lang] and _TRANSLATIONS_MTIMES.get(lang) == mtime:
        return _TRANSLATIONS_CACHE[lang]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                _TRANSLATIONS_CACHE[lang] = data
                _TRANSLATIONS_MTIMES[lang] = mtime
            else:
                _TRANSLATIONS_CACHE[lang] = {}
    except (FileNotFoundError, json.JSONDecodeError, OSError, Exception):
        if lang not in _TRANSLATIONS_CACHE:
            _TRANSLATIONS_CACHE[lang] = {}

    return _TRANSLATIONS_CACHE[lang]


# Pre-warm cache for supported languages
for _code in SUPPORTED_LANGUAGES:
    _load_translation_file(_code)

# Alias for external inspection or testing
_translations = _TRANSLATIONS_CACHE


def get_locale() -> str:
    """Determines the active locale for the current request.
    Priority:
      1. Explicit session preference ('lang' or 'language')
      2. Browser Accept-Language header match
      3. Default fallback ('en')
    Always returns a valid language code present in SUPPORTED_LANGUAGES.
    """
    if not has_request_context():
        return DEFAULT_LANGUAGE

    # 1. Session preference
    sess_lang = session.get("lang") or session.get("language")
    if sess_lang and sess_lang in SUPPORTED_LANGUAGES:
        return sess_lang

    # 2. Browser Accept-Language header match
    if request.accept_languages:
        best_match = request.accept_languages.best_match(list(SUPPORTED_LANGUAGES.keys()))
        if best_match and best_match in SUPPORTED_LANGUAGES:
            return best_match

    # 3. Default
    return DEFAULT_LANGUAGE


def translate(key: str, lang: str = None, **kwargs) -> str:
    """Translates a key string into the current or specified language with safe fallback:
      requested language -> English default -> original key.
    Never throws an exception on missing or malformed keys.
    """
    if key is None:
        return ""

    key_str = str(key)
    if not key_str:
        return ""

    if lang is not None and lang in SUPPORTED_LANGUAGES:
        target_lang = lang
    else:
        target_lang = get_locale()

    # 1. Attempt lookup in target language dictionary
    try:
        lang_dict = _load_translation_file(target_lang)
    except Exception:
        lang_dict = {}
    val = lang_dict.get(key_str)

    # 2. Fallback to default language dictionary if missing
    if val is None and target_lang != DEFAULT_LANGUAGE:
        try:
            default_dict = _load_translation_file(DEFAULT_LANGUAGE)
        except Exception:
            default_dict = {}
        val = default_dict.get(key_str)

    # 3. Fallback to the original key string
    if val is None:
        val = key_str

    # Format with kwargs if parameters provided
    if kwargs:
        try:
            val = val.format(**kwargs)
        except Exception:
            pass

    return val


# Standard shorthand alias
_ = translate


class LazyString:
    """A lazy string proxy that defers translation until string conversion.
    Allows form field labels and validator messages to be declared at class definition
    time and evaluated at request time in the active locale.
    """
    def __init__(self, key: str, **kwargs):
        self.key = key
        self.kwargs = kwargs

    def __str__(self) -> str:
        return translate(self.key, **self.kwargs)

    def __html__(self) -> str:
        return translate(self.key, **self.kwargs)

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other):
        return str(self) == str(other)

    def __mod__(self, other):
        return str(self) % other

    def __add__(self, other):
        return str(self) + str(other)

    def __radd__(self, other):
        return str(other) + str(self)

    def __contains__(self, item):
        return item in str(self)

    def __len__(self):
        return len(str(self))

    def __iter__(self):
        return iter(str(self))

    def __hash__(self):
        return hash(str(self))

    def __bool__(self):
        return bool(str(self))


def lazy_translate(key: str, **kwargs) -> LazyString:
    return LazyString(key, **kwargs)


_l = lazy_translate


class I18NTranslations:
    """Translation provider for WTForms Meta.get_translations."""
    def gettext(self, string: str) -> str:
        return translate(string)

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        return translate(singular if n == 1 else plural)

