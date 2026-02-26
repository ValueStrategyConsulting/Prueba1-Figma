"""Page 2: Work Requests — Planner Review Queue.

Dashboard-style page for planners to review AI-classified work requests.
Card-based layout with status metrics, quick approve/reject, and
expandable detail panels.
"""

import logging
logger = logging.getLogger("02_work_requests")

import html as _html
import streamlit as st
from streamlit_app import api_client
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_mvp_style, apply_wr_style
from streamlit_app.components.feedback import feedback_widget

st.set_page_config(page_title="Work Requests", page_icon=":clipboard:", layout="wide")
page_init()
apply_mvp_style()
apply_wr_style()

st.title(t("work_requests.title"))
st.caption(t("work_requests.subtitle"))

@st.cache_data(ttl=120, show_spinner=False)
def _load_work_requests():
    try:
        return api_client.list_work_requests()
    except Exception:
        return []

# ── Load all work requests ───────────────────────────────────────

all_wr = _load_work_requests()

# ── Status Counts Dashboard ─────────────────────────────────────

counts = {"DRAFT": 0, "PENDING_VALIDATION": 0, "VALIDATED": 0, "REJECTED": 0}
for wr in all_wr:
    s = wr.get("status", "UNKNOWN")
    if s in counts:
        counts[s] += 1

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total", len(all_wr))
col2.metric("Draft", counts["DRAFT"])
col3.metric("Pending", counts["PENDING_VALIDATION"])
col4.metric("Validated", counts["VALIDATED"])
col5.metric("Rejected", counts["REJECTED"])

# Status pills
st.markdown(f"""
<div style='display:flex; gap:12px; margin:12px 0 20px; flex-wrap:wrap;'>
    <span class='status-pill pill-draft'>DRAFT: {counts["DRAFT"]}</span>
    <span class='status-pill pill-pending'>PENDING: {counts["PENDING_VALIDATION"]}</span>
    <span class='status-pill pill-validated'>VALIDATED: {counts["VALIDATED"]}</span>
    <span class='status-pill pill-rejected'>REJECTED: {counts["REJECTED"]}</span>
</div>
""", unsafe_allow_html=True)

# ── Filter ───────────────────────────────────────────────────────

col_f1, _ = st.columns([1, 4])
with col_f1:
    status_filter = st.selectbox(
        t("work_requests.filter_by_status"),
        ["All", "DRAFT", "PENDING_VALIDATION", "VALIDATED", "REJECTED"],
    )

filtered_wr = all_wr if status_filter == "All" else [
    wr for wr in all_wr if wr.get("status") == status_filter
]

if not filtered_wr:
    st.info(t("work_requests.no_requests"))
    st.stop()

# ── Status and priority styling config ───────────────────────────

_STATUS_CFG = {
    "DRAFT": {"bg": "#FFF7ED", "color": "#C2410C", "border": "#FB923C"},
    "PENDING_VALIDATION": {"bg": "#FFFBEB", "color": "#B45309", "border": "#FBBF24"},
    "VALIDATED": {"bg": "#DCFCE7", "color": "#166534", "border": "#4ADE80"},
    "REJECTED": {"bg": "#FEE2E2", "color": "#991B1B", "border": "#F87171"},
}
_DEFAULT_CFG = {"bg": "#F1F5F9", "color": "#6B7280", "border": "#D1D5DB"}

# ── Card-based Work Request List ─────────────────────────────────

for wr in filtered_wr:
    wr_id = wr["request_id"]
    status = wr.get("status", "UNKNOWN")
    equip = wr.get("equipment_tag", "N/A")
    confidence = wr.get("equipment_confidence", 0)
    ai = wr.get("ai_classification") or {}
    priority = ai.get("priority_suggested", "N/A")
    wo_type = ai.get("work_order_type", "N/A")
    duration = ai.get("estimated_duration_hours", "N/A")
    specialties = ", ".join(ai.get("required_specialties", []))
    created = (wr.get("created_at") or "")[:16]
    cfg = _STATUS_CFG.get(status, _DEFAULT_CFG)

    # Card HTML
    st.markdown(f"""
    <div class='wr-card' style='border-left:4px solid {cfg["border"]};'>
        <div class='wr-header'>
            <div class='wr-equip'>{_html.escape(str(equip))}</div>
            <div class='wr-meta'>
                <span style='font-size:0.78rem; font-weight:600; color:#6B7280;'>{_html.escape(str(priority).replace('_', ' '))}</span>
                <span class='wr-status' style='background:{cfg["bg"]}; color:{cfg["color"]};'>{_html.escape(str(status))}</span>
            </div>
        </div>
        <div class='wr-body'>
            <span>WO: {_html.escape(str(wo_type))}</span>
            <span>Duration: {_html.escape(str(duration))}h</span>
            <span>Specialties: {_html.escape(str(specialties))}</span>
            <span>Confidence: {confidence:.0%}</span>
            <span style='color:#9CA3AF;'>{_html.escape(str(created))}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action buttons (only for actionable statuses)
    if status in ("DRAFT", "PENDING_VALIDATION"):
        col_a, col_b, col_c, _ = st.columns([1, 1, 1, 3])
        with col_a:
            if st.button("Approve", key=f"approve_{wr_id}", type="primary"):
                try:
                    api_client.validate_work_request(wr_id, "APPROVE")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        with col_b:
            if st.button("Reject", key=f"reject_{wr_id}"):
                try:
                    api_client.validate_work_request(wr_id, "REJECT")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        with col_c:
            if st.button("Details", key=f"detail_{wr_id}"):
                st.session_state[f"expand_{wr_id}"] = not st.session_state.get(f"expand_{wr_id}", False)

    # Expandable detail panel
    if st.session_state.get(f"expand_{wr_id}", False):
        try:
            detail = api_client.get_work_request(wr_id)
            pd_data = detail.get("problem_description") or {}
            ai_d = detail.get("ai_classification") or {}
            parts = detail.get("spare_parts") or []

            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown("**Structured Description:**")
                st.info(pd_data.get("structured_description", "N/A"))
                if pd_data.get("failure_mode_detected"):
                    st.markdown(f"Failure Mode: **{pd_data['failure_mode_detected']}**")
                if pd_data.get("affected_component"):
                    st.markdown(f"Component: **{pd_data['affected_component']}**")
            with col_r:
                st.markdown(f"**Priority Justification:** {ai_d.get('priority_justification', 'N/A')}")
                if ai_d.get("safety_flags"):
                    st.error(f"Safety: {', '.join(ai_d['safety_flags'])}")
                if parts:
                    st.markdown("**Spare Parts:**")
                    for p in parts:
                        st.markdown(f"- {p.get('description', 'N/A')} (Qty: {p.get('quantity_needed', 0)})")
        except Exception as e:
            logger.exception("Unexpected error")
            st.warning("Could not load full details.")

    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

feedback_widget("work_requests")
