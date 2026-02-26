"""Reusable form builders for Streamlit pages."""

import streamlit as st
from streamlit_app.i18n import t

CRITICALITY_CATEGORIES = [
    "SAFETY", "HEALTH", "ENVIRONMENT", "PRODUCTION", "OPERATING_COST",
    "CAPITAL_COST", "SCHEDULE", "REVENUE", "COMMUNICATIONS", "COMPLIANCE", "REPUTATION",
]

MECHANISMS = [
    "ARCS", "BLOCKS", "BREAKS_FRACTURE_SEPARATES", "CORRODES", "CRACKS",
    "DEGRADES", "DISTORTS", "DRIFTS", "EXPIRES", "IMMOBILISED", "LOOSES_PRELOAD",
    "OPEN_CIRCUIT", "OVERHEATS_MELTS", "SEVERS", "SHORT_CIRCUITS",
    "THERMALLY_OVERLOADS", "WASHES_OFF", "WEARS",
]

TASK_TYPES = ["INSPECT", "CHECK", "TEST", "LUBRICATE", "CLEAN", "REPLACE", "REPAIR", "CALIBRATE"]

STRATEGY_TYPES = ["CONDITION_BASED", "FIXED_TIME", "RUN_TO_FAILURE", "FAULT_FINDING", "REDESIGN"]

FAILURE_CONSEQUENCES = [
    "HIDDEN_SAFETY", "HIDDEN_NONSAFETY", "EVIDENT_SAFETY",
    "EVIDENT_ENVIRONMENTAL", "EVIDENT_OPERATIONAL", "EVIDENT_NONOPERATIONAL",
]


def criticality_matrix_form(key_prefix: str = "crit") -> tuple[list[dict], int]:
    st.subheader(t("forms.criticality_matrix"))
    scores = []
    cols = st.columns(3)
    for i, cat in enumerate(CRITICALITY_CATEGORIES):
        col = cols[i % 3]
        label = t(f"forms.category_{cat.lower()}")
        val = col.slider(label, 1, 5, 3, key=f"{key_prefix}_{cat}")
        scores.append({"category": cat, "consequence_level": val})
    probability = st.slider(t("forms.probability"), 1, 5, 3, key=f"{key_prefix}_prob")
    return scores, probability


def failure_mode_form(key_prefix: str = "fm") -> dict:
    st.subheader(t("forms.failure_mode_entry"))
    col1, col2 = st.columns(2)
    what = col1.text_input(t("forms.what_component"), key=f"{key_prefix}_what")
    mechanism = col1.selectbox(t("fmea.mechanism"), MECHANISMS, key=f"{key_prefix}_mech")
    cause = col2.text_input(t("forms.cause"), key=f"{key_prefix}_cause")
    consequence = col2.selectbox(t("forms.consequence"), FAILURE_CONSEQUENCES, key=f"{key_prefix}_cons")
    strategy = st.selectbox(t("forms.strategy_type"), STRATEGY_TYPES, key=f"{key_prefix}_strat")
    is_hidden = st.checkbox(t("forms.hidden_failure"), key=f"{key_prefix}_hidden")
    return {
        "what": what, "mechanism": mechanism, "cause": cause,
        "failure_consequence": consequence, "strategy_type": strategy, "is_hidden": is_hidden,
    }
