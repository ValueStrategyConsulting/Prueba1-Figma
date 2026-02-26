"""Shared CSS styling for OCP Maintenance AI Streamlit app.

Design system: Enterprise-grade industrial asset management.
Palette: OCP Green (#1B5E20) primary, neutral grays, white cards.
Typography: Inter font, tight letter-spacing for data-heavy screens.

Performance: All base CSS is injected in a SINGLE st.markdown() call
to minimize component overhead. Page-specific styles are separate.
"""

import streamlit as st


# =====================================================================
# BASE CSS — single string, injected once
# =====================================================================

_BASE_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    /* ═══ 1. FONTS ═══ */
    .stApp, .stApp * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    .stApp { background: #F1F5F9; }

    /* ═══ 2. FOUT FIX — hide icon buttons while Material Symbols loads ═══ */
    @keyframes fade-in-btn { to { opacity: 1; } }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stHeader"] button {
        opacity: 0 !important;
        animation: fade-in-btn 0.01s 0.6s forwards !important;
    }

    /* ═══ 3. SIDEBAR ═══ */
    section[data-testid="stSidebar"] { background: #1B3A26; }

    /* All sidebar buttons default to light text */
    section[data-testid="stSidebar"] button { color: #C8E6C9 !important; }

    /* Labels */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] label span,
    section[data-testid="stSidebar"] label p,
    section[data-testid="stSidebar"] label div {
        color: #A5D6A7 !important;
        font-size: 0.78rem !important;
    }

    /* Markdown / paragraphs */
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] .stAlert p {
        color: #D1E7D8 !important;
    }

    /* Nav page links */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
        color: #C8E6C9 !important;
        border-radius: 8px; padding: 6px 12px; margin: 1px 8px;
        font-weight: 500; font-size: 0.88rem; transition: all 0.15s ease;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a p {
        color: inherit !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
        background: rgba(255,255,255,0.08); color: white !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] {
        background: rgba(255,255,255,0.12); color: white !important; font-weight: 700;
    }

    /* "View N more" nav button */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] button,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] button span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] button p {
        color: #A5D6A7 !important; background: transparent !important;
    }

    /* Submit / action buttons (dark text on light bg) */
    section[data-testid="stSidebar"] .stButton button,
    section[data-testid="stSidebar"] .stButton button span,
    section[data-testid="stSidebar"] .stButton button p {
        color: #1B3A26 !important; background: #C8E6C9 !important;
        border: none !important; font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] .stButton button span,
    section[data-testid="stSidebar"] .stButton button p { background: transparent !important; }
    section[data-testid="stSidebar"] .stButton button:hover,
    section[data-testid="stSidebar"] .stButton button:hover span {
        color: #1B3A26 !important; background: white !important;
    }
    section[data-testid="stSidebar"] .stButton button:hover span { background: transparent !important; }

    /* ═══ 4. MAIN CONTENT ═══ */

    /* Layout */
    .block-container { padding: 2rem 3rem !important; max-width: 1400px; }

    /* Page Titles */
    h1 {
        color: #111827 !important; font-weight: 800 !important;
        font-size: 1.75rem !important; letter-spacing: -0.02em; margin-bottom: 0 !important;
    }
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #6B7280 !important; font-size: 0.88rem !important; margin-top: 2px;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background: white; border: 1px solid #E5E7EB; border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
        transition: all 0.2s ease;
    }
    [data-testid="stMetric"]:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); transform: translateY(-1px); }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; color: #6B7280 !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { font-size: 1.75rem !important; font-weight: 800 !important; color: #111827 !important; }
    [data-testid="stMetricDelta"] { font-size: 0.78rem !important; font-weight: 600 !important; }

    /* Buttons */
    .stButton > button {
        border-radius: 8px !important; font-weight: 600 !important;
        font-size: 0.85rem !important; letter-spacing: 0.01em;
        transition: all 0.2s ease !important;
        border: 1px solid #E5E7EB !important; padding: 8px 20px !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%) !important;
        border: none !important; color: white !important;
        box-shadow: 0 2px 4px rgba(27,94,32,0.2);
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2E7D32 0%, #388E3C 100%) !important;
        box-shadow: 0 4px 12px rgba(27,94,32,0.35) !important; transform: translateY(-1px);
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: #1B5E20 !important; color: #1B5E20 !important; background: #F0FFF0 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0; background: white; border: 1px solid #E5E7EB; border-radius: 10px; padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; padding: 8px 20px; font-weight: 600; font-size: 0.82rem; color: #6B7280;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background: #1B5E20 !important; color: white !important; }
    .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

    /* Inputs */
    .stSelectbox > div > div, .stTextInput > div > div, .stTextArea textarea {
        border-radius: 8px !important; border-color: #E5E7EB !important; font-size: 0.88rem !important;
    }
    .stSelectbox > div > div:focus-within, .stTextInput > div > div:focus-within, .stTextArea textarea:focus {
        border-color: #1B5E20 !important; box-shadow: 0 0 0 2px rgba(27,94,32,0.15) !important;
    }
    .stSelectbox label, .stTextInput label, .stTextArea label {
        font-size: 0.82rem !important; font-weight: 600 !important; color: #374151 !important;
    }

    /* DataFrames */
    .stDataFrame { border: 1px solid #E5E7EB; border-radius: 10px; overflow: hidden; }
    .stDataFrame thead th {
        background: #1B5E20 !important; color: white !important;
        font-weight: 600 !important; font-size: 0.78rem !important;
        text-transform: uppercase; letter-spacing: 0.04em;
    }
    .stDataFrame tbody tr:hover { background: #F8FFF8 !important; }

    /* Expanders */
    .streamlit-expanderHeader { font-weight: 700 !important; color: #1B5E20 !important; font-size: 0.88rem !important; }
    .stExpander { border: 1px solid #E5E7EB !important; border-radius: 10px !important; background: white; }

    /* Dividers */
    hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #D1D5DB, transparent); margin: 24px 0; }

    /* Subheaders */
    h2, h3 { color: #111827 !important; font-weight: 700 !important; letter-spacing: -0.01em; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

    /* Multiselect chips */
    [data-baseweb="tag"] { background: #E8F5E9 !important; color: #1B5E20 !important; border-radius: 6px !important; font-weight: 600 !important; }

    /* Progress bars */
    .stProgress > div > div { background: linear-gradient(90deg, #1B5E20, #4CAF50) !important; border-radius: 4px; }

    /* Hide Streamlit toolbar (accessibility icon, etc.) */
    [data-testid="stToolbar"] { display: none !important; }

    /* Alerts */
    .stAlert { border-radius: 10px !important; }

    /* Mobile */
    @media (max-width: 768px) {
        .block-container { padding: 1rem 1rem !important; }
        h1 { font-size: 1.3rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
        [data-testid="stMetric"] { padding: 12px 14px; }
        .stButton > button { padding: 10px 16px !important; font-size: 0.9rem !important; }
    }
</style>
"""


# =====================================================================
# PUBLIC API — called by pages
# =====================================================================

def apply_style():
    """Inject base OCP-branded CSS — ALL in ONE st.markdown() call."""
    st.markdown(_BASE_CSS, unsafe_allow_html=True)


def apply_mvp_style():
    """Enhanced CSS for MVP demo pages — builds on apply_style()."""
    apply_style()


# =====================================================================
# PAGE-SPECIFIC STYLES — each is a single st.markdown()
# =====================================================================

def apply_hierarchy_style():
    """Inject modern hierarchy-specific CSS."""
    st.markdown("""
    <style>
        .tree-panel-header {
            font-size: 0.72rem; font-weight: 700; color: #6B7280;
            text-transform: uppercase; letter-spacing: 0.08em;
            padding: 10px 0 8px; border-bottom: 2px solid #E5E7EB; margin-bottom: 6px;
        }
        .tree-container { max-height: 65vh; overflow-y: auto; padding-right: 4px; }
        .tree-container::-webkit-scrollbar { width: 4px; }
        .tree-container::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 4px; }

        [aria-label="Asset Tree"] { gap: 0px !important; }
        [aria-label="Asset Tree"] [data-baseweb="radio"] {
            font-family: 'Inter', system-ui, sans-serif !important;
            font-size: 0.82rem !important; padding: 5px 10px !important; margin: 0 !important;
            border-radius: 6px; cursor: pointer; transition: all 0.12s ease;
            white-space: pre !important; border-left: 3px solid transparent; line-height: 1.5;
        }
        [aria-label="Asset Tree"] [data-baseweb="radio"]:hover { background: #F1F5F9; }
        [aria-label="Asset Tree"] [data-baseweb="radio"]:has(input:checked) {
            background: #E8F5E9; border-left: 3px solid #1B5E20; font-weight: 600 !important;
        }
        [aria-label="Asset Tree"] [data-baseweb="radio"] > div:first-child { display: none !important; }
        [aria-label="Asset Tree"] input[type="radio"] { display: none !important; }

        .hierarchy-breadcrumb {
            background: white; border: 1px solid #E5E7EB; border-radius: 10px;
            padding: 10px 16px; font-size: 0.82rem; margin-bottom: 16px;
            display: flex; align-items: center; flex-wrap: wrap; gap: 2px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .bc-sep { color: #D1D5DB; margin: 0 6px; font-size: 0.7rem; }
        .bc-item { font-weight: 500; color: #6B7280; }
        .bc-current { font-weight: 700; color: #111827; }

        .node-header-card {
            background: white; border: 1px solid #E5E7EB; border-radius: 14px;
            padding: 24px 28px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }
        .node-header-top { display: flex; gap: 10px; align-items: center; margin-bottom: 8px; }
        .node-type-badge {
            display: inline-flex; align-items: center; gap: 4px; padding: 4px 12px;
            border-radius: 20px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.03em;
        }
        .node-status-badge {
            padding: 3px 10px; border-radius: 12px; font-size: 0.68rem;
            font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;
        }
        .status-active { background: #DCFCE7; color: #166534; }
        .status-inactive { background: #FEE2E2; color: #991B1B; }
        .node-title {
            font-size: 1.35rem; font-weight: 800; color: #111827;
            margin: 4px 0 8px; letter-spacing: -0.02em;
        }
        .node-meta-row { display: flex; gap: 8px; flex-wrap: wrap; }
        .meta-chip {
            background: #F1F5F9; padding: 4px 10px; border-radius: 6px;
            font-size: 0.75rem; color: #475569;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
        }
        .crit-chip { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; color: white; }

        .info-card {
            background: white; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 18px 22px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .info-card-title {
            font-size: 0.72rem; font-weight: 700; color: #6B7280;
            text-transform: uppercase; letter-spacing: 0.06em;
            padding-bottom: 10px; margin-bottom: 10px; border-bottom: 1px solid #F1F5F9;
        }
        .info-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #F8FAFC; }
        .info-row:last-child { border-bottom: none; }
        .info-label { color: #6B7280; font-size: 0.8rem; }
        .info-value { color: #111827; font-size: 0.8rem; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

        .spec-card {
            background: white; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 18px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            transition: all 0.2s ease;
        }
        .spec-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .spec-icon { font-size: 1.5rem; margin-bottom: 4px; }
        .spec-value { font-size: 1.1rem; font-weight: 800; color: #111827; }
        .spec-label { font-size: 0.65rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }

        .empty-state { text-align: center; padding: 60px 20px; color: #9CA3AF; }
        .empty-icon { font-size: 3rem; margin-bottom: 16px; opacity: 0.4; }
        .empty-state h3 { color: #6B7280; font-weight: 700; margin: 0 0 8px; }
        .empty-state p { color: #9CA3AF; font-size: 0.88rem; margin: 0; }

        .stats-pill {
            background: linear-gradient(135deg, #1B5E20, #2E7D32); color: white;
            padding: 6px 14px; border-radius: 20px; font-size: 0.78rem; font-weight: 700;
            display: inline-block;
        }
    </style>
    """, unsafe_allow_html=True)


def apply_r8_module_style():
    """Inject R8-style module CSS for FMEA, Strategy, Work Packages, FMECA pages."""
    st.markdown("""
    <style>
        .r8-toolbar {
            display: flex; gap: 6px; align-items: center; padding: 10px 0;
            border-bottom: 1px solid #E5E7EB; margin-bottom: 14px; flex-wrap: wrap;
        }
        .r8-toolbar .stButton > button {
            font-size: 0.75rem !important; padding: 5px 14px !important;
            border-radius: 6px !important; background: white !important;
            border: 1px solid #E5E7EB !important; color: #374151 !important; font-weight: 600 !important;
        }
        .r8-toolbar .stButton > button:hover {
            background: #F0FFF0 !important; border-color: #1B5E20 !important; color: #1B5E20 !important;
        }
        .r8-filter-bar {
            background: white; border: 1px solid #E5E7EB; border-radius: 8px;
            padding: 10px 14px; margin-bottom: 14px; font-size: 0.82rem;
        }
        .r8-form-card {
            background: white; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 20px 24px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .r8-form-title {
            font-size: 0.72rem; font-weight: 700; color: #6B7280;
            text-transform: uppercase; letter-spacing: 0.06em;
            padding-bottom: 10px; margin-bottom: 12px; border-bottom: 1px solid #F1F5F9;
        }
        .r8-chip {
            display: inline-block; padding: 3px 10px; border-radius: 12px;
            font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;
        }
        .r8-chip-draft { background: #FFF7ED; color: #C2410C; }
        .r8-chip-approved { background: #DCFCE7; color: #166534; }
        .r8-chip-reviewed { background: #DBEAFE; color: #1E40AF; }
        .r8-chip-recommended { background: #F3E8FF; color: #6B21A8; }
        .r8-action-row { display: flex; gap: 6px; padding: 8px 0; flex-wrap: wrap; }
        .r8-grid-container { border: 1px solid #E5E7EB; border-radius: 10px; overflow: hidden; margin-bottom: 14px; }
        .r8-detail-section {
            background: #F8FAFC; border: 1px solid #E5E7EB; border-radius: 10px;
            padding: 14px 18px; margin-bottom: 14px;
        }
        .r8-detail-title {
            font-size: 0.7rem; font-weight: 700; color: #6B7280;
            text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;
        }
        .r8-allocator-panel {
            background: white; border: 1px solid #E5E7EB; border-radius: 10px;
            padding: 14px; min-height: 200px;
        }
        .r8-allocator-title {
            font-size: 0.7rem; font-weight: 700; color: #1B5E20;
            text-transform: uppercase; margin-bottom: 8px;
        }
    </style>
    """, unsafe_allow_html=True)


def apply_capture_style():
    """CSS for the Field Capture page — mobile-first, enterprise-grade."""
    st.markdown("""
    <style>
        [data-testid="stSegmentedControl"] {
            background: #F1F5F9 !important; border-radius: 12px !important;
            padding: 4px !important; border: 1px solid #E2E8F0 !important;
        }
        [data-testid="stSegmentedControl"] button {
            border-radius: 10px !important; font-weight: 600 !important;
            font-size: 0.92rem !important; padding: 10px 20px !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stSegmentedControl"] button[aria-pressed="true"] {
            background: linear-gradient(135deg, #166534 0%, #15803D 100%) !important;
            color: white !important; box-shadow: 0 2px 8px rgba(22,101,52,0.25) !important;
        }
        .result-card {
            background: linear-gradient(135deg, #DCFCE7 0%, #BBF7D0 100%);
            border: 1px solid #86EFAC; border-radius: 14px;
            padding: 20px 24px; margin: 16px 0;
        }
        .result-header { font-size: 1.1rem; font-weight: 800; color: #166534; margin-bottom: 12px; }
        .priority-banner { padding: 14px 20px; border-radius: 10px; margin: 10px 0; }
        .history-card {
            background: white; border: 1px solid #E5E7EB; border-radius: 10px;
            padding: 14px 18px; margin-bottom: 8px; transition: all 0.2s ease;
        }
        .history-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); border-color: #D1D5DB; }
        [data-testid="stAudioInput"] {
            border: 2px dashed #D1D5DB !important; border-radius: 12px !important;
            padding: 16px !important; background: #FAFAFA !important;
        }
        [data-testid="stCameraInput"] > div { border-radius: 12px !important; overflow: hidden !important; }
        [data-testid="stFileUploader"] {
            border: 2px dashed #D1D5DB !important; border-radius: 12px !important;
            padding: 16px !important; background: #FAFAFA !important;
        }
        @media (max-width: 768px) {
            [data-testid="stSegmentedControl"] button { padding: 10px 12px !important; font-size: 0.85rem !important; }
            [data-testid="stColumns"] { flex-direction: column !important; }
            [data-testid="stColumns"] > div { width: 100% !important; flex: 1 1 100% !important; }
        }
    </style>
    """, unsafe_allow_html=True)


def apply_wr_style():
    """CSS for the Work Requests review queue page."""
    st.markdown("""
    <style>
        .wr-card {
            background: white; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 18px 22px; margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s ease;
        }
        .wr-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
        .wr-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .wr-equip { font-size: 1.05rem; font-weight: 700; color: #111827; }
        .wr-meta { display: flex; gap: 8px; align-items: center; }
        .wr-status {
            padding: 4px 12px; border-radius: 20px;
            font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;
        }
        .wr-body { display: flex; gap: 16px; flex-wrap: wrap; font-size: 0.82rem; color: #6B7280; }
        .status-pill { padding: 6px 16px; border-radius: 20px; font-size: 0.78rem; font-weight: 700; display: inline-block; }
        .pill-draft { background: #FFF7ED; color: #C2410C; }
        .pill-pending { background: #FFFBEB; color: #B45309; }
        .pill-validated { background: #DCFCE7; color: #166534; }
        .pill-rejected { background: #FEE2E2; color: #991B1B; }
    </style>
    """, unsafe_allow_html=True)
