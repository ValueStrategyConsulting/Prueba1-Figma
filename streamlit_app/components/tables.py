"""Reusable table formatting for Streamlit."""

import streamlit as st


def render_data_table(data: list[dict], title: str = "", key_columns: list[str] | None = None):
    if title:
        st.subheader(title)
    if not data:
        from streamlit_app.i18n import t
        st.info(t("common.no_data_available"))
        return
    if key_columns:
        filtered = [{k: row.get(k, "") for k in key_columns} for row in data]
        st.dataframe(filtered, width="stretch")
    else:
        st.dataframe(data, width="stretch")


def status_badge(status: str) -> str:
    colors = {
        "DRAFT": "orange", "REVIEWED": "blue", "APPROVED": "green",
        "GENERATED": "gray", "UPLOADED": "purple",
        "OPEN": "red", "IN_PROGRESS": "orange", "CLOSED": "green", "VERIFIED": "blue",
        "ACTIVE": "green", "INACTIVE": "gray",
    }
    color = colors.get(status, "gray")
    return f":{color}[{status}]"


def metric_row(metrics: dict):
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label, value)
