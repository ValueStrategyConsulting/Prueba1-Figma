"""Page 4: Maintenance Strategy — Tasks, Work Packages, Naming (R8 Style)."""

import logging
logger = logging.getLogger("10_strategy")

import html as _html
import json
import pandas as pd
import streamlit as st
from streamlit_app import api_client
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_style, apply_hierarchy_style, apply_r8_module_style
from streamlit_app.components.feedback import feedback_widget
from streamlit_app.components.forms import TASK_TYPES
from streamlit_app.components.tree_panel import (
    build_tree, init_tree_state, render_tree_panel,
    render_breadcrumb_bar, render_node_header, render_info_card,
)

st.set_page_config(page_title="Strategy", layout="wide")
page_init()
apply_style()
apply_hierarchy_style()
apply_r8_module_style()

# ── Session state ─────────────────────────────────────────────────────────────

init_tree_state(key_prefix="strat")
if "strat_selected_task_id" not in st.session_state:
    st.session_state["strat_selected_task_id"] = None
if "strat_selected_wp_id" not in st.session_state:
    st.session_state["strat_selected_wp_id"] = None

@st.cache_data(ttl=300, show_spinner=False)
def _load_plants():
    try:
        return api_client.list_plants()
    except Exception:
        return []

@st.cache_data(ttl=120, show_spinner=False)
def _load_nodes(plant_id):
    return api_client.list_nodes(plant_id=plant_id)

st.title(t("strategy.title"))

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
    key="strat_plant_select",
)

nodes = _load_nodes(plant_id=selected_plant)
node_map, children_map, root_ids = build_tree(nodes)


# ── Helper: gather tasks for a node ───────────────────────────────────────────

def _gather_tasks_for_node(node_id):
    """Get all maintenance tasks linked to failure modes under a node."""
    tasks_with_fm = []
    try:
        functions = api_client.list_functions(node_id=node_id)
    except Exception as e:
        logger.exception("Unexpected error")
        return []

    for func in functions:
        try:
            ffs = api_client.list_functional_failures(function_id=func["function_id"])
        except Exception as e:
            logger.exception("Unexpected error")
            continue
        for ff in ffs:
            try:
                fms = api_client.list_failure_modes(functional_failure_id=ff["failure_id"])
            except Exception as e:
                logger.exception("Unexpected error")
                continue
            for fm in fms:
                try:
                    tasks = api_client.list_tasks(failure_mode_id=fm["failure_mode_id"])
                except Exception as e:
                    logger.exception("Unexpected error")
                    tasks = []
                for task in tasks:
                    task["_mechanism"] = fm.get("mechanism", "")
                    task["_cause"] = fm.get("cause", "")
                    task["_what"] = fm.get("what", "")
                    task["_fm_id"] = fm.get("failure_mode_id", "")
                    tasks_with_fm.append(task)
    return tasks_with_fm


# ── Top-level tabs ────────────────────────────────────────────────────────────

