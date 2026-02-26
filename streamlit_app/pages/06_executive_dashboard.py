"""Page 14: Executive Dashboard — Consolidated KPI view with traffic lights."""

import logging
logger = logging.getLogger("06_executive_dashboard")

import streamlit as st
from streamlit_app import api_client
from streamlit_app.components.charts import (
    traffic_light_grid, kpi_trend_chart, notification_summary_chart,
    correlation_scatter, bad_actor_overlap_chart,
)
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_mvp_style
from streamlit_app.components.feedback import feedback_widget

st.set_page_config(page_title="Executive Dashboard", layout="wide")
page_init()
apply_mvp_style()

st.title(t("dashboard.title"))
st.caption("Consolidated KPI view with traffic lights, health scores, and cross-module analytics")

@st.cache_data(ttl=300, show_spinner=False)
def _load_kpi_summary(plant_id):
    try:
        return api_client.get_kpi_summary(plant_id)
    except Exception:
        return {}

@st.cache_data(ttl=300, show_spinner=False)
def _load_dashboard(plant_id):
    try:
        return api_client.get_executive_dashboard(plant_id)
    except Exception:
        return {}

@st.cache_data(ttl=300, show_spinner=False)
def _load_alerts(plant_id):
    try:
        return api_client.get_dashboard_alerts(plant_id)
    except Exception:
        return {}

plant_id = st.text_input(t("common.plant_id"), value="OCP-JFC")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    t("dashboard.tab_kpi"), t("dashboard.tab_health"), t("dashboard.tab_trends"),
    t("dashboard.tab_notifications"), t("dashboard.tab_cross_module"),
])

with tab1:
    st.subheader(t("dashboard.kpi_traffic_light"))
    st.info(t("dashboard.generate_report_first"))
    try:
        summary = _load_kpi_summary(plant_id)
        if summary.get("has_data") and summary.get("report"):
            report = summary["report"]
            lights = report.get("traffic_lights", {})
            if lights:
                kpi_data = [
                    {"name": name, "traffic_light": color, "value": 0}
                    for name, color in lights.items()
                ]
                st.plotly_chart(traffic_light_grid(kpi_data), width="stretch")
            else:
                st.info(t("dashboard.no_traffic_light"))
        else:
            st.info(t("dashboard.no_monthly_reports"))
    except Exception as e:
        logger.exception("Unexpected error")
        st.warning(t("common.could_not_connect"))

with tab2:
    st.subheader(t("dashboard.health_risk"))
    try:
        dashboard = _load_dashboard(plant_id)
        col1, col2, col3 = st.columns(3)
        col1.metric(t("dashboard.total_reports"), dashboard.get("total_reports", 0))
        col2.metric(t("dashboard.total_notifications"), dashboard.get("total_notifications", 0))
        col3.metric(t("dashboard.critical_alerts"), dashboard.get("critical_alerts", 0))
    except Exception as e:
        logger.exception("Unexpected error")
        st.warning(t("common.could_not_connect"))

with tab3:
    st.subheader(t("dashboard.kpi_trends"))
    st.info(t("dashboard.select_kpi"))
    kpi_name = st.selectbox(t("dashboard.kpi"), [
        "wo_completion", "schedule_adherence", "pm_compliance",
        "reactive_pct", "backlog_weeks",
    ])
    # Placeholder — trends require historical data
    periods = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    values = [85, 87, 90, 88, 92, 91]
    targets = [90] * 6
    st.plotly_chart(kpi_trend_chart(periods, values, targets, f"{kpi_name} Trend"),
                    width="stretch")

with tab4:
    st.subheader(t("dashboard.active_notifications"))
    try:
        alerts = _load_alerts(plant_id)
        st.metric(t("dashboard.active_alerts"), alerts.get("total_active", 0))
        notifications = alerts.get("alerts", [])
        if notifications:
            st.plotly_chart(notification_summary_chart(notifications), width="stretch")
            for n in notifications[:10]:
                level_icon = {"CRITICAL": "🔴", "WARNING": "🟡"}.get(n.get("level"), "🔵")
                st.write(f"{level_icon} **{n.get('title')}** — {n.get('message', '')}")
        else:
            st.success(t("dashboard.no_alerts"))
    except Exception as e:
        logger.exception("Unexpected error")
        st.warning(t("common.could_not_connect"))

with tab5:
    st.subheader(t("dashboard.cross_module"))
    st.info(t("dashboard.cross_module_info"))
    if st.button(t("dashboard.run_demo")):
        try:
            result = api_client.run_cross_module_analysis(plant_id, {
                "equipment_criticality": [
                    {"equipment_id": "EQ-1", "criticality": "AA"},
                    {"equipment_id": "EQ-2", "criticality": "B"},
                ],
                "failure_records": [
                    {"equipment_id": "EQ-1"}, {"equipment_id": "EQ-1"},
                    {"equipment_id": "EQ-2"},
                ],
            })
            st.json(result)
        except Exception as e:
            st.error(f"Analysis failed: {e}")

feedback_widget("executive_dashboard")
