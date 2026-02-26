"""Page 6: SAP Upload Review — approve/reject gate."""

import logging
logger = logging.getLogger("12_sap_review")

import streamlit as st
from streamlit_app import api_client
from streamlit_app.i18n import page_init, t
from streamlit_app.style import apply_mvp_style
from streamlit_app.components.feedback import feedback_widget
from streamlit_app.components.tables import render_data_table, status_badge

st.set_page_config(page_title="SAP Review", layout="wide")
page_init()
apply_mvp_style()

st.title(t("sap.title"))

@st.cache_data(ttl=120, show_spinner=False)
def _load_sap_uploads():
    try:
        return api_client.list_sap_uploads()
    except Exception:
        return []

tab1, tab2 = st.tabs([t("sap.tab_uploads"), t("sap.tab_mock")])

with tab1:
    st.subheader(t("sap.upload_packages"))
    try:
        uploads = _load_sap_uploads()
        if uploads:
            render_data_table(uploads, key_columns=["package_id", "plant_code", "status"])

            # Approval gate
            pending = [u for u in uploads if u.get("status") in ("GENERATED", "REVIEWED")]
            if pending:
                st.subheader(t("sap.pending_approval"))
                selected = st.selectbox(t("sap.select_package"), [u["package_id"] for u in pending])
                st.warning(t("sap.safety_warning"))
                if st.button(t("sap.approve_upload")):
                    result = api_client.approve_sap_upload(selected)
                    st.success(f"Package {selected} approved: {result}")
                    st.rerun()
            else:
                st.info(t("sap.no_pending"))
        else:
            st.info(t("sap.no_packages"))
    except Exception as e:
        logger.exception("Unexpected error")
        st.warning(t("common.cannot_connect"))

with tab2:
    st.subheader(t("sap.mock_explorer"))
    transaction = st.selectbox(t("sap.sap_transaction"), ["IE03", "IW38", "IP10", "MM60", "IL03"])
    if st.button(t("sap.load_mock")):
        try:
            data = api_client.get_sap_mock(transaction)
            if isinstance(data, list):
                st.write(f"**{len(data)} records**")
                render_data_table(data[:50])
            else:
                st.json(data)
        except Exception as e:
            st.error(f"Error: {e}. Run seed first.")

feedback_widget("sap_review")
