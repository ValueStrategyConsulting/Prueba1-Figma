"""Page 3: FMEA — Functions, Functional Failures & Failure Modes (R8 Style)."""

import logging
logger = logging.getLogger("09_fmea")

import pandas as pd
import streamlit as st
from streamlit_app import api_client
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_style, apply_hierarchy_style, apply_r8_module_style
from streamlit_app.components.feedback import feedback_widget
from streamlit_app.components.forms import MECHANISMS, FAILURE_CONSEQUENCES, STRATEGY_TYPES
from streamlit_app.components.tables import render_data_table
from streamlit_app.components.tree_panel import (
    build_tree, init_tree_state, render_tree_panel,
    render_breadcrumb_bar, render_node_header, render_info_card,
)

st.set_page_config(page_title="FMEA", layout="wide")
page_init()
apply_style()
apply_hierarchy_style()
apply_r8_module_style()

# ── Session state ─────────────────────────────────────────────────────────────

init_tree_state(key_prefix="fmea")

@st.cache_data(ttl=300, show_spinner=False)
def _load_plants():
    try:
        return api_client.list_plants()
    except Exception:
        return []

@st.cache_data(ttl=120, show_spinner=False)
def _load_nodes(plant_id):
    return api_client.list_nodes(plant_id=plant_id)

st.title(t("fmea.title"))

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
    key="fmea_plant_select",
)

nodes = _load_nodes(plant_id=selected_plant)
node_map, children_map, root_ids = build_tree(nodes)

# ── Top-level tabs ────────────────────────────────────────────────────────────

