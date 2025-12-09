import streamlit as st

def load_css(css_file_path="frontend_second/css/style.css"):
    with open(css_file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def history_css(css_file_path="frontend_second/css/history_css.css"):
    with open(css_file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def dashboard_css(css_file_path="frontend_second/css/base_dashboard.css"):
    with open(css_file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)