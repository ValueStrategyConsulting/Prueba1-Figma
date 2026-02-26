"""Page 1: Plant Hierarchy — Modern split-pane explorer with tree + detail."""

import logging
logger = logging.getLogger("07_hierarchy")

import html as _html
import streamlit as st
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_style, apply_hierarchy_style
from streamlit_app import api_client
from streamlit_app.components.tree_panel import (
    NODE_CONFIG,
    build_tree, init_tree_state, render_tree_panel,
    render_breadcrumb_bar, render_node_header, render_info_card,
)
from streamlit_app.components.tables import metric_row
from streamlit_app.components.charts import node_distribution_pie, hierarchy_sunburst
from streamlit_app.components.feedback import feedback_widget

st.set_page_config(page_title="Plant Hierarchy", page_icon=":deciduous_tree:", layout="wide")
page_init()
apply_style()
apply_hierarchy_style()

# ── Constants ─────────────────────────────────────────────────────────────────

EQUIPMENT_TYPES = [
    "SAG_MILL", "BALL_MILL", "ROD_MILL", "SLURRY_PUMP", "FLOTATION_CELL",
    "BELT_CONVEYOR", "THICKENER", "BELT_FILTER", "ROTARY_DRYER", "CRUSHER",
    "VIBRATING_SCREEN", "HYDROCYCLONE", "AGITATOR", "COMPRESSOR", "HEAT_EXCHANGER",
]


# ── Session state ─────────────────────────────────────────────────────────────

init_tree_state(key_prefix="hier")

@st.cache_data(ttl=300, show_spinner=False)
def _load_plants():
    try:
        return api_client.list_plants()
    except Exception:
        return []

@st.cache_data(ttl=120, show_spinner=False)
def _load_nodes(plant_id):
    return api_client.list_nodes(plant_id=plant_id)


# ── Render: detail panel ─────────────────────────────────────────────────────

