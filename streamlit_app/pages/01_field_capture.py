"""Page 1: Field Capture — AI-Powered Problem Reporting.

Unified capture: Text + Voice + Photo in a single form.
Designed for field technicians on mobile devices.
"""

import logging
logger = logging.getLogger("01_field_capture")

import html as _html
import streamlit as st
from streamlit_app import api_client
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_mvp_style, apply_capture_style
from streamlit_app.components.feedback import feedback_widget

st.set_page_config(page_title="Report a Problem", page_icon=":wrench:", layout="wide")
page_init()
apply_mvp_style()
apply_capture_style()

st.title(t("capture.title"))
st.caption(t("capture.subtitle"))


# ── Helpers ──────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def _load_equipment_options():
    try:
        items = api_client.list_equipment_tags()
        return [f"{it['tag']} — {it['name']}" for it in items if it.get("tag")]
    except Exception as e:
        logger.exception("Unexpected error")
        return []


_PRIORITY_COLORS = {
    "1_EMERGENCY": ("#991B1B", "#FEE2E2"),
    "2_URGENT": ("#C2410C", "#FFF7ED"),
    "3_NORMAL": ("#1E40AF", "#DBEAFE"),
    "4_PLANNED": ("#166534", "#DCFCE7"),
}

_TYPE_EMOJIS = {"TEXT": "\u2328\ufe0f", "VOICE": "\U0001f3a4", "IMAGE": "\U0001f4f7", "VOICE+IMAGE": "\U0001f3a4"}


# ── Common Options ───────────────────────────────────────────────

col_eq, col_loc, col_lang = st.columns(3)
with col_eq:
    equip_options = _load_equipment_options()
    equip_choice = st.selectbox(
        t("capture.equipment_select"),
        options=[""] + equip_options,
        format_func=lambda x: x if x else t("capture.auto_detect"),
        key="cap_equip",
    )
with col_loc:
    location = st.text_input(
        t("capture.location_hint"),
        placeholder="e.g., Grinding area, level 2",
        key="cap_loc",
    )
with col_lang:
    lang = st.selectbox(
        t("capture.language"),
        ["en", "fr", "es", "ar"],
        format_func=lambda x: {"en": "English", "fr": "Français", "es": "Español", "ar": "العربية"}[x],
        key="cap_lang",
    )

st.divider()

# ── Unified Capture Form ─────────────────────────────────────────

raw_text = st.text_area(
    t("capture.describe_problem"),
    placeholder=t("capture.text_placeholder"),
    height=140,
    key="cap_text",
)

col_voice, col_photo = st.columns(2)

with col_voice:
    st.markdown(f"**{t('capture.voice_label')}**")
    audio_data = st.audio_input(
        t("capture.voice_record"),
        key="cap_voice",
    )
    if audio_data:
        st.audio(audio_data)

with col_photo:
    st.markdown(f"**{t('capture.photo_label')}**")
    file_photos = st.file_uploader(
        t("capture.photo_upload"),
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="cap_photos",
    )
    uploaded_photos = []
    if file_photos:
        for f in file_photos[:4]:
            uploaded_photos.append((f.name, f))
        st.markdown(f"**{len(uploaded_photos)}** {t('capture.photos_attached')}")

# Determine capture type based on what the user provided
has_text = bool(raw_text and raw_text.strip())
has_voice = bool(audio_data)
has_photos = bool(uploaded_photos)

if has_voice and has_photos:
    capture_type = "VOICE+IMAGE"
elif has_voice:
    capture_type = "VOICE"
elif has_photos:
    capture_type = "IMAGE"
else:
    capture_type = "TEXT"

can_submit = has_text

# ── Submit Button ─────────────────────────────────────────────────

submitted = st.button(
    t("capture.analyze_btn"),
    type="primary",
    use_container_width=True,
    disabled=not can_submit,
)


# ── Process capture ──────────────────────────────────────────────

if submitted and can_submit:
    tag_manual = equip_choice.split(" — ")[0] if equip_choice else None

    data = {
        "technician_id": "TECH-001",
        "technician_name": "Field Technician",
        "capture_type": capture_type,
        "language": lang,
        "equipment_tag_manual": tag_manual,
        "location_hint": location or None,
        "raw_text_input": raw_text,
    }

    if capture_type == "VOICE":
        data["raw_voice_text"] = raw_text

    with st.spinner(t("capture.analyzing")):
        try:
            result = api_client.submit_capture(data)
            st.session_state["last_capture_result"] = result
            st.session_state["last_capture_wr_id"] = result.get("work_request_id")
        except Exception as e:
            st.error(f"Error: {e}")


# ── AI Result Card ───────────────────────────────────────────────

