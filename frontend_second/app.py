import streamlit as st
import sys, os
from components.css_loader import load_css

# Set page config
st.set_page_config(
    page_title="eSewa AI",
    page_icon="💳",
    layout="centered"
)

load_css()

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

backend_dir = os.path.join(project_root, "backend_second")
sys.path.append(backend_dir)

from frontend_second.pages.search import render_search

st.markdown("""
<div class="esewa-header" style="padding: 1rem; margin-bottom: 1.5rem;">
    <div style="display: flex; align-items: center; gap: 1rem;">
        <h1 style="margin:0;">eSewa AI Search</h1>
        <div style="font-size: 0.9rem; opacity: 0.9;">Financial Intelligence Platform</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation with styled buttons
col1 = st.columns(1)[0]
with col1:
    if st.button("🔍 AI Search", use_container_width=True, type="secondary"):
        st.session_state.page = "search"


# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "search"

# Render selected page
if st.session_state.page == "search":
    render_search()


# Simple footer
st.markdown("---")
st.caption("© 2025 eSewa AI Assistant | Secure Financial Services")