tab_strategy, tab_wp, tab_naming = st.tabs([
    t("strategy.tab_tasks"),
    t("strategy.tab_work_packages"),
    t("strategy.tab_naming"),
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: Maintenance Strategy / Tasks (R8 split-pane)
# ══════════════════════════════════════════════════════════════════════════════

with tab_strategy:
    if not nodes:
        st.info(t("hierarchy.no_nodes"))
    else:
        left, right = st.columns([1, 3])

        with left:
            render_tree_panel(nodes, node_map, children_map, root_ids, key_prefix="strat")

        with right:
            sel_id = st.session_state.get("strat_selected_node_id")

            if not sel_id or sel_id not in node_map:
                st.markdown(
                    "<div class='empty-state'>"
                    "<div style='font-size:4em; opacity:0.3;'>\U0001F527</div>"
                    f"<h3>{t('strategy.select_node_first')}</h3>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                node = node_map[sel_id]
                render_breadcrumb_bar(sel_id, node_map)
                render_node_header(node)

                # ── Toolbar ───────────────────────────────────────────────
                tb_cols = st.columns([1, 1, 1, 4])
                add_task_btn = tb_cols[0].button(t("strategy.add_task"), key="btn_add_task")
                tb_cols[1].button(t("strategy.delete_task"), key="btn_del_task")
                tb_cols[2].button(t("strategy.export_tasks"), key="btn_export_task")

                # ── Main Task Grid ────────────────────────────────────────
                all_tasks = _gather_tasks_for_node(sel_id)

                if not all_tasks:
                    st.info(t("strategy.no_tasks_for_node"))
                else:
                    grid_rows = []
                    for i, task in enumerate(all_tasks, 1):
                        grid_rows.append({
                            t("strategy.no_col"): i,
                            t("strategy.item_col"): task.get("name", ""),
                            t("strategy.mechanism_col"): task.get("_mechanism", ""),
                            t("strategy.cause_col"): task.get("_cause", ""),
                            t("strategy.status_col"): task.get("status", ""),
                            t("strategy.priority_task_col"): task.get("task_type", ""),
                        })

                    st.markdown(f"<div class='r8-form-title'>{t('strategy.task_grid')}</div>", unsafe_allow_html=True)
                    df_tasks = pd.DataFrame(grid_rows)
                    st.dataframe(df_tasks, use_container_width=True, hide_index=True)

                    # Task selector for detail view
                    task_options = {task["task_id"]: task.get("name", task["task_id"]) for task in all_tasks}
                    selected_task_id = st.selectbox(
                        t("strategy.select_task_detail"),
                        list(task_options.keys()),
                        format_func=lambda x: task_options[x],
                        key="strat_task_select",
                    )

                    if selected_task_id:
                        # Fetch full task detail
                        try:
                            task_detail = api_client.get_task(selected_task_id)
                        except Exception as e:
                            logger.exception("Unexpected error")
                            task_detail = next((t for t in all_tasks if t["task_id"] == selected_task_id), {})

                        # ── Task Definition Sub-tabs ──────────────────────
                        st.markdown(f"<div class='r8-form-title'>{t('strategy.task_definition')}: {_html.escape(task_detail.get('name', ''))}</div>", unsafe_allow_html=True)

                        tab_info, tab_full, tab_mat, tab_lab, tab_tools = st.tabs([
                            t("strategy.tab_information"),
                            t("strategy.tab_full_data"),
                            t("strategy.tab_material"),
                            t("strategy.tab_labour"),
                            t("strategy.tab_tools"),
                        ])

                        with tab_info:
                            ic1, ic2 = st.columns(2)
                            with ic1:
                                render_info_card(t("strategy.tab_information"), {
                                    t("strategy.task_name"): task_detail.get("name", ""),
                                    t("strategy.task_type"): task_detail.get("task_type", ""),
                                    t("strategy.constraint"): task_detail.get("constraint", ""),
                                    t("strategy.frequency_value"): str(task_detail.get("frequency_value", "")),
                                    t("strategy.frequency_unit"): task_detail.get("frequency_unit", ""),
                                    t("common.status"): task_detail.get("status", ""),
                                })
                            with ic2:
                                render_info_card(t("strategy.task_definition"), {
                                    t("strategy.acceptable_limits"): task_detail.get("acceptable_limits", "") or "\u2014",
                                    t("strategy.conditional_comments"): task_detail.get("conditional_comments", "") or "\u2014",
                                    t("strategy.consequence"): task_detail.get("consequences", "") or "\u2014",
                                    t("strategy.justification"): task_detail.get("justification", "") or "\u2014",
                                    t("strategy.origin"): task_detail.get("origin", "") or "\u2014",
                                })

                        with tab_full:
                            # Flat display of all task fields
                            flat_data = {k: str(v) for k, v in task_detail.items() if v and k != "_fm_id"}
                            st.dataframe(
                                pd.DataFrame(list(flat_data.items()), columns=["Field", "Value"]),
                                use_container_width=True,
                                hide_index=True,
                            )

                        with tab_mat:
                            materials = task_detail.get("material_resources") or []
                            if isinstance(materials, str):
                                try:
                                    materials = json.loads(materials)
                                except Exception as e:
                                    logger.exception("Unexpected error")
                                    materials = []
                            if materials:
                                st.dataframe(pd.DataFrame(materials), use_container_width=True, hide_index=True)
                            else:
                                st.info(t("common.no_data_available"))

                            with st.expander(t("strategy.add_material")):
                                with st.form("add_material_form", clear_on_submit=True):
                                    mc1, mc2 = st.columns(2)
                                    mat_name = mc1.text_input(t("strategy.material_name"))
                                    mat_pn = mc2.text_input(t("strategy.material_part_number"))
                                    mc3, mc4 = st.columns(2)
                                    mat_code = mc3.text_input(t("strategy.material_stock_code"))
                                    mat_qty = mc4.number_input(t("strategy.material_qty"), min_value=1, value=1)
                                    if st.form_submit_button(t("strategy.add_material")):
                                        st.info("Material added (save pending)")

                        with tab_lab:
                            labour = task_detail.get("labour_resources") or []
                            if isinstance(labour, str):
                                try:
                                    labour = json.loads(labour)
                                except Exception as e:
                                    logger.exception("Unexpected error")
                                    labour = []
                            if labour:
                                st.dataframe(pd.DataFrame(labour), use_container_width=True, hide_index=True)
                            else:
                                st.info(t("common.no_data_available"))

                            with st.expander(t("strategy.add_labour")):
                                with st.form("add_labour_form", clear_on_submit=True):
                                    lc1, lc2 = st.columns(2)
                                    lab_skill = lc1.selectbox(t("strategy.labour_skill"), [
                                        "MECHANIC", "ELECTRICIAN", "INSTRUMENTATION",
                                        "BOILERMAKER", "FITTER", "OPERATOR", "SUPERVISOR",
                                    ])
                                    lab_hours = lc2.number_input(t("strategy.labour_hours"), min_value=0.1, value=1.0, step=0.5)
                                    if st.form_submit_button(t("strategy.add_labour")):
                                        st.info("Labour added (save pending)")

                        with tab_tools:
                            tools = task_detail.get("tools_list") or []
                            if isinstance(tools, str):
                                try:
                                    tools = json.loads(tools)
                                except Exception as e:
                                    logger.exception("Unexpected error")
                                    tools = []
                            if tools:
                                st.dataframe(pd.DataFrame(tools), use_container_width=True, hide_index=True)
                            else:
                                st.info(t("common.no_data_available"))

                # ── Add Task form ─────────────────────────────────────────
                if add_task_btn:
                    st.divider()
                    st.markdown(f"<div class='r8-form-title'>{t('strategy.add_task')}</div>", unsafe_allow_html=True)

                    # Gather FMs for this node
                    available_fms = []
                    try:
                        functions = api_client.list_functions(node_id=sel_id)
                        for func in functions:
                            try:
                                ffs = api_client.list_functional_failures(function_id=func["function_id"])
                            except Exception as e:
                                logger.exception("Unexpected error")
                                continue
                            for ff in ffs:
                                try:
                                    fms = api_client.list_failure_modes(functional_failure_id=ff["failure_id"])
                                    available_fms.extend(fms)
                                except Exception as e:
                                    logger.exception("Unexpected error")
                                    pass
                    except Exception as e:
                        logger.exception("Unexpected error")
                        pass

                    if not available_fms:
                        st.warning("No failure modes found for this node. Create failure modes in the FMEA page first.")
                    else:
                        with st.form("add_task_strategy_form", clear_on_submit=True):
                            tc1, tc2 = st.columns(2)
                            new_task_fm = tc1.selectbox(
                                "Failure Mode",
                                [fm["failure_mode_id"] for fm in available_fms],
                                format_func=lambda fid: next(
                                    (f"{fm['what']} - {fm['mechanism']}" for fm in available_fms if fm["failure_mode_id"] == fid), fid
                                ),
                            )
                            new_task_name = tc2.text_input(t("strategy.task_name"), max_chars=72)
                            tc3, tc4, tc5 = st.columns(3)
                            new_task_type = tc3.selectbox(t("strategy.task_type"), TASK_TYPES)
                            new_task_constraint = tc4.selectbox(t("strategy.constraint"), ["ONLINE", "OFFLINE", "TEST_MODE"])
                            new_task_freq_val = tc5.number_input(t("strategy.frequency_value"), min_value=0.1, value=1.0)
                            tc6, tc7 = st.columns(2)
                            new_task_freq_unit = tc6.selectbox(t("strategy.frequency_unit"), [
                                "HOURS", "DAYS", "WEEKS", "MONTHS", "YEARS", "OPERATING_HOURS",
                            ])
                            new_task_limits = tc7.text_input(t("strategy.acceptable_limits"))
                            new_task_comments = st.text_area(t("strategy.conditional_comments"))

                            if st.form_submit_button(t("strategy.add_task")):
                                if new_task_name:
                                    # Validate naming convention
                                    validation = api_client.validate_task_name(new_task_name, new_task_type)
                                    if not validation.get("valid", True):
                                        for issue in validation.get("issues", []):
                                            st.warning(issue)
                                    try:
                                        result = api_client.create_task({
                                            "failure_mode_id": new_task_fm,
                                            "name": new_task_name,
                                            "task_type": new_task_type,
                                            "constraint": new_task_constraint,
                                            "frequency_value": new_task_freq_val,
                                            "frequency_unit": new_task_freq_unit,
                                            "acceptable_limits": new_task_limits,
                                            "conditional_comments": new_task_comments,
                                        })
                                        st.success(t("strategy.task_created", id=result.get("task_id", "")))
                                        st.rerun()
                                    except Exception as e:
                                        st.error(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: Work Packages (R8 split-pane)
# ══════════════════════════════════════════════════════════════════════════════

with tab_wp:
    # Initialize WP tree state
    if "wp_selected_id" not in st.session_state:
        st.session_state["wp_selected_id"] = None

    wp_left, wp_right = st.columns([1, 3])

    with wp_left:
        st.markdown("<div class='r8-form-title'>Work Packages</div>", unsafe_allow_html=True)

        # Load all work packages
        try:
            all_wps = api_client.list_work_packages()
        except Exception as e:
            logger.exception("Unexpected error")
            all_wps = []

        if not all_wps:
            st.info(t("strategy.no_wps_for_node"))
        else:
            # Build WP list as a selectable radio
            wp_labels = []
            wp_ids = []
            for wp in all_wps:
                status_icon = "\u2705" if wp.get("status") == "APPROVED" else "\U0001F4DD"
                wp_labels.append(f"{status_icon} {wp.get('name', wp['work_package_id'])}")
                wp_ids.append(wp["work_package_id"])

            current_wp = st.session_state.get("wp_selected_id")
            default_idx = 0
            if current_wp and current_wp in wp_ids:
                default_idx = wp_ids.index(current_wp)

            chosen_wp = st.radio(
                "Work Packages",
                wp_labels,
                index=default_idx,
                key="wp_tree_radio",
                label_visibility="collapsed",
            )
            if chosen_wp:
                idx = wp_labels.index(chosen_wp)
                st.session_state["wp_selected_id"] = wp_ids[idx]

    with wp_right:
        sel_wp_id = st.session_state.get("wp_selected_id")

        if not sel_wp_id:
            st.markdown(
                "<div class='empty-state'>"
                "<div style='font-size:4em; opacity:0.3;'>\U0001F4E6</div>"
                f"<h3>{t('strategy.select_wp_first')}</h3>"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            # Fetch WP detail
            try:
                wp_detail = api_client.get_work_package(sel_wp_id)
            except Exception as e:
                logger.exception("Unexpected error")
                wp_detail = next((wp for wp in all_wps if wp["work_package_id"] == sel_wp_id), {})

            # ── WP Sub-tabs ───────────────────────────────────────────
            wp_tab_folder, wp_tab_details, wp_tab_alloc, wp_tab_resources = st.tabs([
                t("strategy.wp_folder"),
                t("strategy.wp_details"),
                t("strategy.wp_allocate_tasks"),
                t("strategy.wp_resources"),
            ])

            with wp_tab_folder:
                # Overview grid of all WPs
                wp_grid = []
                for wp in all_wps:
                    wp_grid.append({
                        "Name": wp.get("name", ""),
                        "Code": wp.get("code", ""),
                        t("common.status"): wp.get("status", ""),
                    })
                st.dataframe(pd.DataFrame(wp_grid), use_container_width=True, hide_index=True)

            with wp_tab_details:
                st.markdown(f"<div class='r8-form-title'>{_html.escape(wp_detail.get('name', ''))}</div>", unsafe_allow_html=True)
                dc1, dc2 = st.columns(2)
                with dc1:
                    render_info_card(t("strategy.wp_details"), {
                        t("strategy.wp_name"): wp_detail.get("name", ""),
                        t("strategy.wp_code"): wp_detail.get("code", ""),
                        t("strategy.wp_type"): wp_detail.get("work_package_type", ""),
                        t("strategy.wp_status"): wp_detail.get("status", ""),
                    })
                with dc2:
                    render_info_card(t("strategy.wp_frequency"), {
                        t("strategy.frequency_value"): str(wp_detail.get("frequency_value", "")),
                        t("strategy.frequency_unit"): wp_detail.get("frequency_unit", ""),
                        t("strategy.wp_constraint"): wp_detail.get("constraint", ""),
                        t("strategy.wp_access_time"): str(wp_detail.get("access_time_hours", "")),
                        "Node ID": wp_detail.get("node_id", ""),
                    })

                # Approve button for DRAFT WPs
                if wp_detail.get("status") == "DRAFT":
                    if st.button(t("strategy.approve_wp"), key="btn_approve_wp"):
                        try:
                            result = api_client.approve_work_package(sel_wp_id)
                            st.success(t("strategy.approved", result=result.get("status", "")))
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

            with wp_tab_alloc:
                allocated = wp_detail.get("allocated_tasks") or []
                if isinstance(allocated, str):
                    try:
                        allocated = json.loads(allocated)
                    except Exception as e:
                        logger.exception("Unexpected error")
                        allocated = []

                if allocated:
                    st.markdown(f"<div class='r8-form-title'>{t('strategy.allocated_tasks')}</div>", unsafe_allow_html=True)
                    st.dataframe(pd.DataFrame(allocated), use_container_width=True, hide_index=True)
                else:
                    st.info(t("common.no_data_available"))

            with wp_tab_resources:
                # Labour summary
                labour_summary = wp_detail.get("labour_summary") or {}
                if isinstance(labour_summary, str):
                    try:
                        labour_summary = json.loads(labour_summary)
                    except Exception as e:
                        logger.exception("Unexpected error")
                        labour_summary = {}

                st.markdown(f"<div class='r8-form-title'>{t('strategy.labour_summary')}</div>", unsafe_allow_html=True)
                if labour_summary:
                    st.json(labour_summary)
                else:
                    st.info(t("common.no_data_available"))

                # Material summary
                material_summary = wp_detail.get("material_summary") or []
                if isinstance(material_summary, str):
                    try:
                        material_summary = json.loads(material_summary)
                    except Exception as e:
                        logger.exception("Unexpected error")
                        material_summary = []

                st.markdown(f"<div class='r8-form-title'>{t('strategy.material_summary')}</div>", unsafe_allow_html=True)
                if material_summary:
                    st.dataframe(pd.DataFrame(material_summary), use_container_width=True, hide_index=True)
                else:
                    st.info(t("common.no_data_available"))

    # ── Add Work Package form ─────────────────────────────────────────
    st.divider()
    with st.expander(t("strategy.add_wp"), expanded=False):
        with st.form("add_wp_form", clear_on_submit=True):
            wc1, wc2 = st.columns(2)
            wp_name = wc1.text_input(t("strategy.wp_name"), max_chars=40)
            wp_type = wc2.selectbox(t("strategy.wp_type"), ["STANDALONE", "SUPPRESSIVE", "SEQUENTIAL"])
            wc3, wc4 = st.columns(2)
            wp_constraint = wc3.selectbox(t("strategy.wp_constraint"), ["ONLINE", "OFFLINE"])
            wp_freq_val = wc4.number_input(t("strategy.frequency_value"), min_value=0.1, value=1.0)
            wc5, wc6 = st.columns(2)
            wp_freq_unit = wc5.selectbox(t("strategy.frequency_unit"), [
                "HOURS", "DAYS", "WEEKS", "MONTHS", "YEARS", "OPERATING_HOURS",
            ])
            wp_node = wc6.text_input("Node ID", value=st.session_state.get("strat_selected_node_id", ""))

            if st.form_submit_button(t("strategy.add_wp")):
                if wp_name:
                    # R8 validation: ALL CAPS, max 40
                    if wp_name != wp_name.upper():
                        st.warning("WP name must be ALL CAPS per R8 naming convention.")
                    elif len(wp_name) > 40:
                        st.warning("WP name must be max 40 characters.")
                    else:
                        try:
                            code = f"WP-{wp_name[:20].replace(' ', '-')}"
                            result = api_client.create_work_package({
                                "name": wp_name,
                                "code": code,
                                "node_id": wp_node,
                                "frequency_value": wp_freq_val,
                                "frequency_unit": wp_freq_unit,
                                "constraint": wp_constraint,
                                "work_package_type": wp_type,
                            })
                            st.success(t("strategy.wp_created", id=result.get("work_package_id", "")))
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: Naming Validation (kept from original)
# ══════════════════════════════════════════════════════════════════════════════

with tab_naming:
    st.subheader(t("strategy.task_name_validation"))
    task_name = st.text_input(t("strategy.task_name_input"), key="val_task_name")
    task_type = st.selectbox(t("strategy.task_type"), TASK_TYPES, key="val_task_type")
    if st.button(t("strategy.validate_task_name"), key="btn_val_task"):
        result = api_client.validate_task_name(task_name, task_type)
        if result["valid"]:
            st.success(t("strategy.valid_task_name"))
        else:
            for issue in result.get("issues", []):
                st.warning(issue)

    st.subheader(t("strategy.wp_name_validation"))
    wp_name_val = st.text_input(t("strategy.wp_name_input"), key="val_wp_name")
    if st.button(t("strategy.validate_wp_name"), key="btn_val_wp"):
        result = api_client.validate_wp_name(wp_name_val)
        if result["valid"]:
            st.success(t("strategy.valid_wp_name"))
        else:
            for issue in result.get("issues", []):
                st.warning(issue)

feedback_widget("strategy")
