"""Page 11: Backlog & Schedule — M3 Backlog Optimization."""

import logging
logger = logging.getLogger("03_backlog")

import streamlit as st
from streamlit_app import api_client
from streamlit_app.components.charts import (
    backlog_stratification_chart,
    schedule_utilization_chart,
    priority_distribution_pie,
)
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_mvp_style
from streamlit_app.components.feedback import feedback_widget

st.set_page_config(page_title="Backlog & Schedule", page_icon="📊", layout="wide")
page_init()
apply_mvp_style()

st.title(t("backlog.title"))
st.markdown(t("backlog.subtitle"))

@st.cache_data(ttl=120, show_spinner=False)
def _load_backlog(status=None, priority=None):
    try:
        return api_client.list_backlog(status=status, priority=priority)
    except Exception:
        return []

@st.cache_data(ttl=120, show_spinner=False)
def _load_schedule():
    try:
        return api_client.get_schedule()
    except Exception:
        return None

tab_backlog, tab_optimize, tab_schedule = st.tabs([t("backlog.tab_backlog"), t("backlog.tab_optimize"), t("backlog.tab_schedule")])

with tab_backlog:
    st.subheader(t("backlog.current_backlog"))

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        status_filter = st.selectbox(t("backlog.status_filter"), [None, "AWAITING_MATERIALS", "AWAITING_SHUTDOWN", "AWAITING_APPROVAL", "SCHEDULED"])
    with col_f2:
        priority_filter = st.selectbox(t("backlog.priority_filter"), [None, "1_EMERGENCY", "2_URGENT", "3_NORMAL", "4_PLANNED"])

    items = _load_backlog(status=status_filter, priority=priority_filter)

    if items:
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric(t("backlog.total_items"), len(items))
        ready = sum(1 for i in items if i.get("materials_ready"))
        col_m2.metric(t("backlog.materials_ready"), ready)
        total_hours = sum(i.get("estimated_hours", 0) for i in items)
        col_m3.metric(t("backlog.total_hours"), f"{total_hours:.0f}h")

        st.plotly_chart(priority_distribution_pie(items), width="stretch")
        st.dataframe(items, width="stretch")
    else:
        st.info(t("backlog.no_items"))

with tab_optimize:
    st.subheader(t("backlog.run_optimization"))

    col_o1, col_o2 = st.columns(2)
    with col_o1:
        plant_id = st.text_input(t("common.plant_id"), value="OCP-JFC1")
    with col_o2:
        period_days = st.slider(t("backlog.planning_horizon"), 7, 90, 30)

    if st.button(t("backlog.run_optimization_btn"), type="primary"):
        try:
            result = api_client.optimize_backlog(plant_id, period_days)
            st.session_state["last_optimization"] = result
            st.success(t("backlog.optimization_complete"))
        except Exception as e:
            st.error(f"Error: {e}")

    opt = st.session_state.get("last_optimization")
    if opt:
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        col_r1.metric(t("backlog.total_items"), opt.get("total_items", 0))
        col_r2.metric(t("backlog.schedulable_now"), opt.get("schedulable_now", 0))
        col_r3.metric(t("backlog.blocked"), opt.get("blocked", 0))
        col_r4.metric(t("backlog.work_packages"), opt.get("work_packages", 0))

        strat = opt.get("stratification", {})
        if strat:
            st.plotly_chart(backlog_stratification_chart(strat), width="stretch")

        opt_id = opt.get("optimization_id", "")
        if st.button(t("backlog.approve_schedule")):
            try:
                approval = api_client.approve_schedule(opt_id)
                st.success(f"Schedule APPROVED: {approval}")
            except Exception as e:
                st.error(str(e))

with tab_schedule:
    st.subheader(t("backlog.latest_schedule"))
    schedule_data = _load_schedule()

    if schedule_data and "schedule" in schedule_data and schedule_data["schedule"]:
        col_s1, col_s2 = st.columns(2)
        col_s1.metric("Status", schedule_data.get("status", "N/A"))
        col_s2.metric("Period", f"{schedule_data.get('period_start', '')} to {schedule_data.get('period_end', '')}")

        schedule_entries = schedule_data.get("schedule", [])
        if schedule_entries:
            st.plotly_chart(schedule_utilization_chart(schedule_entries), width="stretch")

        work_packages = schedule_data.get("work_packages", [])
        if work_packages:
            st.subheader(t("backlog.work_packages"))
            st.dataframe(work_packages, width="stretch")

        alerts = schedule_data.get("alerts", [])
        if alerts:
            st.subheader(t("backlog.alerts"))
            for alert in alerts:
                alert_type = alert.get("type", "INFO")
                msg = alert.get("message", "")
                if alert_type in ("OVERDUE", "PRIORITY_ESCALATION"):
                    st.error(f"**{alert_type}:** {msg}")
                elif alert_type == "MATERIAL_DELAY":
                    st.warning(f"**{alert_type}:** {msg}")
                else:
                    st.info(f"**{alert_type}:** {msg}")
    else:
        st.info(t("backlog.no_schedule"))

feedback_widget("backlog")
