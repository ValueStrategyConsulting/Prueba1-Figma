"""Page 5: Analytics — KPIs, Health Scores, Weibull Prediction."""

import logging
logger = logging.getLogger("11_analytics")

import streamlit as st
from streamlit_app import api_client
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_mvp_style
from streamlit_app.components.feedback import feedback_widget
from streamlit_app.components.charts import health_gauge, kpi_bar_chart, weibull_curve

st.set_page_config(page_title="Analytics", layout="wide")
page_init()
apply_mvp_style()

st.title(t("analytics.title"))

@st.cache_data(ttl=120, show_spinner=False)
def _load_equipment_nodes():
    try:
        return api_client.list_nodes(node_type="EQUIPMENT")
    except Exception:
        return []

tab1, tab2, tab3 = st.tabs([t("analytics.tab_health"), t("analytics.tab_kpis"), t("analytics.tab_weibull")])

with tab1:
    st.subheader(t("analytics.asset_health"))
    try:
        nodes = _load_equipment_nodes()
        if nodes:
            eq_names = {n["node_id"]: f"{n['name']} ({n.get('tag', '')})" for n in nodes}
            selected_eq = st.selectbox(t("common.select_equipment"), list(eq_names.keys()), format_func=lambda x: eq_names[x], key="health_eq")
            selected_node = next(n for n in nodes if n["node_id"] == selected_eq)

            col1, col2 = st.columns(2)
            with col1:
                risk_class = st.selectbox(t("analytics.risk_class"), ["I_LOW", "II_MEDIUM", "III_HIGH", "IV_CRITICAL"], key="health_rc")
                backlog_hours = st.number_input(t("analytics.pending_backlog"), 0.0, 1000.0, 50.0, key="health_bl")
                fm_total = st.number_input(t("analytics.total_fm"), 0, 100, 10, key="health_fm")
                fm_strategy = st.number_input(t("analytics.fm_with_strategy"), 0, 100, 8, key="health_fms")

            if st.button(t("analytics.calculate_health")):
                result = api_client.calculate_health_score({
                    "node_id": selected_eq,
                    "plant_id": selected_node.get("plant_id", "OCP-JFC1"),
                    "equipment_tag": selected_node.get("tag", ""),
                    "risk_class": risk_class,
                    "pending_backlog_hours": backlog_hours,
                    "total_failure_modes": fm_total,
                    "fm_with_strategy": fm_strategy,
                })
                with col2:
                    st.plotly_chart(health_gauge(result["composite_score"], f"Health: {result['health_class']}"), width="stretch")
                    st.write(t("analytics.recommendations"))
                    for rec in result.get("recommendations", []):
                        st.write(f"- {rec}")
    except Exception as e:
        st.warning(f"Cannot connect to API: {e}")

with tab2:
    st.subheader(t("analytics.kpi_calculator"))
    col1, col2 = st.columns(2)
    with col1:
        plant_id = st.text_input(t("common.plant_id"), "OCP-JFC1", key="kpi_plant")
        total_hours = st.number_input(t("analytics.total_period_hours"), 0.0, 100000.0, 8760.0, key="kpi_hours")
        downtime_hours = st.number_input(t("analytics.total_downtime_hours"), 0.0, 10000.0, 120.0, key="kpi_dt")

    if st.button(t("analytics.calculate_kpis")):
        result = api_client.calculate_kpis({
            "plant_id": plant_id,
            "total_period_hours": total_hours,
            "total_downtime_hours": downtime_hours,
        })
        with col2:
            if result:
                st.plotly_chart(kpi_bar_chart(result, "KPI Results"), width="stretch")
                for k, v in result.items():
                    if v is not None:
                        st.metric(k.replace("_", " ").title(), f"{v:.1f}")

with tab3:
    st.subheader(t("analytics.weibull_title"))
    intervals_str = st.text_input(t("analytics.failure_intervals"), "120, 180, 95, 210, 150", key="weibull_int")
    current_age = st.number_input(t("analytics.current_age"), 0.0, 10000.0, 100.0, key="weibull_age")

    if st.button(t("analytics.fit_weibull")):
        intervals = [float(x.strip()) for x in intervals_str.split(",") if x.strip()]
        if len(intervals) >= 3:
            params = api_client.fit_weibull(intervals)
            col1, col2 = st.columns(2)
            col1.metric(t("analytics.beta_shape"), f"{params['beta']:.3f}")
            col1.metric(t("analytics.eta_scale"), f"{params['eta']:.1f}")
            col2.metric(t("analytics.r_squared"), f"{params['r_squared']:.4f}")

            # Generate reliability curve
            times = [i * 10 for i in range(1, 101)]
            from tools.engines.weibull_engine import WeibullEngine
            from tools.models.schemas import WeibullParameters
            wp = WeibullParameters(beta=params["beta"], eta=params["eta"], gamma=params.get("gamma", 0), r_squared=params["r_squared"])
            rels = [WeibullEngine.reliability(t_val, wp) for t_val in times]
            st.plotly_chart(weibull_curve(times, rels, "Reliability R(t) vs Time"), width="stretch")
        else:
            st.error(t("analytics.need_intervals"))

feedback_widget("analytics")
