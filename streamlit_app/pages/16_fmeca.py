"""FMECA Analysis — Phase 7 Streamlit page (R8 Style).

Provides:
- FMECA Worksheets: Create worksheets, view stage progress, run decisions
- RPN Calculator: Interactive S x O x D sliders with color-coded result
- Analysis Summary: Strategy distribution, RPN distribution, top risks
"""

import logging
logger = logging.getLogger("16_fmeca")

import html as _html
import pandas as pd
import streamlit as st
from streamlit_app import api_client
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_style, apply_hierarchy_style, apply_r8_module_style
from streamlit_app.components.feedback import feedback_widget
from streamlit_app.components.tree_panel import (
    build_tree, init_tree_state, render_tree_panel,
    render_breadcrumb_bar, render_node_header,
)

st.set_page_config(page_title="FMECA Analysis", page_icon=":bar_chart:", layout="wide")
page_init()
apply_style()
apply_hierarchy_style()
apply_r8_module_style()

# Local engine imports for RPN calculator (standalone, no API needed)
from tools.engines.fmeca_engine import FMECAEngine
from tools.models.schemas import RPNCategory

# ── Session state ─────────────────────────────────────────────────────────────

init_tree_state(key_prefix="fmeca")

@st.cache_data(ttl=300, show_spinner=False)
def _load_plants():
    try:
        return api_client.list_plants()
    except Exception:
        return []

@st.cache_data(ttl=120, show_spinner=False)
def _load_nodes(plant_id):
    return api_client.list_nodes(plant_id=plant_id)

st.title(t("fmeca.title"))

# ── Load plant & nodes ────────────────────────────────────────────────────────

plants = _load_plants()
if not plants:
    st.info(t("hierarchy.no_plants"))
    st.stop()

plant_names = {p["plant_id"]: p["name"] for p in plants}
selected_plant = st.selectbox(
    t("hierarchy.select_plant"),
    list(plant_names.keys()),
    format_func=lambda x: plant_names[x],
    key="fmeca_plant_select",
)

nodes = _load_nodes(plant_id=selected_plant)
node_map, children_map, root_ids = build_tree(nodes)

# ── Top-level tabs ────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs([t("fmeca.tab_worksheets"), t("fmeca.tab_rpn"), t("fmeca.tab_summary")])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: FMECA Worksheets (R8 split-pane)
# ══════════════════════════════════════════════════════════════════════════════