def _render_metadata_cards(meta: dict):
    """Render spec cards for technical metadata."""
    specs = [
        ("meta_manufacturer", "\U0001F3ED"),
        ("meta_model", "\U0001F4CB"),
        ("meta_serial_number", "\U0001F4DF"),
        ("meta_installation_date", "\U0001F4C5"),
        ("meta_power_kw", "\u26A1"),
        ("meta_weight_kg", "\u2696\uFE0F"),
        ("meta_operational_hours", "\u23F1\uFE0F"),
    ]
    cols = st.columns(4)
    idx = 0
    for key, icon in specs:
        raw_key = key.replace("meta_", "")
        val = meta.get(raw_key, "")
        if val:
            with cols[idx % 4]:
                st.markdown(
                    f"<div class='spec-card'>"
                    f"<div style='font-size:1.8em;'>{icon}</div>"
                    f"<div style='font-size:1.2em; font-weight:700;'>{val}</div>"
                    f"<div style='font-size:0.8em; color:#777;'>{t(f'hierarchy.{key}')}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            idx += 1
    if idx == 0:
        st.info(t("hierarchy.no_metadata"))


def render_detail(node, node_map, children_map):
    """Right panel: breadcrumb + header + tabs (Properties, Children, Technical)."""
    render_breadcrumb_bar(node["node_id"], node_map)
    render_node_header(node)

    tab_p, tab_c, tab_t = st.tabs([
        t("hierarchy.tab_properties"),
        t("hierarchy.tab_children"),
        t("hierarchy.tab_technical"),
    ])

    with tab_p:
        col1, col2 = st.columns(2)
        with col1:
            render_info_card(t("hierarchy.identity"), {
                t("hierarchy.node_id_label"): node.get("node_id", ""),
                t("hierarchy.node_type_label"): node.get("node_type", ""),
                t("hierarchy.level_label"): node.get("level", ""),
                t("hierarchy.code_label"): node.get("code", ""),
                t("hierarchy.tag_label"): node.get("tag", ""),
                t("hierarchy.status_label"): node.get("status", ""),
                t("hierarchy.criticality_label"): node.get("criticality", ""),
            })
        with col2:
            render_info_card(t("hierarchy.sap_references"), {
                t("hierarchy.sap_func_loc"): node.get("sap_func_loc", ""),
                t("hierarchy.sap_equipment_nr"): node.get("sap_equipment_nr", ""),
                t("hierarchy.equipment_lib_ref"): node.get("equipment_lib_ref", ""),
                t("hierarchy.component_lib_ref"): node.get("component_lib_ref", ""),
            })
            render_info_card(t("hierarchy.hierarchy_info"), {
                t("hierarchy.parent_label"): node_map.get(node.get("parent_node_id", ""), {}).get("name", "\u2014"),
                t("hierarchy.plant_label"): node.get("plant_id", ""),
            })

    with tab_c:
        child_ids = children_map.get(node["node_id"], [])
        if child_ids:
            import pandas as pd
            child_rows = []
            for cid in child_ids:
                cn = node_map.get(cid, {})
                cfg = NODE_CONFIG.get(cn.get("node_type", ""), {})
                child_rows.append({
                    "": cfg.get("icon", ""),
                    t("hierarchy.node_type_label"): cn.get("node_type", ""),
                    "Name": cn.get("name", ""),
                    t("hierarchy.code_label"): cn.get("code", ""),
                    t("hierarchy.criticality_label"): cn.get("criticality", ""),
                })
            st.dataframe(pd.DataFrame(child_rows), use_container_width=True, hide_index=True)
        else:
            st.info(t("hierarchy.no_children"))

    with tab_t:
        meta = node.get("metadata_json") or node.get("metadata") or {}
        if isinstance(meta, str):
            import json
            try:
                meta = json.loads(meta)
            except Exception as e:
                logger.exception("Unexpected error")
                meta = {}
        _render_metadata_cards(meta)


# ── Render: vendor build form ────────────────────────────────────────────────

def render_vendor_form(selected_plant):
    """Vendor build form migrated from original code."""
    with st.form("vendor_build_form"):
        vc1, vc2, vc3 = st.columns(3)
        vb_area = vc1.text_input(t("hierarchy.area_code"), value="BRY", max_chars=4)
        vb_type = vc2.selectbox(t("hierarchy.equipment_type"), EQUIPMENT_TYPES)
        vb_model = vc3.text_input(t("hierarchy.model"), placeholder="e.g. 36x20")
        vc4, vc5, vc6 = st.columns(3)
        vb_manufacturer = vc4.text_input(t("hierarchy.manufacturer"), placeholder="e.g. FLSmidth")
        vb_power = vc5.number_input(t("hierarchy.power_kw"), min_value=0.0, value=0.0)
        vb_weight = vc6.number_input(t("hierarchy.weight_kg"), min_value=0.0, value=0.0)

        submitted = st.form_submit_button(t("hierarchy.build_hierarchy"))
        if submitted:
            try:
                result = api_client.build_from_vendor({
                    "plant_id": selected_plant,
                    "area_code": vb_area,
                    "equipment_type": vb_type,
                    "model": vb_model,
                    "manufacturer": vb_manufacturer,
                    "power_kw": vb_power,
                    "weight_kg": vb_weight,
                })
                st.success(f"{t('hierarchy.nodes_created')}: {result.get('nodes_persisted', result.get('nodes_created', 0))}")
                st.json(result)
            except Exception as e:
                st.error(str(e))


# ── Main ──────────────────────────────────────────────────────────────────────

st.title(t("hierarchy.title"))

# Load plants
plants = _load_plants()
if not plants:
    st.info(t("hierarchy.no_plants"))
    st.stop()

plant_names = {p["plant_id"]: p["name"] for p in plants}
selected_plant = st.selectbox(
    t("hierarchy.select_plant"),
    list(plant_names.keys()),
    format_func=lambda x: plant_names[x],
    key="hier_plant_select",
)

# Load all nodes for the selected plant
nodes = _load_nodes(plant_id=selected_plant)
node_map, children_map, root_ids = build_tree(nodes)

# ── 4 top-level tabs ─────────────────────────────────────────────────────────

tab_explorer, tab_grids, tab_stats, tab_vendor = st.tabs([
    t("hierarchy.tab_explorer"),
    t("hierarchy.tab_grid_views"),
    t("hierarchy.tab_statistics"),
    t("hierarchy.tab_vendor_build"),
])

# ── Tab 1: Explorer (split-pane) ─────────────────────────────────────────────

with tab_explorer:
    if not nodes:
        st.info(t("hierarchy.no_nodes"))
    else:
        left, right = st.columns([1, 3])
        with left:
            render_tree_panel(nodes, node_map, children_map, root_ids, key_prefix="hier")
        with right:
            sel_id = st.session_state.get("hier_selected_node_id")
            if sel_id and sel_id in node_map:
                render_detail(node_map[sel_id], node_map, children_map)
            else:
                st.markdown(
                    "<div class='empty-state'>"
                    "<div style='font-size:4em; opacity:0.3;'>\U0001F3D7\uFE0F</div>"
                    f"<h3>{t('hierarchy.empty_state_title')}</h3>"
                    f"<p>{t('hierarchy.empty_state_desc')}</p>"
                    "</div>",
                    unsafe_allow_html=True,
                )

# ── Tab 2: Grid Views ────────────────────────────────────────────────────────

with tab_grids:
    if not nodes:
        st.info(t("hierarchy.no_nodes"))
    else:
        import pandas as pd
        grid_eq, grid_mi, grid_all = st.tabs([
            t("hierarchy.equipment_grid"),
            t("hierarchy.maintainable_grid"),
            t("hierarchy.full_hierarchy_grid"),
        ])

        key_cols = ["node_id", "node_type", "name", "code", "level", "criticality", "tag", "status"]

        with grid_eq:
            eq_nodes = [n for n in nodes if n.get("node_type") == "EQUIPMENT"]
            if eq_nodes:
                df = pd.DataFrame(eq_nodes)[key_cols]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No equipment nodes found.")

        with grid_mi:
            mi_nodes = [n for n in nodes if n.get("node_type") == "MAINTAINABLE_ITEM"]
            if mi_nodes:
                df = pd.DataFrame(mi_nodes)[key_cols]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No maintainable item nodes found.")

        with grid_all:
            df = pd.DataFrame(nodes)
            display_cols = [c for c in key_cols if c in df.columns]
            st.dataframe(df[display_cols] if display_cols else df, use_container_width=True, hide_index=True)

# ── Tab 3: Statistics ─────────────────────────────────────────────────────────

with tab_stats:
    stats = api_client.get_node_stats(selected_plant)
    if stats:
        metric_row(stats)
        col_pie, col_sun = st.columns(2)
        with col_pie:
            st.plotly_chart(
                node_distribution_pie(stats, t("hierarchy.title")),
                use_container_width=True,
            )
        with col_sun:
            if nodes:
                st.plotly_chart(
                    hierarchy_sunburst(nodes, t("hierarchy.sunburst_title")),
                    use_container_width=True,
                )
    else:
        st.info(t("hierarchy.no_nodes"))

# ── Tab 4: Vendor Build ──────────────────────────────────────────────────────

with tab_vendor:
    st.subheader(t("hierarchy.build_from_vendor"))
    render_vendor_form(selected_plant)

feedback_widget("hierarchy")
