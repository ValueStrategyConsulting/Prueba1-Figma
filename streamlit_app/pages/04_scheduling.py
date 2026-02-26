"""Page 12: Weekly Scheduling — Phase 4B Scheduling Engine."""

import logging
logger = logging.getLogger("04_scheduling")

import streamlit as st
from streamlit_app import api_client
from streamlit_app.components.charts import gantt_chart, schedule_utilization_chart
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_mvp_style
from streamlit_app.components.feedback import feedback_widget

st.set_page_config(page_title="Weekly Scheduling", page_icon="📅", layout="wide")
page_init()
apply_mvp_style()

st.title(t("scheduling.title"))
st.markdown(t("scheduling.subtitle"))

@st.cache_data(ttl=120, show_spinner=False)
def _load_programs(plant_id):
    try:
        return api_client.list_programs(plant_id=plant_id)
    except Exception:
        return []

tab_programs, tab_resources, tab_gantt = st.tabs([t("scheduling.tab_programs"), t("scheduling.tab_resources"), t("scheduling.tab_gantt")])

with tab_programs:
    st.subheader(t("scheduling.weekly_programs"))

    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        plant_id = st.text_input(t("common.plant_id"), value="OCP-JFC1")
    with col_c2:
        week_num = st.number_input(t("scheduling.week_number"), min_value=1, max_value=53, value=1)
    with col_c3:
        year = st.number_input(t("scheduling.year"), min_value=2020, max_value=2030, value=2025)

    if st.button(t("scheduling.create_program"), type="primary"):
        try:
            result = api_client.create_program(plant_id, week_num, year)
            st.session_state["last_program"] = result
            st.success(f"Program created: {result.get('program_id', '')}")
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()
    st.subheader(t("scheduling.existing_programs"))

    programs = _load_programs(plant_id=plant_id)

    if programs:
        for prog in programs:
            col_p1, col_p2, col_p3, col_p4 = st.columns([3, 1, 1, 2])
            col_p1.write(f"**{prog.get('program_id', '')[:12]}...** — W{prog.get('week_number')}/{prog.get('year')}")
            col_p2.write(prog.get("status", ""))
            col_p3.write(f"{prog.get('total_hours', 0):.0f}h")
            with col_p4:
                pid = prog.get("program_id", "")
                if prog.get("status") == "DRAFT":
                    if st.button(t("scheduling.finalize"), key=f"fin-{pid}"):
                        try:
                            r = api_client.finalize_program(pid)
                            st.success(r.get("message", ""))
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
    else:
        st.info(t("scheduling.no_programs"))

with tab_resources:
    st.subheader(t("scheduling.resource_utilization"))

    prog = st.session_state.get("last_program")
    if prog:
        pid = prog.get("program_id", "")
        try:
            details = api_client.get_program(pid)
        except Exception as e:
            logger.exception("Unexpected error")
            details = None

        if details:
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric(t("scheduling.total_hours"), f"{details.get('total_hours', 0):.0f}h")
            col_m2.metric(t("backlog.work_packages"), len(details.get("work_packages") or []))
            conflicts = details.get("conflicts") or []
            col_m3.metric(t("scheduling.conflicts"), len(conflicts))

            slots = details.get("resource_slots") or []
            if slots:
                st.plotly_chart(schedule_utilization_chart(
                    [{"date": s.get("slot_date", ""), "utilization_percent": s.get("utilization_pct", 0)} for s in slots]
                ), width="stretch")

            if conflicts:
                st.subheader(t("scheduling.conflicts"))
                for c in conflicts:
                    st.warning(f"**{c.get('shift', '')}** — {c.get('description', '')}")
    else:
        st.info(t("scheduling.create_first_resources"))

with tab_gantt:
    st.subheader(t("scheduling.gantt_chart"))

    prog = st.session_state.get("last_program")
    if prog:
        pid = prog.get("program_id", "")
        try:
            gantt_data = api_client.get_gantt(pid)
        except Exception as e:
            logger.exception("Unexpected error")
            gantt_data = None

        if gantt_data:
            st.plotly_chart(gantt_chart(gantt_data), width="stretch")

            st.download_button(
                label=t("scheduling.download_excel"),
                data=b"",  # Placeholder — actual download via API
                file_name=f"gantt_{pid}.xlsx",
                disabled=True,
                help="Use the API endpoint /scheduling/programs/{id}/gantt/export",
            )
        else:
            st.info(t("scheduling.no_gantt"))
    else:
        st.info(t("scheduling.create_first_gantt"))

feedback_widget("scheduling")
