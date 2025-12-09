import streamlit as st
from frontend.pages.count_validation import render_count_validation
from frontend.pages.fetch_errors import render_indexing_errors
from frontend.pages.system_stats import render_system_stats
from frontend.pages.upsert import render_upsert
from frontend.components.css_loader import load_css


def render_admin():
    load_css()
    st.markdown("""
    <div class="esewa-header" style="padding: 1rem; margin-bottom: 1.5rem;">
        <div style="header-content: flex; align-items: center; gap: 1rem;">
            <h1 style="margin:0;">Admin Dashboard</h1>
            <div style="font-size: 0.9rem; opacity: 0.9;">System management and monitoring</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    if "admin_page" not in st.session_state:
        st.session_state.admin_page = "stats"

    nav_items = [
        ("📊 System Stats", "stats"),
        ("📝 Upsert Document", "upsert"),
        ("❌ Indexing Errors", "errors"),
        ("🏷️ Count Validation", "validation"),

    ]

    cols = st.columns(len(nav_items), gap="large")
    for col, (label, page_key) in zip(cols, nav_items):
        with col:
            if st.button(label, key=f"nav_{page_key}"):
                st.session_state.admin_page = page_key

    # Render selected page
    page = st.session_state.admin_page
    if page == "upsert":
        render_upsert()
    elif page == "errors":
        render_indexing_errors()
    if page == "validation":
        render_count_validation()
    elif page == "stats":
        render_system_stats()

    st.markdown('</div>', unsafe_allow_html=True)
