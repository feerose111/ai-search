import streamlit as st
import requests
from backend_second.utils.config import SEARCH_API_SECOND
from frontend_second.components.build_nl_query import build_query
from frontend_second.components.css_loader import load_css
from frontend_second.components.search_result import render_search_results
from frontend_second.components.search_history import render_search_history


def render_search():
    load_css()

    # Add custom CSS for clickable header
    st.markdown("""
    <style>
    .clickable-header {
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .clickable-header:hover {
        transform: scale(1.02);
        opacity: 0.9;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="esewa-header clickable-header" onclick="document.getElementById('clear_results').click()">
            <div class="header-content">
                <h1 style="color:white; margin:0; padding:0">eSewa AI Search</h1>
                <p style="color:rgba(255,255,255,0.8); margin:0; padding:0">Search across transactions, products, services, and saved payments</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Hidden button for clearing results
    if st.button("Clear Results", key="clear_results", type="secondary"):
        st.session_state.results = []
        st.session_state.search_performed = False
        st.session_state.filters_visible = False
        st.session_state.show_history = False
        st.session_state.filters = {
            "type": [],
            "category": "",
            "date_from": None,
            "date_to": None,
            "min_amt": None,
            "max_amt": None,
        }
        # Clear the query input as well
        if 'query' in st.session_state:
            st.session_state.query = ""
        st.rerun()

    # Hide the clear button with CSS
    st.markdown("""
    <style>
    button[data-testid="stButton"][key="clear_results"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    # Initialize session state
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'search_performed' not in st.session_state:
        st.session_state.search_performed = False
    if 'filters_visible' not in st.session_state:
        st.session_state.filters_visible = False
    if 'filters' not in st.session_state:
        st.session_state.filters = {
            "type": [],
            "category": "",
            "date_from": None,
            "date_to": None,
            "min_amt": None,
            "max_amt": None,
        }
    if 'show_history' not in st.session_state:
        st.session_state.show_history = False

    # Search controls
    col1, col2, col3 = st.columns([10, 1.5, 3])
    with col1:
        query = st.text_input("Enter your search query:", key="query")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕", key="show_filters"):
            st.session_state.filters_visible = not st.session_state.filters_visible
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🕘 History", key="toggle_history"):
            st.session_state.show_history = not st.session_state.show_history

    # Filter panel
    if st.session_state.filters_visible:
        with st.container():
            st.markdown('<div class="esewa-card">', unsafe_allow_html=True)
            st.markdown("### Filter Options")
            st.session_state.filters['type'] = st.multiselect(
                "Select types",
                options=["Transaction", "Product", "Payment", "Service"],
                key="type"
            )
            st.session_state.filters['category'] = st.text_input("Enter category name", key="category")

            col_date1, col_date2 = st.columns(2)
            st.session_state.filters['date_from'] = col_date1.date_input(
                "From Date", value=None, key="date_from", label_visibility="visible"
            )
            st.session_state.filters['date_to'] = col_date2.date_input(
                "To Date", value=None, key="date_to", label_visibility="visible"
            )

            col_amt1, col_amt2 = st.columns(2)
            min_amt = col_amt1.number_input("Minimum amount", value=0.0, step=1.0, format="%.2f", key="min_amt")
            max_amt = col_amt2.number_input("Maximum amount", value=0.0, step=1.0, format="%.2f", key="max_amt")

            st.session_state.filters['min_amt'] = min_amt if min_amt > 0 else None
            st.session_state.filters['max_amt'] = max_amt if max_amt > 0 else None
            st.markdown("</div>", unsafe_allow_html=True)

    # Search action
    if st.button("Search", key="search_btn", use_container_width=True) and query:
        with st.spinner("Searching..."):
            try:
                full_query = build_query(query, st.session_state.filters)
                st.write(f"Query: {full_query}")

                response = requests.get(SEARCH_API_SECOND, params={"q": full_query})
                st.session_state.results = response.json().get("results", [])
                st.session_state.search_performed = True  # Mark that a search was performed
                if not st.session_state.results:
                    st.warning("No results found for your query.")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend API.")
            except requests.exceptions.HTTPError as http_err:
                st.error(f"HTTP error: {http_err}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

    # Conditional rendering
    if st.session_state.show_history:
        render_search_history()

    render_search_results(st.session_state.results, st.session_state.search_performed)

    st.markdown('</div>', unsafe_allow_html=True)