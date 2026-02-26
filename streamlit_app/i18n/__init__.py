"""Multilingual i18n engine for OCP Maintenance AI Streamlit app.

Supports English (default), French, Arabic (RTL), and Spanish.
Usage in pages:
    from streamlit_app.i18n import page_init, t
    st.set_page_config(...)
    page_init()
    st.title(t("hierarchy.title"))
"""

import json
from pathlib import Path

import streamlit as st

_TRANSLATIONS: dict[str, dict] = {}
_I18N_DIR = Path(__file__).parent

SUPPORTED_LANGUAGES = {
    "en": "English",
    "fr": "Français",
    "es": "Español",
    "ar": "العربية",
}
DEFAULT_LANGUAGE = "en"


def _load_translations():
    """Load all JSON translation files once into module-level cache."""
    global _TRANSLATIONS
    if _TRANSLATIONS:
        return
    for lang_code in SUPPORTED_LANGUAGES:
        filepath = _I18N_DIR / f"{lang_code}.json"
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                _TRANSLATIONS[lang_code] = json.load(f)


def init_language():
    """Initialize session state with default language. Call at top of every page."""
    _load_translations()
    if "language" not in st.session_state:
        st.session_state.language = DEFAULT_LANGUAGE


def t(key: str, **kwargs) -> str:
    """Translate a dotted key like 'criticality.title'.

    Fallback chain: current_lang -> 'en' -> raw key.
    Supports {variable} interpolation via kwargs.
    """
    lang = st.session_state.get("language", DEFAULT_LANGUAGE)
    value = _resolve(lang, key)
    if value is None and lang != "en":
        value = _resolve("en", key)
    if value is None:
        value = key
    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return value


def _resolve(lang: str, dotted_key: str) -> str | None:
    """Walk nested dict using dotted key path."""
    data = _TRANSLATIONS.get(lang, {})
    for part in dotted_key.split("."):
        if isinstance(data, dict):
            data = data.get(part)
        else:
            return None
    return data if isinstance(data, str) else None


def language_switcher():
    """Render language selector in sidebar."""
    lang_options = list(SUPPORTED_LANGUAGES.keys())
    current = st.session_state.get("language", DEFAULT_LANGUAGE)
    current_idx = lang_options.index(current) if current in lang_options else 0

    selected = st.sidebar.selectbox(
        "Language / Langue / Idioma / اللغة",
        lang_options,
        index=current_idx,
        format_func=lambda code: SUPPORTED_LANGUAGES[code],
        key="_i18n_lang",
    )
    if selected != st.session_state.get("language"):
        st.session_state.language = selected
        st.rerun()


def apply_rtl():
    """Inject RTL CSS when Arabic is active."""
    lang = st.session_state.get("language", DEFAULT_LANGUAGE)
    meta = _TRANSLATIONS.get(lang, {}).get("_meta", {})
    if meta.get("direction") == "rtl":
        st.markdown("""
        <style>
            .main .block-container {
                direction: rtl;
                text-align: right;
            }
            section[data-testid="stSidebar"] .block-container {
                direction: ltr;
                text-align: left;
            }
            .stTextInput label, .stSelectbox label, .stTextArea label,
            .stNumberInput label, .stSlider label, .stCheckbox label,
            .stRadio label, .stMultiSelect label {
                direction: rtl;
                text-align: right;
            }
            .stMarkdown, .stText {
                direction: rtl;
                text-align: right;
            }
            [data-testid="stMetricValue"] {
                direction: ltr;
            }
            .stDataFrame th {
                direction: rtl;
                text-align: right;
            }
            .stTabs [data-baseweb="tab"] {
                direction: rtl;
            }
        </style>
        """, unsafe_allow_html=True)


def page_init():
    """Standard initialization for every page. Call after set_page_config()."""
    init_language()
    apply_rtl()
