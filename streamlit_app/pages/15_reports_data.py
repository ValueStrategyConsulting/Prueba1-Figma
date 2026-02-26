"""Page 15: Reports & Data Management — report generation, import, export."""

import logging
logger = logging.getLogger("15_reports_data")

import streamlit as st
from streamlit_app import api_client
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_mvp_style
from streamlit_app.components.feedback import feedback_widget

st.set_page_config(page_title="Reports & Data", layout="wide")
page_init()
apply_mvp_style()

st.title(t("reports.title"))

plant_id = st.text_input(t("common.plant_id"), value="OCP-JFC")

@st.cache_data(ttl=120, show_spinner=False)
def _load_reports(plant_id, report_type=None):
    try:
        return api_client.list_reports(plant_id, report_type)
    except Exception:
        return []

tab1, tab2, tab3, tab4 = st.tabs([
    t("reports.tab_generate"), t("reports.tab_history"), t("reports.tab_import"), t("reports.tab_export"),
])

with tab1:
    st.subheader(t("reports.generate_report"))
    report_type = st.selectbox(t("reports.report_type"), [t("reports.weekly"), t("reports.monthly"), t("reports.quarterly")])

    if report_type == t("reports.weekly"):
        col1, col2 = st.columns(2)
        week = col1.number_input(t("reports.week_number"), 1, 52, 1)
        year = col2.number_input(t("reports.year"), 2020, 2030, 2025)
        safety = st.number_input(t("reports.safety_incidents"), 0, 100, 0)
        backlog = st.number_input(t("reports.backlog_hours"), 0.0, 100000.0, 0.0)
        if st.button(t("reports.generate_weekly")):
            try:
                result = api_client.generate_weekly_report(plant_id, week, year, {
                    "safety_incidents": safety, "backlog_hours": backlog,
                })
                st.success(t("reports.weekly_generated"))
                st.json(result)
            except Exception as e:
                st.error(f"Failed: {e}")

    elif report_type == t("reports.monthly"):
        col1, col2 = st.columns(2)
        month = col1.number_input(t("reports.month"), 1, 12, 1)
        year = col2.number_input(t("reports.year"), 2020, 2030, 2025)
        if st.button(t("reports.generate_monthly")):
            try:
                result = api_client.generate_monthly_report(plant_id, month, year)
                st.success(t("reports.monthly_generated"))
                st.json(result)
            except Exception as e:
                st.error(f"Failed: {e}")

    else:
        col1, col2 = st.columns(2)
        quarter = col1.number_input(t("reports.quarter"), 1, 4, 1)
        year = col2.number_input(t("reports.year"), 2020, 2030, 2025)
        if st.button(t("reports.generate_quarterly")):
            try:
                result = api_client.generate_quarterly_report(plant_id, quarter, year)
                st.success(t("reports.quarterly_generated"))
                st.json(result)
            except Exception as e:
                st.error(f"Failed: {e}")

with tab2:
    st.subheader(t("reports.report_history"))
    type_filter = st.selectbox(t("reports.filter_type"), ["All", "WEEKLY_MAINTENANCE", "MONTHLY_KPI", "QUARTERLY_REVIEW"])
    try:
        rt = None if type_filter == "All" else type_filter
        reports = _load_reports(plant_id, rt)
        if reports:
            for r in reports:
                with st.expander(f"{r.get('report_type')} — {r.get('generated_at', '')[:10]}"):
                    st.write(f"**Report ID:** {r.get('report_id')}")
                    st.write(f"**Period:** {r.get('period_start')} to {r.get('period_end')}")
                    if st.button("View", key=r.get("report_id")):
                        detail = api_client.get_report(r["report_id"])
                        st.json(detail)
        else:
            st.info(t("reports.no_reports"))
    except Exception as e:
        logger.exception("Unexpected error")
        st.warning(t("common.could_not_connect"))

with tab3:
    st.subheader(t("reports.data_import"))
    import_type = st.selectbox(t("reports.import_type"), [
        "EQUIPMENT_HIERARCHY", "FAILURE_HISTORY", "MAINTENANCE_PLAN",
    ])
    st.info(t("reports.upload_info"))
    uploaded = st.file_uploader(t("reports.upload_file"), type=["csv", "xlsx"])
    sample_data = st.text_area(t("reports.paste_json"), value='[{"equipment_id": "EQ-001", "description": "Pump", "equipment_type": "ROTATING"}]')
    if st.button(t("reports.validate_import")):
        try:
            import json
            rows = json.loads(sample_data)
            result = api_client.validate_import(import_type, rows)
            col1, col2, col3 = st.columns(3)
            col1.metric(t("reports.total_rows"), result.get("total_rows", 0))
            col2.metric(t("reports.valid_rows"), result.get("valid_rows", 0))
            col3.metric(t("reports.error_rows"), result.get("error_rows", 0))
            if result.get("errors"):
                st.warning(t("reports.validation_errors"))
                for err in result["errors"][:10]:
                    st.write(f"  Row {err.get('row')}, Column '{err.get('column')}': {err.get('message')}")
        except Exception as e:
            st.error(f"Validation failed: {e}")

with tab4:
    st.subheader(t("reports.data_export"))
    export_type = st.selectbox(t("reports.export_type"), ["equipment", "kpis", "schedule", "report"])
    if st.button(t("reports.prepare_export")):
        try:
            result = api_client.export_data(export_type, {})
            st.success(f"Export prepared with {len(result.get('sheets', []))} sheet(s)")
            for sheet in result.get("sheets", []):
                st.write(f"**{sheet.get('name')}**: {len(sheet.get('rows', []))} rows")
                if sheet.get("headers"):
                    st.write(f"Headers: {', '.join(sheet['headers'])}")
        except Exception as e:
            st.error(f"Export failed: {e}")

feedback_widget("reports_data")
