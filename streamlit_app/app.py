"""OCP Maintenance AI MVP — Dashboard Landing Page.

Launch: PYTHONPATH=. streamlit run streamlit_app/app.py
Requires: FastAPI backend running at http://localhost:8000
"""

import streamlit as st
from streamlit_app.i18n import init_language, language_switcher, apply_rtl, t
from streamlit_app.style import apply_mvp_style
from streamlit_app import api_client
from streamlit_app.components.feedback import feedback_widget

st.set_page_config(
    page_title="OCP Maintenance AI",
    page_icon=":factory:",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_language()
apply_rtl()
apply_mvp_style()
language_switcher()

# ── Header ────────────────────────────────────────────────────────
st.markdown("""
<div style='background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 50%, #388E3C 100%);
            border-radius: 16px; padding: 32px 36px; margin-bottom: 24px;
            box-shadow: 0 4px 16px rgba(27,94,32,0.2);'>
    <div style='color: white; font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em;'>
        OCP Maintenance AI
    </div>
    <div style='color: #A5D6A7; font-size: 0.92rem; margin-top: 4px; font-weight: 500;'>
        Intelligent Asset Management Platform — Jorf Fertilizer Complex
    </div>
</div>
""", unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────────
try:
    stats = api_client.get_stats()
    api_connected = True
except Exception:
    stats = {}
    api_connected = False

try:
    all_wr = api_client.list_work_requests()
    pending_wr = [wr for wr in all_wr if wr.get("status") in ("DRAFT", "PENDING_VALIDATION")]
except Exception:
    all_wr, pending_wr = [], []

try:
    captures = api_client.list_captures()
except Exception:
    captures = []

try:
    backlog = api_client.list_backlog()
except Exception:
    backlog = []

# ── Row 1: Key Metrics ──────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric(t("home.total_captures"), len(captures), help=t("home.captures_help"))
col2.metric(
    t("home.pending_review"),
    len(pending_wr),
    delta=f"{len(pending_wr)} awaiting" if pending_wr else None,
    delta_color="inverse",
)
col3.metric(t("home.backlog_size"), len(backlog))
col4.metric(t("home.equipment_nodes"), stats.get("total_nodes", 0))

st.divider()

# ── Row 2: Quick Actions + Recent Activity ──────────────────────
col_actions, col_activity = st.columns([1, 2])

with col_actions:
    st.subheader(t("home.quick_actions"))
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button(t("home.new_capture_btn"), type="primary", use_container_width=True):
        st.switch_page("pages/01_field_capture.py")
    if st.button(t("home.review_requests_btn"), use_container_width=True):
        st.switch_page("pages/02_work_requests.py")
    if st.button(t("home.view_backlog_btn"), use_container_width=True):
        st.switch_page("pages/03_backlog.py")
    if st.button(t("home.view_schedule_btn"), use_container_width=True):
        st.switch_page("pages/04_scheduling.py")

with col_activity:
    st.subheader(t("home.recent_activity"))
    if all_wr:
        for wr in all_wr[:8]:
            status = wr.get("status", "UNKNOWN")
            badge_colors = {
                "DRAFT": ("#FFF7ED", "#C2410C"),
                "PENDING_VALIDATION": ("#FFFBEB", "#B45309"),
                "VALIDATED": ("#DCFCE7", "#166534"),
                "REJECTED": ("#FEE2E2", "#991B1B"),
            }
            badge_bg, badge_color = badge_colors.get(status, ("#F1F5F9", "#6B7280"))
            equip = wr.get("equipment_tag", "N/A")
            created = (wr.get("created_at") or "")[:16]
            ai = wr.get("ai_classification") or {}
            priority = ai.get("priority_suggested", "")

            st.markdown(f"""
            <div style='background:white; border:1px solid #E5E7EB; border-radius:10px;
                        padding:14px 18px; margin-bottom:8px; display:flex;
                        justify-content:space-between; align-items:center;
                        transition: all 0.15s ease; box-shadow: 0 1px 2px rgba(0,0,0,0.04);'>
                <div>
                    <span style='font-weight:700; color:#111827;'>{equip}</span>
                    <span style='color:#9CA3AF; margin-left:10px; font-size:0.8rem;'>{created}</span>
                </div>
                <div style='display:flex; gap:8px; align-items:center;'>
                    <span style='font-size:0.75rem; color:#6B7280; font-weight:500;'>{priority.replace('_', ' ')}</span>
                    <span style='background:{badge_bg}; color:{badge_color}; padding:4px 12px;
                           border-radius:20px; font-size:0.68rem; font-weight:700;
                           letter-spacing:0.03em;'>{status}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(t("home.no_activity"))

# ── Row 3: Status bar ───────────────────────────────────────────
st.divider()
col_s1, col_s2 = st.columns(2)
with col_s1:
    if api_connected:
        st.success(t("common.api_connected", nodes=stats.get("total_nodes", 0)))
    else:
        st.error(t("common.api_not_connected"))
with col_s2:
    st.caption(t("home.safety_notice"))

feedback_widget("dashboard")
