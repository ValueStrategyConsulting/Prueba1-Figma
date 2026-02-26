"""Page 10: Planner Assistant — M2 AI Recommendations."""

import logging
logger = logging.getLogger("05_planner")

import streamlit as st
from streamlit_app import api_client
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_mvp_style
from streamlit_app.components.feedback import feedback_widget

st.set_page_config(page_title="Planner Assistant", page_icon="🧠", layout="wide")
page_init()
apply_mvp_style()

st.title(t("planner.title"))
st.markdown(t("planner.subtitle"))

@st.cache_data(ttl=120, show_spinner=False)
def _load_work_requests():
    try:
        return api_client.list_work_requests()
    except Exception:
        return []

# Load work requests for selection
work_requests = _load_work_requests()

if not work_requests:
    st.info(t("planner.no_requests"))
    st.stop()

# Select work request
wr_options = {f"{wr['request_id'][:12]}... | {wr.get('equipment_tag', 'N/A')} [{wr.get('status', '')}]": wr for wr in work_requests}
selected_label = st.selectbox(t("planner.select_wr"), list(wr_options.keys()))
selected_wr = wr_options[selected_label]

col1, col2, col3 = st.columns(3)
col1.metric(t("planner.equipment"), selected_wr.get("equipment_tag", "N/A"))
col2.metric(t("planner.status"), selected_wr.get("status", "N/A"))
ai = selected_wr.get("ai_classification") or {}
col3.metric(t("planner.ai_priority"), ai.get("priority_suggested", "N/A"))

st.divider()

if st.button(t("planner.generate_recommendation"), type="primary"):
    try:
        rec = api_client.generate_recommendation(selected_wr["request_id"])
        st.session_state["last_recommendation"] = rec
        st.success(t("planner.recommendation_generated"))
    except Exception as e:
        st.error(f"Error: {e}")

# Display recommendation
rec = st.session_state.get("last_recommendation")
if rec:
    st.subheader(t("planner.ai_recommendation"))

    col_a, col_b, col_c = st.columns(3)
    action = rec.get("planner_action", "N/A")
    action_color = {"APPROVE": "green", "MODIFY": "orange", "ESCALATE": "red", "DEFER": "blue"}.get(action, "gray")
    col_a.metric(t("planner.suggested_action"), action)
    col_b.metric(t("planner.confidence"), f"{rec.get('ai_confidence', 0):.0%}")
    col_c.metric(t("planner.risk_level"), rec.get("risk_level", "N/A"))

    tab_res, tab_sched, tab_risk = st.tabs([t("planner.tab_resources"), t("planner.tab_scheduling"), t("planner.tab_risk")])

    with tab_res:
        ra = rec.get("resource_analysis", {})
        st.markdown(t("planner.workforce_availability"))
        for wf in ra.get("workforce_available", []):
            st.markdown(f"- {wf.get('specialty', 'N/A')}: {wf.get('technicians_available', 0)} available")
        st.markdown(t("planner.materials_status"))
        ms = ra.get("materials_status", {})
        if ms.get("all_available"):
            st.success(t("planner.all_materials_available"))
        else:
            st.warning(t("planner.materials_missing", count=len(ms.get('missing_items', []))))

    with tab_sched:
        ss = rec.get("scheduling_suggestion", {})
        st.markdown(f"**Recommended Date:** {ss.get('recommended_date', 'N/A')}")
        st.markdown(f"**Shift:** {ss.get('recommended_shift', 'N/A')}")
        st.markdown(f"**Reasoning:** {ss.get('reasoning', 'N/A')}")
        if ss.get("conflicts"):
            st.warning("Conflicts: " + ", ".join(ss["conflicts"]))
        if ss.get("groupable_with"):
            st.info(f"Can be grouped with {len(ss['groupable_with'])} backlog item(s)")

    with tab_risk:
        ra = rec.get("risk_assessment", {})
        st.markdown(f"**Risk Level:** {ra.get('risk_level', 'N/A')}")
        for rf in ra.get("risk_factors", []):
            st.markdown(f"- {rf}")
        st.markdown(f"**Recommendation:** {ra.get('recommendation', 'N/A')}")

    st.divider()
    st.subheader(t("planner.planner_actions"))
    col_act1, col_act2, col_act3, col_act4 = st.columns(4)
    rec_id = rec.get("recommendation_id", "")

    for col, action in [(col_act1, "APPROVE"), (col_act2, "MODIFY"), (col_act3, "ESCALATE"), (col_act4, "DEFER")]:
        if col.button(action, key=f"action_{action}"):
            try:
                result = api_client.apply_planner_action(rec_id, action)
                st.success(t("planner.action_applied", action=action))
                st.json(result)
            except Exception as e:
                st.error(str(e))

feedback_widget("planner")