tab_functions, tab_validation, tab_rcm = st.tabs([
    t("fmea.tab_functions"),
    t("fmea.tab_validation"),
    t("fmea.tab_rcm"),
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: Functions & Functional Failures (R8 split-pane)
# ══════════════════════════════════════════════════════════════════════════════

with tab_functions:
    if not nodes:
        st.info(t("hierarchy.no_nodes"))
    else:
        left, right = st.columns([1, 3])

        with left:
            render_tree_panel(nodes, node_map, children_map, root_ids, key_prefix="fmea")

        with right:
            sel_id = st.session_state.get("fmea_selected_node_id")

            if not sel_id or sel_id not in node_map:
                st.markdown(
                    "<div class='empty-state'>"
                    "<div style='font-size:4em; opacity:0.3;'>\u2699\uFE0F</div>"
                    f"<h3>{t('fmea.select_node_first')}</h3>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                node = node_map[sel_id]
                render_breadcrumb_bar(sel_id, node_map)
                render_node_header(node)

                # ── Functions Grid ────────────────────────────────────────
                try:
                    functions = api_client.list_functions(node_id=sel_id)
                except Exception as e:
                    logger.exception("Unexpected error")
                    functions = []

                if not functions:
                    st.info(t("fmea.no_functions"))
                else:
                    # Build the combined functions + functional failures table
                    grid_rows = []
                    for i, func in enumerate(functions, 1):
                        try:
                            ffs = api_client.list_functional_failures(function_id=func["function_id"])
                        except Exception as e:
                            logger.exception("Unexpected error")
                            ffs = []

                        if ffs:
                            for ff in ffs:
                                grid_rows.append({
                                    t("fmea.function_number"): i,
                                    t("fmea.function_type"): func.get("function_type", ""),
                                    t("fmea.function_desc"): func.get("description", ""),
                                    t("fmea.ff_type"): ff.get("failure_type", ""),
                                    t("fmea.ff_description"): ff.get("description", ""),
                                })
                        else:
                            grid_rows.append({
                                t("fmea.function_number"): i,
                                t("fmea.function_type"): func.get("function_type", ""),
                                t("fmea.function_desc"): func.get("description", ""),
                                t("fmea.ff_type"): "\u2014",
                                t("fmea.ff_description"): "\u2014",
                            })

                    st.markdown(f"<div class='r8-form-title'>{t('fmea.functions_grid')}</div>", unsafe_allow_html=True)
                    st.dataframe(pd.DataFrame(grid_rows), use_container_width=True, hide_index=True)

                # ── Sub-tabs: Entity Details | Existing Tasks | Failure Modes ─
                sub_details, sub_tasks, sub_fms = st.tabs([
                    t("fmea.tab_entity_details"),
                    t("fmea.tab_existing_tasks"),
                    t("fmea.tab_failure_modes"),
                ])

                with sub_details:
                    col1, col2 = st.columns(2)
                    with col1:
                        render_info_card(t("hierarchy.identity"), {
                            t("hierarchy.node_id_label"): node.get("node_id", ""),
                            t("hierarchy.node_type_label"): node.get("node_type", ""),
                            t("hierarchy.code_label"): node.get("code", ""),
                            t("hierarchy.tag_label"): node.get("tag", ""),
                            t("hierarchy.criticality_label"): node.get("criticality", ""),
                        })
                    with col2:
                        render_info_card(t("hierarchy.sap_references"), {
                            t("hierarchy.sap_func_loc"): node.get("sap_func_loc", ""),
                            t("hierarchy.sap_equipment_nr"): node.get("sap_equipment_nr", ""),
                        })

                with sub_tasks:
                    # Show tasks linked to this node's failure modes
                    all_tasks = []
                    if functions:
                        for func in functions:
                            try:
                                ffs = api_client.list_functional_failures(function_id=func["function_id"])
                            except Exception as e:
                                logger.exception("Unexpected error")
                                ffs = []
                            for ff in ffs:
                                try:
                                    fms = api_client.list_failure_modes(functional_failure_id=ff["failure_id"])
                                except Exception as e:
                                    logger.exception("Unexpected error")
                                    fms = []
                                for fm in fms:
                                    try:
                                        tasks = api_client.list_tasks(failure_mode_id=fm["failure_mode_id"])
                                    except Exception as e:
                                        logger.exception("Unexpected error")
                                        tasks = []
                                    all_tasks.extend(tasks)

                    if all_tasks:
                        st.dataframe(
                            pd.DataFrame(all_tasks)[["task_id", "name", "task_type", "status"]],
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info(t("fmea.tab_existing_tasks") + ": " + t("common.no_data_available"))

                with sub_fms:
                    # Show all failure modes for this node
                    all_fms = []
                    if functions:
                        for func in functions:
                            try:
                                ffs = api_client.list_functional_failures(function_id=func["function_id"])
                            except Exception as e:
                                logger.exception("Unexpected error")
                                ffs = []
                            for ff in ffs:
                                try:
                                    fms = api_client.list_failure_modes(functional_failure_id=ff["failure_id"])
                                except Exception as e:
                                    logger.exception("Unexpected error")
                                    fms = []
                                all_fms.extend(fms)

                    if all_fms:
                        render_data_table(all_fms, key_columns=["failure_mode_id", "what", "mechanism", "cause", "strategy_type"])
                    else:
                        st.info(t("fmea.no_fm"))

                # ── CRUD: Add Function / Add FF / Add FM ─────────────────
                st.divider()
                crud_col1, crud_col2, crud_col3 = st.columns(3)

                with crud_col1:
                    with st.expander(t("fmea.add_function"), expanded=False):
                        with st.form("add_function_form", clear_on_submit=True):
                            func_type = st.selectbox(
                                t("fmea.function_type"),
                                ["PRIMARY", "SECONDARY", "PROTECTIVE"],
                                key="add_func_type",
                            )
                            func_desc = st.text_area(
                                t("fmea.function_desc"),
                                key="add_func_desc",
                            )
                            func_perf = st.text_input(
                                t("fmea.performance_standard"),
                                key="add_func_perf",
                            )
                            if st.form_submit_button(t("fmea.add_function")):
                                if func_desc:
                                    try:
                                        result = api_client.create_function({
                                            "node_id": sel_id,
                                            "function_type": func_type,
                                            "description": func_desc,
                                        })
                                        st.success(t("fmea.function_created", id=result.get("function_id", "")))
                                        st.rerun()
                                    except Exception as e:
                                        st.error(str(e))

                with crud_col2:
                    with st.expander(t("fmea.add_ff"), expanded=False):
                        if functions:
                            with st.form("add_ff_form", clear_on_submit=True):
                                ff_func = st.selectbox(
                                    t("fmea.select_function"),
                                    [f["function_id"] for f in functions],
                                    format_func=lambda fid: next(
                                        (f["description"][:50] for f in functions if f["function_id"] == fid), fid
                                    ),
                                    key="add_ff_func",
                                )
                                ff_type = st.selectbox(
                                    t("fmea.ff_type"),
                                    ["TOTAL", "PARTIAL"],
                                    key="add_ff_type",
                                )
                                ff_desc = st.text_area(
                                    t("fmea.ff_description"),
                                    key="add_ff_desc",
                                )
                                if st.form_submit_button(t("fmea.add_ff")):
                                    if ff_desc:
                                        try:
                                            result = api_client.create_functional_failure({
                                                "function_id": ff_func,
                                                "failure_type": ff_type,
                                                "description": ff_desc,
                                            })
                                            st.success(t("fmea.ff_created", id=result.get("failure_id", "")))
                                            st.rerun()
                                        except Exception as e:
                                            st.error(str(e))
                        else:
                            st.info(t("fmea.no_functions"))

                with crud_col3:
                    with st.expander(t("fmea.add_fm"), expanded=False):
                        # Gather all functional failures for this node
                        all_ffs = []
                        if functions:
                            for func in functions:
                                try:
                                    ffs = api_client.list_functional_failures(function_id=func["function_id"])
                                    all_ffs.extend(ffs)
                                except Exception as e:
                                    logger.exception("Unexpected error")
                                    pass

                        if all_ffs:
                            with st.form("add_fm_form", clear_on_submit=True):
                                fm_ff = st.selectbox(
                                    t("fmea.select_ff"),
                                    [ff["failure_id"] for ff in all_ffs],
                                    format_func=lambda fid: next(
                                        (ff["description"][:50] for ff in all_ffs if ff["failure_id"] == fid), fid
                                    ),
                                    key="add_fm_ff",
                                )
                                fm_what = st.text_input("What", key="add_fm_what")
                                fm_mechanism = st.selectbox(t("fmea.mechanism"), MECHANISMS, key="add_fm_mech")
                                # Load valid causes for selected mechanism
                                try:
                                    combos = api_client.get_fm_combinations(fm_mechanism)
                                    valid_causes = combos.get("causes", [])
                                except Exception as e:
                                    logger.exception("Unexpected error")
                                    valid_causes = []
                                fm_cause = st.selectbox(
                                    t("fmea.cause"),
                                    valid_causes if valid_causes else ["(select mechanism first)"],
                                    key="add_fm_cause",
                                )
                                fm_consequence = st.selectbox(
                                    t("fmea.failure_consequence"),
                                    FAILURE_CONSEQUENCES,
                                    key="add_fm_cons",
                                )
                                fm_strategy = st.selectbox(
                                    "Strategy Type",
                                    STRATEGY_TYPES,
                                    key="add_fm_strat",
                                )
                                fm_hidden = st.checkbox(t("fmea.hidden_failure"), key="add_fm_hidden")

                                if st.form_submit_button(t("fmea.add_fm")):
                                    if fm_what and fm_cause != "(select mechanism first)":
                                        try:
                                            result = api_client.create_failure_mode({
                                                "functional_failure_id": fm_ff,
                                                "what": fm_what,
                                                "mechanism": fm_mechanism,
                                                "cause": fm_cause,
                                                "failure_consequence": fm_consequence,
                                                "strategy_type": fm_strategy,
                                                "is_hidden": fm_hidden,
                                            })
                                            st.success(t("fmea.fm_created", id=result.get("failure_mode_id", "")))
                                            st.rerun()
                                        except Exception as e:
                                            st.error(str(e))
                        else:
                            st.info(t("fmea.no_ff"))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: FM Validation (kept from original)
# ══════════════════════════════════════════════════════════════════════════════

with tab_validation:
    st.subheader(t("fmea.validate_combination"))
    col1, col2 = st.columns(2)
    mechanism = col1.selectbox(t("fmea.mechanism"), MECHANISMS, key="val_mech")
    try:
        combos = api_client.get_fm_combinations(mechanism)
        valid_causes = combos.get("causes", [])
        cause = col2.selectbox(t("fmea.cause"), valid_causes if valid_causes else [t("fmea.select_mechanism_first")], key="val_cause")
    except Exception as e:
        logger.exception("Unexpected error")
        cause = col2.text_input(t("fmea.cause"), key="val_cause_input")

    if st.button(t("common.validate"), key="btn_validate_fm"):
        result = api_client.validate_fm_combination(mechanism, cause)
        if result.get("valid"):
            st.success(t("fmea.valid_combination", mechanism=mechanism, cause=cause))
        else:
            st.error(t("fmea.invalid_combination", mechanism=mechanism, cause=cause))

    st.subheader(t("fmea.all_valid_combinations"))
    try:
        all_combos = api_client.get_fm_combinations()
        st.write(f"**{all_combos.get('total_combinations', 72)}** valid Mechanism+Cause combinations")
        st.write("Mechanisms:", ", ".join(all_combos.get("mechanisms", [])))
    except Exception as e:
        logger.exception("Unexpected error")
        pass


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: RCM Decision Tree (kept from original)
# ══════════════════════════════════════════════════════════════════════════════

with tab_rcm:
    st.subheader(t("fmea.rcm_decision_tree"))
    col1, col2 = st.columns(2)
    is_hidden = col1.checkbox(t("fmea.hidden_failure"), key="rcm_hidden")
    consequence = col1.selectbox(t("fmea.failure_consequence"), FAILURE_CONSEQUENCES, key="rcm_cons")
    cbm_feasible = col2.checkbox(t("fmea.cbm_tech_feasible"), value=True, key="rcm_cbm_tech")
    cbm_viable = col2.checkbox(t("fmea.cbm_econ_viable"), value=True, key="rcm_cbm_econ")
    ft_feasible = col2.checkbox(t("fmea.ft_feasible"), value=True, key="rcm_ft")
    failure_pattern = col1.selectbox(t("fmea.failure_pattern"), ["B_AGE", "C_FATIGUE", "D_STRESS", "E_RANDOM", "A_BATHTUB", "F_EARLY_LIFE"], key="rcm_pattern")

    if st.button(t("fmea.run_rcm_decision"), key="btn_rcm"):
        result = api_client.rcm_decide({
            "is_hidden": is_hidden,
            "failure_consequence": consequence,
            "cbm_technically_feasible": cbm_feasible,
            "cbm_economically_viable": cbm_viable,
            "ft_feasible": ft_feasible,
            "failure_pattern": failure_pattern,
        })
        st.success(t("fmea.strategy_result", strategy=result['strategy_type']))
        st.write(f"Path: {result['path']}")
        st.write(f"Reasoning: {result['reasoning']}")
        if result.get("requires_secondary_task"):
            st.warning(t("fmea.requires_secondary"))

feedback_widget("fmea")
