"""Reusable hierarchy tree panel for R8-style split-pane layouts.

Extracted from 1_hierarchy.py for reuse across Functions, Strategy,
Work Packages, and FMECA pages.
"""

import html as _html
import streamlit as st
from streamlit_app import api_client
from streamlit_app.i18n import t


# ── Node display configuration ────────────────────────────────────────

NODE_CONFIG = {
    "PLANT":             {"icon": "\U0001F3ED", "color": "#1B5E20", "bg": "#E8F5E9"},
    "AREA":              {"icon": "\U0001F4CD", "color": "#0D47A1", "bg": "#E3F2FD"},
    "SYSTEM":            {"icon": "\u2699\uFE0F",  "color": "#E65100", "bg": "#FFF3E0"},
    "EQUIPMENT":         {"icon": "\U0001F527", "color": "#4A148C", "bg": "#F3E5F5"},
    "SUB_ASSEMBLY":      {"icon": "\U0001F529", "color": "#006064", "bg": "#E0F7FA"},
    "MAINTAINABLE_ITEM": {"icon": "\U0001F50D", "color": "#BF360C", "bg": "#FBE9E7"},
}

CRIT_COLORS = {
    "AA": "#D32F2F", "A+": "#E65100", "A": "#F9A825", "B": "#2E7D32", "C": "#757575",
}


# ── Tree data helpers ─────────────────────────────────────────────────

def build_tree(nodes: list[dict]):
    """Flat list -> node_map, children_map, root_ids."""
    node_map = {n["node_id"]: n for n in nodes}
    children_map: dict[str, list[str]] = {}
    root_ids: list[str] = []
    for n in nodes:
        pid = n.get("parent_node_id")
        if pid and pid in node_map:
            children_map.setdefault(pid, []).append(n["node_id"])
        else:
            root_ids.append(n["node_id"])
    return node_map, children_map, root_ids


def get_visible(root_ids, children_map, expanded, node_map, query=""):
    """Return ordered list of (node_id, indent_level) for the visible tree."""
    result = []
    query_lower = query.strip().lower()

    def _matches(nid):
        n = node_map[nid]
        name = (n.get("name") or "").lower()
        code = (n.get("code") or "").lower()
        return query_lower in name or query_lower in code

    def _subtree_matches(nid):
        if _matches(nid):
            return True
        for cid in children_map.get(nid, []):
            if _subtree_matches(cid):
                return True
        return False

    def _walk(nid, depth):
        if query_lower and not _subtree_matches(nid):
            return
        result.append((nid, depth))
        if nid in expanded or query_lower:
            for cid in children_map.get(nid, []):
                _walk(cid, depth + 1)

    for rid in root_ids:
        _walk(rid, 0)
    return result


def get_breadcrumb(node_id, node_map):
    """Walk parents upward to build breadcrumb list."""
    crumbs = []
    nid = node_id
    while nid and nid in node_map:
        n = node_map[nid]
        cfg = NODE_CONFIG.get(n.get("node_type", ""), {})
        crumbs.append({"name": n.get("name", nid), "icon": cfg.get("icon", ""), "id": nid})
        nid = n.get("parent_node_id")
    crumbs.reverse()
    return crumbs


# ── Session state helpers ─────────────────────────────────────────────

def init_tree_state(key_prefix="tree"):
    """Initialize session state keys for a tree instance."""
    expanded_key = f"{key_prefix}_expanded_nodes"
    selected_key = f"{key_prefix}_selected_node_id"
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = set()
    if selected_key not in st.session_state:
        st.session_state[selected_key] = None


# ── Render: tree panel ────────────────────────────────────────────────

def render_tree_panel(nodes, node_map, children_map, root_ids, key_prefix="tree"):
    """Render the tree panel with search and radio selection.

    Args:
        nodes: Full flat list of nodes
        node_map: dict {node_id: node}
        children_map: dict {node_id: [child_ids]}
        root_ids: list of root node IDs
        key_prefix: Unique prefix for session state keys

    Returns:
        Selected node_id or None
    """
    expanded_key = f"{key_prefix}_expanded_nodes"
    selected_key = f"{key_prefix}_selected_node_id"

    # Auto-expand roots on first load
    if not st.session_state[expanded_key] and root_ids:
        st.session_state[expanded_key] = set(root_ids)

    query = st.text_input(
        "\U0001F50E",
        placeholder=t("hierarchy.search_placeholder"),
        key=f"{key_prefix}_tree_search",
        label_visibility="collapsed",
    )

    visible = get_visible(
        root_ids, children_map, st.session_state[expanded_key], node_map, query,
    )

    if not visible:
        st.caption(t("hierarchy.no_nodes"))
        return st.session_state.get(selected_key)

    # Build labels
    labels = []
    id_list = []
    for nid, depth in visible:
        n = node_map[nid]
        cfg = NODE_CONFIG.get(n.get("node_type", ""), {"icon": "", "color": "#555"})
        has_children = nid in children_map
        is_expanded = nid in st.session_state[expanded_key]
        chevron = "\u25BC" if (has_children and is_expanded) else ("\u25B6" if has_children else "\u2003")
        indent = "\u2003" * depth
        crit = n.get("criticality", "")
        crit_badge = f"  [{crit}]" if crit else ""
        label = f"{indent}{chevron} {cfg['icon']} {n.get('name', nid)}{crit_badge}"
        labels.append(label)
        id_list.append(nid)

    # Find current selection index
    current_sel = st.session_state.get(selected_key)
    default_idx = 0
    if current_sel and current_sel in id_list:
        default_idx = id_list.index(current_sel)

    chosen = st.radio(
        "Asset Tree",
        labels,
        index=default_idx,
        key=f"{key_prefix}_tree_radio",
        label_visibility="collapsed",
    )

    if chosen:
        idx = labels.index(chosen)
        nid = id_list[idx]
        # Toggle expand/collapse
        if nid in children_map:
            if nid in st.session_state[expanded_key]:
                if nid != st.session_state.get(selected_key):
                    st.session_state[selected_key] = nid
                else:
                    st.session_state[expanded_key].discard(nid)
                    st.session_state[selected_key] = nid
            else:
                st.session_state[expanded_key].add(nid)
                st.session_state[selected_key] = nid
        else:
            st.session_state[selected_key] = nid

    st.caption(f"{len(nodes)} {t('hierarchy.total_nodes')}")
    return st.session_state.get(selected_key)


