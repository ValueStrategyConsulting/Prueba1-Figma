"""Lightweight user feedback widget for Streamlit sidebar."""

import streamlit as st


def feedback_widget(page_name: str):
    """Render a toggleable feedback form in the sidebar."""
    from streamlit_app.i18n import t

    show = st.sidebar.toggle(t("feedback.title"), value=False, key=f"fb_show_{page_name}")
    if show:
        rating = st.sidebar.radio(
            t("feedback.rating"),
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: "\u2605" * x + "\u2606" * (5 - x),
            horizontal=True,
            key=f"fb_rating_{page_name}",
        )
        comment = st.sidebar.text_area(
            t("feedback.comment"),
            placeholder=t("feedback.comment_placeholder"),
            key=f"fb_comment_{page_name}",
            height=80,
        )

        if st.sidebar.button(t("feedback.submit"), key=f"fb_submit_{page_name}"):
            try:
                from streamlit_app import api_client
                api_client.submit_feedback({
                    "page": page_name,
                    "rating": rating,
                    "comment": comment or "",
                })
                st.sidebar.success(t("feedback.thank_you"))
            except Exception:
                st.sidebar.warning(t("feedback.error"))