with tab1:
    if not nodes:
        st.info(t("hierarchy.no_nodes"))
    else:
        left, right = st.columns([1, 3])

        with left:
            render_tree_panel(nodes, node_map, children_map, root_ids, key_prefix="fmeca")

        with right:
            sel_id = st.session_state.get("fmeca_selected_node_id")

            if sel_id and sel_id in node_map:
                node = node_map[sel_id]
                render_breadcrumb_bar(sel_id, node_map)
                render_node_header(node)

            # ── Create / Load worksheet ───────────────────────────────
            st.markdown("<div class='r8-form-title'>FMECA Worksheet</div>", unsafe_allow_html=True)

            create_col1, create_col2 = st.columns(2)
            with create_col1:
                eq_id = st.text_input(
                    t("common.equipment_id"),
                    value=sel_id if sel_id else "EQ-001",
                    key="fmeca_eq_id",
                )
                eq_tag = st.text_input(t("fmeca.equipment_tag"), value="", key="fmeca_eq_tag")
            with create_col2:
                eq_name_val = ""
                if sel_id and sel_id in node_map:
                    eq_name_val = node_map[sel_id].get("name", "")
                eq_name = st.text_input(t("fmeca.equipment_name"), value=eq_name_val, key="fmeca_eq_name")
                analyst = st.text_input(t("fmeca.analyst"), value="", key="fmeca_analyst")

            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button(t("fmeca.create_ws_btn"), key="btn_create_ws"):
                    try:
                        result = api_client.create_fmeca_worksheet({
                            "equipment_id": eq_id,
                            "equipment_tag": eq_tag,
                            "equipment_name": eq_name,
                            "analyst": analyst,
                        })
                        st.session_state["fmeca_worksheet_id"] = result["worksheet_id"]
                        st.success(f"Worksheet {result['worksheet_id']} created")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
            with bc2:
                ws_id_input = st.text_input("Load Worksheet ID", key="fmeca_load_id")
                if ws_id_input:
                    st.session_state["fmeca_worksheet_id"] = ws_id_input

            # ── Display worksheet ─────────────────────────────────────
            ws_id = st.session_state.get("fmeca_worksheet_id")

            if ws_id:
                try:
                    ws_data = api_client.get_fmeca_worksheet(ws_id)
                except Exception as e:
                    logger.exception("Unexpected error")
                    ws_data = None

                if ws_data:
                    st.divider()
                    st.markdown(f"<div class='r8-form-title'>Worksheet: {_html.escape(str(ws_data['worksheet_id']))}</div>", unsafe_allow_html=True)

                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("Status", ws_data.get("status", ""))
                    mc2.metric(t("fmeca.current_stage"), ws_data.get("current_stage", ""))
                    mc3.metric(t("fmeca.rows"), len(ws_data.get("rows", [])))

                    # ── Rows grid ─────────────────────────────────────
                    rows = ws_data.get("rows") or []
                    if rows:
                        rows_display = []
                        for r in rows:
                            rows_display.append({
                                "ID": r.get("row_id", ""),
                                "Function": str(r.get("function_description", ""))[:30],
                                "Failure Mode": str(r.get("failure_mode", ""))[:30],
                                "S": r.get("severity", ""),
                                "O": r.get("occurrence", ""),
                                "D": r.get("detection", ""),
                                "RPN": r.get("rpn", ""),
                                "Category": r.get("rpn_category", ""),
                                "Strategy": r.get("strategy_type") or "\u2014",
                            })
                        st.dataframe(pd.DataFrame(rows_display), use_container_width=True, hide_index=True)

                    # ── Add row form ──────────────────────────────────
                    with st.expander(t("fmeca.add_row"), expanded=False):
                        # Use local engine for row creation, then persist
                        with st.form("add_fmeca_row_form", clear_on_submit=True):
                            r1, r2 = st.columns(2)
                            with r1:
                                func_desc = st.text_input(t("fmeca.function_desc"))
                                func_fail = st.text_input(t("fmeca.functional_failure"))
                                fail_mode = st.text_input(t("fmeca.failure_mode"))
                            with r2:
                                fail_effect = st.text_input(t("fmeca.failure_effect"))
                                fail_cons = st.selectbox(t("fmeca.failure_consequence"), [
                                    "", "HIDDEN_SAFETY", "HIDDEN_NONSAFETY",
                                    "EVIDENT_SAFETY", "EVIDENT_ENVIRONMENTAL",
                                    "EVIDENT_OPERATIONAL", "EVIDENT_NONOPERATIONAL",
                                ])

                            s1, s2, s3 = st.columns(3)
                            severity = s1.slider(t("fmeca.severity"), 1, 10, 5, key="fmeca_add_sev")
                            occurrence = s2.slider(t("fmeca.occurrence"), 1, 10, 5, key="fmeca_add_occ")
                            detection = s3.slider(t("fmeca.detection"), 1, 10, 5, key="fmeca_add_det")

                            if st.form_submit_button(t("fmeca.add_row_btn")):
                                if func_desc and fail_mode:
                                    # Use local engine to compute RPN
                                    rpn_result = FMECAEngine.calculate_rpn(severity, occurrence, detection)
                                    st.success(f"Row added (RPN={rpn_result.rpn}, Category={rpn_result.category.value})")
                                    st.info("Note: Row persistence via API to be fully integrated.")

                    # ── Stage management ──────────────────────────────
                    st.divider()
                    stage_col1, stage_col2 = st.columns(2)
                    with stage_col1:
                        if st.button("Run Stage 4 Decisions", key="btn_run_stage4_api"):
                            try:
                                result = api_client.run_fmeca_decisions(ws_id)
                                st.success(f"Decisions run \u2014 {result.get('rows_processed', 0)} rows processed")
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                else:
                    st.warning(f"Worksheet '{ws_id}' not found.")
            else:
                # Fallback: use local engine (session state)
                if "fmeca_worksheet" not in st.session_state:
                    st.info(t("fmeca.create_ws_first"))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: RPN Calculator (kept from original with styling)
# ══════════════════════════════════════════════════════════════════════════════

