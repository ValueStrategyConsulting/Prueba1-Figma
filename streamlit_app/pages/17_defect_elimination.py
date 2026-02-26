"""Page 17: Defect Elimination & Root Cause Analysis — Phase 8."""

import logging
logger = logging.getLogger("17_defect_elimination")

import streamlit as st
from datetime import date, timedelta
from streamlit_app import api_client
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_mvp_style
from streamlit_app.components.feedback import feedback_widget
from streamlit_app.components.charts import rca_level_distribution, planning_kpi_radar, de_program_gauge

st.set_page_config(page_title="Defect Elimination", page_icon="🔍", layout="wide")
page_init()
apply_mvp_style()

st.title(t("defect_elimination.title"))
st.markdown(t("defect_elimination.subtitle"))

@st.cache_data(ttl=120, show_spinner=False)
def _load_rca_summary(plant_id):
    try:
        return api_client.get_rca_summary(plant_id)
    except Exception:
        return {}

@st.cache_data(ttl=120, show_spinner=False)
def _load_rcas(plant_id):
    try:
        return api_client.list_rcas(plant_id=plant_id)
    except Exception:
        return []

tab_rca, tab_5w2h, tab_pkpi, tab_dekpi = st.tabs([
    t("defect_elimination.tab_rca"), t("defect_elimination.tab_5w2h"),
    t("defect_elimination.tab_planning_kpi"), t("defect_elimination.tab_de_kpi"),
])

# -- RCA Analyses --------------------------------------------------------------

with tab_rca:
    st.subheader(t("defect_elimination.rca_title"))
    st.markdown(t("defect_elimination.rca_desc"))

    col_create, col_list = st.columns([1, 2])

    with col_create:
        st.markdown(t("defect_elimination.new_rca"))
        plant_id = st.text_input(t("common.plant_id"), value="OCP-JFC1", key="rca_plant")
        event_desc = st.text_area(t("defect_elimination.event_description"), key="rca_event", height=100,
                                  placeholder="Describe the failure event...")
        equipment_id = st.text_input(t("defect_elimination.equipment_id_optional"), key="rca_eq")

        c1, c2 = st.columns(2)
        with c1:
            consequence = st.slider(t("defect_elimination.max_consequence"), 1, 5, 3, key="rca_cons")
        with c2:
            frequency = st.slider(t("defect_elimination.frequency"), 1, 5, 3, key="rca_freq")

        team = st.text_input(t("defect_elimination.team_members"), key="rca_team",
                             placeholder="J. Garcia, M. Benali, S. Dupont")

        if st.button(t("defect_elimination.create_rca"), type="primary", key="rca_create"):
            if not event_desc:
                st.warning(t("defect_elimination.describe_event"))
            else:
                try:
                    result = api_client.create_rca({
                        "event_description": event_desc,
                        "plant_id": plant_id,
                        "equipment_id": equipment_id or None,
                        "max_consequence": consequence,
                        "frequency": frequency,
                        "team_members": [tm.strip() for tm in team.split(",") if tm.strip()] if team else [],
                    })
                    st.success(f"RCA created: {result['analysis_id']}")
                    st.info(f"Level: **{result['level']}** — {result['team_requirements']['description']}")
                except Exception as e:
                    st.error(str(e))

    with col_list:
        st.markdown(t("defect_elimination.active_rcas"))
        try:
            summary = _load_rca_summary(plant_id)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t("defect_elimination.total"), summary.get("total", 0))
            m2.metric(t("defect_elimination.open"), summary.get("open", 0))
            m3.metric(t("defect_elimination.under_investigation"), summary.get("under_investigation", 0))
            m4.metric(t("defect_elimination.completed"), summary.get("completed", 0))

            analyses = _load_rcas(plant_id=plant_id)
            if analyses:
                st.dataframe([{
                    "ID": a["analysis_id"][:8] + "...",
                    "Event": a["event_description"][:50],
                    "Level": a["level"],
                    "Status": a["status"],
                    "Created": a.get("created_at", "")[:10],
                } for a in analyses], width="stretch")
                st.plotly_chart(rca_level_distribution(analyses), width="stretch")
            else:
                st.info(t("defect_elimination.no_rcas"))
        except Exception as e:
            st.warning(f"API not available: {e}")
            st.info("Start the API server with: `uvicorn api.main:app --reload`")


# -- 5W+2H Quick Analysis -----------------------------------------------------