# ── Render: breadcrumb bar ────────────────────────────────────────────

def render_breadcrumb_bar(node_id, node_map):
    """Render breadcrumb bar as HTML."""
    crumbs = get_breadcrumb(node_id, node_map)
    parts = [f"{c['icon']} {c['name']}" for c in crumbs]
    html = " <span style='color:#999; margin:0 4px;'>\u25B8</span> ".join(parts)
    st.markdown(f"<div class='hierarchy-breadcrumb'>{html}</div>", unsafe_allow_html=True)


# ── Render: node header card ─────────────────────────────────────────

def render_node_header(node):
    """Node header card with type badge, status, name, chips."""
    cfg = NODE_CONFIG.get(node.get("node_type", ""), {"icon": "", "color": "#555", "bg": "#f5f5f5"})
    ntype = node.get("node_type", "UNKNOWN")
    type_key = f"hierarchy.type_{ntype.lower()}"
    type_label = t(type_key) if t(type_key) != type_key else ntype
    status = node.get("status", "")
    status_color = "#2E7D32" if status == "ACTIVE" else "#E65100" if status == "INACTIVE" else "#757575"

    code_chip = f"<span style='background:#f0f0f0; padding:2px 10px; border-radius:12px; font-size:0.85em;'>{_html.escape(str(node.get('code', '-')))}</span>" if node.get("code") else ""
    tag_chip = f"<span style='background:#f0f0f0; padding:2px 10px; border-radius:12px; font-size:0.85em;'>{_html.escape(str(node.get('tag', '')))}</span>" if node.get("tag") else ""
    crit = node.get("criticality", "")
    crit_chip = ""
    if crit:
        cc = CRIT_COLORS.get(crit, "#757575")
        crit_chip = f"<span style='background:{cc}; color:white; padding:2px 10px; border-radius:12px; font-size:0.85em; font-weight:600;'>{_html.escape(str(crit))}</span>"

    html = f"""
    <div class='node-header-card'>
      <div style='display:flex; align-items:center; gap:10px; margin-bottom:8px;'>
        <span class='node-type-badge' style='background:{cfg["bg"]}; color:{cfg["color"]};'>{cfg["icon"]} {_html.escape(str(type_label))}</span>
        <span class='node-status-badge' style='background:{status_color}20; color:{status_color};'>{_html.escape(status or "\u2014")}</span>
      </div>
      <div style='font-size:1.5em; font-weight:700; margin-bottom:8px;'>{_html.escape(str(node.get("name", "\u2014")))}</div>
      <div style='display:flex; gap:8px; flex-wrap:wrap;'>
        {code_chip} {tag_chip} {crit_chip}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ── Render: info card ─────────────────────────────────────────────────

def render_info_card(title: str, data: dict):
    """Render a key-value info card."""
    rows_html = ""
    for k, v in data.items():
        if v:
            rows_html += f"<div class='info-row'><span class='info-key'>{_html.escape(str(k))}</span><span class='info-val'>{_html.escape(str(v))}</span></div>"
    if not rows_html:
        rows_html = "<div class='info-row'><span class='info-key' style='color:#999;'>\u2014</span></div>"
    html = f"""
    <div class='info-card'>
      <div class='info-card-title'>{title}</div>
      {rows_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ── Common: plant selector + node loader ──────────────────────────────

def load_plant_and_nodes(key_prefix="tree"):
    """Render plant selector and load nodes. Returns (plant_id, nodes, node_map, children_map, root_ids) or stops page."""
    try:
        plants = api_client.list_plants()
    except Exception:
        st.warning(t("common.cannot_connect_start"))
        st.stop()

    if not plants:
        st.info(t("hierarchy.no_plants"))
        st.stop()

    plant_names = {p["plant_id"]: p["name"] for p in plants}
    selected_plant = st.selectbox(
        t("hierarchy.select_plant"),
        list(plant_names.keys()),
        format_func=lambda x: plant_names[x],
        key=f"{key_prefix}_plant_select",
    )

    nodes = api_client.list_nodes(plant_id=selected_plant)
    node_map, children_map, root_ids = build_tree(nodes)

    return selected_plant, nodes, node_map, children_map, root_ids