with tab2:
    st.subheader(t("fmeca.rpn_calculator"))
    st.markdown(t("fmeca.rpn_formula"))

    c1, c2, c3 = st.columns(3)
    s = c1.slider(t("fmeca.severity_s"), 1, 10, 5, key="rpn_s")
    o = c2.slider(t("fmeca.occurrence_o"), 1, 10, 5, key="rpn_o")
    d = c3.slider(t("fmeca.detection_d"), 1, 10, 5, key="rpn_d")

    result = FMECAEngine.calculate_rpn(s, o, d)

    color_map = {
        RPNCategory.LOW: "green",
        RPNCategory.MEDIUM: "orange",
        RPNCategory.HIGH: "red",
        RPNCategory.CRITICAL: "darkred",
    }
    color = color_map.get(result.category, "gray")

    st.markdown(f"### RPN: <span style='color:{color}; font-size:2em;'>{result.rpn}</span>", unsafe_allow_html=True)
    st.markdown(f"**Category:** {result.category.value}")

    st.divider()
    st.markdown(t("fmeca.rpn_table"))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: Analysis Summary (API-driven)
# ══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.subheader(t("fmeca.analysis_summary"))

    ws_id = st.session_state.get("fmeca_worksheet_id")
    if ws_id:
        try:
            summary = api_client.get_fmeca_summary(ws_id)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t("fmeca.total_rows_metric"), summary.get("total_rows", 0))
            m2.metric(t("fmeca.avg_rpn"), summary.get("avg_rpn", 0))
            m3.metric(t("fmeca.high_critical"), summary.get("high_critical_count", 0))
            m4.metric(t("fmeca.strategies_assigned"), sum(summary.get("strategy_distribution", {}).values()))

            rpn_dist = summary.get("rpn_distribution", {})
            if rpn_dist:
                st.subheader(t("fmeca.rpn_distribution"))
                rpn_df = pd.DataFrame([{"Category": k, "Count": v} for k, v in rpn_dist.items()])
                st.bar_chart(rpn_df.set_index("Category"))

            strat_dist = summary.get("strategy_distribution", {})
            if strat_dist:
                st.subheader(t("fmeca.strategy_distribution"))
                strat_df = pd.DataFrame([{"Strategy": k, "Count": v} for k, v in strat_dist.items()])
                st.bar_chart(strat_df.set_index("Strategy"))

            top_risks = summary.get("top_risks", [])
            if top_risks:
                st.subheader(t("fmeca.top_risks"))
                st.dataframe(pd.DataFrame(top_risks), use_container_width=True, hide_index=True)

            recommendations = summary.get("recommendations", [])
            if recommendations:
                st.subheader(t("fmeca.recommendations"))
                for rec in recommendations:
                    st.warning(rec)
        except Exception as e:
            logger.exception("Unexpected error")
            st.info("No summary available. Create a worksheet and add rows first.")
    else:
        # Fallback to local engine
        if "fmeca_worksheet" in st.session_state:
            ws = st.session_state["fmeca_worksheet"]
            summary = FMECAEngine.generate_summary(ws)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t("fmeca.total_rows_metric"), summary.total_rows)
            m2.metric(t("fmeca.avg_rpn"), summary.avg_rpn)
            m3.metric(t("fmeca.high_critical"), summary.high_critical_count)
            m4.metric(t("fmeca.strategies_assigned"), sum(summary.strategy_distribution.values()))

            if summary.rpn_distribution:
                st.subheader(t("fmeca.rpn_distribution"))
                rpn_df = pd.DataFrame([{"Category": k, "Count": v} for k, v in summary.rpn_distribution.items()])
                st.bar_chart(rpn_df.set_index("Category"))

            if summary.strategy_distribution:
                st.subheader(t("fmeca.strategy_distribution"))
                strat_df = pd.DataFrame([{"Strategy": k, "Count": v} for k, v in summary.strategy_distribution.items()])
                st.bar_chart(strat_df.set_index("Strategy"))

            if summary.top_risks:
                st.subheader(t("fmeca.top_risks"))
                st.dataframe(pd.DataFrame(summary.top_risks), use_container_width=True, hide_index=True)

            if summary.recommendations:
                st.subheader(t("fmeca.recommendations"))
                for rec in summary.recommendations:
                    st.warning(rec)
        else:
            st.info(t("fmeca.create_ws_first"))

feedback_widget("fmeca")