if "last_capture_result" in st.session_state:
    result = st.session_state["last_capture_result"]
    confidence = result.get("equipment_confidence", 0)
    priority = result.get("priority_suggested", "N/A")
    equip_tag = result.get("equipment_tag", "UNKNOWN")
    failure = result.get("failure_mode_detected")
    spare_count = result.get("spare_parts_count", 0)
    p_text, p_bg = _PRIORITY_COLORS.get(priority, ("#6B7280", "#F1F5F9"))

    st.markdown(f"""
    <div class='result-card'>
        <div class='result-header'>{t("capture.analysis_complete")}</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("capture.detected_equipment"), equip_tag)
    c2.metric(t("capture.confidence"), f"{confidence:.0%}")
    c3.metric(t("capture.failure_mode"), failure or "None detected")
    c4.metric(t("capture.spare_parts"), f"{spare_count} suggested")

    st.markdown(f"""
    <div class='priority-banner' style='background:{p_bg}; border-left:4px solid {p_text};'>
        <span style='font-weight:700; color:{p_text}; font-size:1.05rem;'>
            Priority: {_html.escape(priority.replace('_', ' '))}
        </span>
        <span style='color:#6B7280; margin-left:12px; font-size:0.88rem;'>
            WR: {_html.escape(result.get("work_request_id", "")[:16])}
        </span>
    </div>
    """, unsafe_allow_html=True)

    wr_id = st.session_state.get("last_capture_wr_id")
    if wr_id:
        try:
            wr_detail = api_client.get_work_request(wr_id)
            with st.expander(t("capture.view_full_analysis"), expanded=False):
                ai = wr_detail.get("ai_classification") or {}
                pd_data = wr_detail.get("problem_description") or {}
                parts = wr_detail.get("spare_parts") or []

                tab_cls, tab_desc, tab_parts = st.tabs([
                    t("capture.tab_classification"),
                    t("capture.tab_description"),
                    t("capture.tab_spare_parts"),
                ])

                with tab_cls:
                    st.markdown(f"**Work Order Type:** {ai.get('work_order_type', 'N/A')}")
                    st.markdown(f"**Estimated Duration:** {ai.get('estimated_duration_hours', 'N/A')} hours")
                    st.markdown(f"**Required Specialties:** {', '.join(ai.get('required_specialties', []))}")
                    st.markdown(f"**Justification:** {ai.get('priority_justification', 'N/A')}")
                    if ai.get("safety_flags"):
                        st.warning(f"Safety Flags: {', '.join(ai['safety_flags'])}")

                with tab_desc:
                    st.info(pd_data.get("structured_description", "N/A"))
                    if pd_data.get("affected_component"):
                        st.markdown(f"**Affected Component:** {pd_data['affected_component']}")
                    if pd_data.get("failure_mode_code"):
                        st.markdown(f"**Failure Mode Code:** {pd_data['failure_mode_code']}")

                with tab_parts:
                    if parts:
                        for part in parts:
                            st.markdown(
                                f"- **{part.get('description', 'N/A')}** "
                                f"(SAP: {part.get('sap_material_code', 'N/A')}, "
                                f"Qty: {part.get('quantity_needed', 0)})"
                            )
                    else:
                        st.info("No spare parts suggested for this issue.")
        except Exception as e:
            logger.exception("Unexpected error")
            pass


# ── Recent Capture History ───────────────────────────────────────

st.divider()
st.subheader(t("capture.recent_history"))

try:
    captures = api_client.list_captures()
    if captures:
        for cap in captures[:10]:
            cap_type = cap.get("capture_type", "TEXT")
            created = (cap.get("created_at") or "")[:16]
            equip_manual = cap.get("equipment_tag_manual") or ""
            text_preview = cap.get("raw_text_preview") or ""
            wr_status = cap.get("work_request_status")
            resolved_tag = cap.get("equipment_tag_resolved") or ""
            cap_priority = cap.get("priority") or ""

            subtitle_parts = []
            if resolved_tag:
                subtitle_parts.append(resolved_tag)
            elif equip_manual:
                subtitle_parts.append(equip_manual)
            if cap_priority:
                subtitle_parts.append(cap_priority.replace("_", " "))
            subtitle = " | ".join(subtitle_parts) if subtitle_parts else cap_type

            type_emoji = _TYPE_EMOJIS.get(cap_type, "\U0001f4cb")
            status_str = wr_status or "CAPTURED"
            s_bg = {"DRAFT": "#FFF7ED", "VALIDATED": "#DCFCE7", "REJECTED": "#FEE2E2"}.get(status_str, "#F1F5F9")
            s_color = {"DRAFT": "#C2410C", "VALIDATED": "#166534", "REJECTED": "#991B1B"}.get(status_str, "#6B7280")

            st.markdown(f"""
            <div class='history-card'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div style='display:flex; align-items:center; gap:10px;'>
                        <span style='font-size:1.1rem;'>{type_emoji}</span>
                        <div>
                            <span style='font-weight:700; color:#111827;'>{subtitle}</span>
                            <span style='color:#9CA3AF; margin-left:8px; font-size:0.78rem;'>{created}</span>
                        </div>
                    </div>
                    <span style='background:{s_bg}; color:{s_color}; padding:4px 12px;
                           border-radius:20px; font-size:0.68rem; font-weight:700;
                           letter-spacing:0.03em;'>{status_str}</span>
                </div>
                <div style='color:#6B7280; font-size:0.82rem; margin-top:6px; padding-left:32px;'>
                    {text_preview}{'...' if len(text_preview) >= 100 else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(t("capture.no_captures"))
except Exception as e:
    st.warning(t("capture.could_not_load", error=str(e)))

feedback_widget("field_capture")