with tab_5w2h:
    st.subheader(t("defect_elimination.tab_5w2h"))
    st.markdown("Level 1 structured analysis for simple events (REF-15 \u00a75.2).")

    analysis_id = st.text_input(t("defect_elimination.tab_rca") + " ID", key="5w2h_id",
                                placeholder="Enter existing RCA analysis ID")

    col1, col2 = st.columns(2)
    with col1:
        what = st.text_area("WHAT (Problem + Goal)", key="5w2h_what", height=80)
        when = st.text_area("WHEN (Timing + Schedule)", key="5w2h_when", height=80)
        where = st.text_area("WHERE (Location + Implementation)", key="5w2h_where", height=80)
        who = st.text_area("WHO (Skills + Responsible)", key="5w2h_who", height=80)
    with col2:
        why = st.text_area("WHY (Traceability + Justification)", key="5w2h_why", height=80)
        how = st.text_area("HOW (Manifestation + Approach)", key="5w2h_how", height=80)
        how_much = st.text_area("HOW MUCH (Quantification + Cost)", key="5w2h_howmuch", height=80)

    if st.button("Submit 5W+2H Analysis", type="primary", key="5w2h_submit"):
        if not analysis_id:
            st.warning("Please enter an RCA Analysis ID.")
        elif not what:
            st.warning("At minimum, describe WHAT happened.")
        else:
            try:
                result = api_client.run_5w2h(analysis_id, {
                    "what": what, "when": when, "where": where,
                    "who": who, "why": why, "how": how, "how_much": how_much,
                })
                st.success("5W+2H analysis saved successfully.")
                report = result.get("5w2h", {}).get("report", "")
                if report:
                    st.code(report, language=None)
            except Exception as e:
                st.error(str(e))


# -- Planning KPIs (11) -------------------------------------------------------

with tab_pkpi:
    st.subheader(t("defect_elimination.tab_planning_kpi"))
    st.markdown("GFSN REF-14 \u00a78 \u2014 Track planning performance with targets.")

    with st.expander("Calculate KPIs", expanded=True):
        pkpi_plant = st.text_input(t("common.plant_id"), value="OCP-JFC1", key="pkpi_plant")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            wo_planned = st.number_input("WOs Planned", value=100, min_value=0, key="pkpi_planned")
            wo_completed = st.number_input("WOs Completed", value=92, min_value=0, key="pkpi_completed")
            manhours_planned = st.number_input("Man-hours Planned", value=800.0, min_value=0.0, key="pkpi_mh_p")
        with c2:
            manhours_actual = st.number_input("Man-hours Actual", value=780.0, min_value=0.0, key="pkpi_mh_a")
            pm_planned = st.number_input("PM Planned", value=50, min_value=0, key="pkpi_pm_p")
            pm_executed = st.number_input("PM Executed", value=48, min_value=0, key="pkpi_pm_e")
        with c3:
            backlog_hours = st.number_input("Backlog Hours", value=300.0, min_value=0.0, key="pkpi_bl")
            weekly_cap = st.number_input("Weekly Capacity (hrs)", value=200.0, min_value=1.0, key="pkpi_wc")
            corrective = st.number_input("Corrective WOs", value=15, min_value=0, key="pkpi_corr")
        with c4:
            proactive = st.number_input("Proactive WOs", value=75, min_value=0, key="pkpi_pro")
            planned_wo = st.number_input("Planned WOs", value=88, min_value=0, key="pkpi_pwo")
            release_days = st.number_input("Release Horizon (days)", value=5, min_value=0, key="pkpi_rh")

        c5, c6 = st.columns(2)
        with c5:
            pending_notices = st.number_input("Pending Notices", value=12, min_value=0, key="pkpi_pn")
            total_notices = st.number_input("Total Notices", value=100, min_value=0, key="pkpi_tn")
        with c6:
            sched_cap_hrs = st.number_input("Scheduled Capacity (hrs)", value=170.0, min_value=0.0, key="pkpi_sc")
            total_cap_hrs = st.number_input("Total Capacity (hrs)", value=200.0, min_value=0.0, key="pkpi_tc")

        sched_planned = st.number_input("Schedule Compliance - Planned", value=90, min_value=0, key="pkpi_sp")
        sched_executed = st.number_input("Schedule Compliance - Executed", value=82, min_value=0, key="pkpi_se")

        if st.button("Calculate Planning KPIs", type="primary", key="pkpi_calc"):
            today = date.today()
            try:
                result = api_client.calculate_planning_kpis({
                    "plant_id": pkpi_plant,
                    "period_start": (today - timedelta(days=7)).isoformat(),
                    "period_end": today.isoformat(),
                    "wo_planned": wo_planned, "wo_completed": wo_completed,
                    "manhours_planned": manhours_planned, "manhours_actual": manhours_actual,
                    "pm_planned": pm_planned, "pm_executed": pm_executed,
                    "backlog_hours": backlog_hours, "weekly_capacity_hours": weekly_cap,
                    "corrective_count": corrective, "total_wo": wo_planned,
                    "schedule_compliance_planned": sched_planned,
                    "schedule_compliance_executed": sched_executed,
                    "release_horizon_days": release_days,
                    "pending_notices": pending_notices, "total_notices": total_notices,
                    "scheduled_capacity_hours": sched_cap_hrs,
                    "total_capacity_hours": total_cap_hrs,
                    "proactive_wo": proactive, "planned_wo": planned_wo,
                })
                st.success(f"Overall Health: **{result.get('overall_health', 'UNKNOWN')}** — "
                           f"{result.get('on_target_count', 0)}/11 on target")

                kpis = result.get("kpis", [])
                if kpis:
                    rows = []
                    for k in kpis:
                        status_icon = "✅" if k["status"] == "ON_TARGET" else "⚠️"
                        rows.append({
                            "Status": status_icon,
                            "KPI": k["name"].replace("_", " ").title(),
                            "Value": f"{k['value']:.1f}" if k["value"] is not None else "N/A",
                            "Target": f"{k['target']:.1f}",
                            "Unit": k.get("unit", "%"),
                        })
                    st.dataframe(rows, width="stretch")
                    st.plotly_chart(planning_kpi_radar(kpis), width="stretch")
            except Exception as e:
                st.error(str(e))


# -- DE KPIs (5) ---------------------------------------------------------------

with tab_dekpi:
    st.subheader(t("defect_elimination.tab_de_kpi"))
    st.markdown("GFSN REF-15 \u00a77.2 \u2014 Track DE program effectiveness.")

    with st.expander("Calculate DE KPIs", expanded=True):
        de_plant = st.text_input(t("common.plant_id"), value="OCP-JFC1", key="de_plant")

        c1, c2, c3 = st.columns(3)
        with c1:
            ev_reported = st.number_input("Events Reported", value=18, min_value=0, key="de_er")
            ev_required = st.number_input("Events Required", value=20, min_value=0, key="de_eq")
            meet_held = st.number_input("Meetings Held", value=9, min_value=0, key="de_mh")
            meet_required = st.number_input("Meetings Required", value=10, min_value=0, key="de_mq")
        with c2:
            act_impl = st.number_input("Actions Implemented", value=14, min_value=0, key="de_ai")
            act_planned = st.number_input("Actions Planned", value=16, min_value=0, key="de_ap")
            savings_ach = st.number_input("Savings Achieved ($)", value=85000.0, min_value=0.0, key="de_sa")
            savings_tgt = st.number_input("Savings Target ($)", value=100000.0, min_value=0.0, key="de_st")
        with c3:
            fail_current = st.number_input("Failures (Current)", value=8, min_value=0, key="de_fc")
            fail_previous = st.number_input("Failures (Previous)", value=12, min_value=0, key="de_fp")

        if st.button("Calculate DE KPIs", type="primary", key="de_calc"):
            today = date.today()
            try:
                result = api_client.calculate_de_kpis_full({
                    "plant_id": de_plant,
                    "period_start": (today - timedelta(days=30)).isoformat(),
                    "period_end": today.isoformat(),
                    "events_reported": ev_reported, "events_required": ev_required,
                    "meetings_held": meet_held, "meetings_required": meet_required,
                    "actions_implemented": act_impl, "actions_planned": act_planned,
                    "savings_achieved": savings_ach, "savings_target": savings_tgt,
                    "failures_current": fail_current, "failures_previous": fail_previous,
                })
                kpi_data = result.get("kpis", {})
                health_data = result.get("health", {})

                st.success(f"Program Maturity: **{health_data.get('maturity_level', 'UNKNOWN')}** — "
                           f"Score: {health_data.get('program_score', 0):.0f}/100")
                st.plotly_chart(de_program_gauge(health_data.get('program_score', 0), health_data.get('maturity_level', '')), width="stretch")

                kpis = kpi_data.get("kpis", [])
                if kpis:
                    rows = []
                    for k in kpis:
                        status_icon = "✅" if k["status"] == "ON_TARGET" else "⚠️"
                        rows.append({
                            "Status": status_icon,
                            "KPI": k["name"].replace("_", " ").title(),
                            "Value": f"{k['value']:.1f}%" if k["value"] is not None else "N/A",
                            "Target": f"{k['target']:.0f}%",
                        })
                    st.dataframe(rows, width="stretch")

                # Show strengths and improvements
                strengths = health_data.get("strengths", [])
                improvements = health_data.get("improvement_areas", [])

                if strengths:
                    st.markdown("**Strengths:**")
                    for s in strengths:
                        st.markdown(f"- ✅ {s}")
                if improvements:
                    st.markdown("**Areas for Improvement:**")
                    for i in improvements:
                        st.markdown(f"- ⚠️ {i}")

            except Exception as e:
                st.error(str(e))

feedback_widget("defect_elimination")
