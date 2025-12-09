import streamlit as st
import pandas as pd
from frontend.services.admin_service import get_count_validation, get_system_stats
from frontend.components.css_loader import dashboard_css


def render_count_validation():
    dashboard_css()

    # Initialize session state
    if 'show_counts' not in st.session_state:
        st.session_state.show_counts = False
    if 'show_system' not in st.session_state:
        st.session_state.show_system = False

    # Header
    st.markdown("""
    <div class="esewa-header">
        <div class="header-content">
            <h1>📊 System Statistics</h1>
            <p>Monitor system performance and data consistency</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Control buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Check Counts", use_container_width=True):
            with st.spinner("Loading..."):
                try:
                    response = get_count_validation()
                    st.session_state['count_data'] = response.json()
                    st.session_state.show_counts = True
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        if st.button("⚙️ System Info", use_container_width=True):
            with st.spinner("Loading..."):
                try:
                    response = get_system_stats()
                    st.session_state['system_stats'] = response.json()
                    st.session_state.show_system = True
                except Exception as e:
                    st.error(f"Error: {e}")

    with col3:
        if st.button("🗑️ Clear Data", use_container_width=True):
            st.session_state.show_counts = False
            st.session_state.show_system = False
            if 'count_data' in st.session_state:
                del st.session_state['count_data']
            if 'system_stats' in st.session_state:
                del st.session_state['system_stats']

    # Display system stats table
    if st.session_state.show_system and 'system_stats' in st.session_state:
        st.subheader("🖥️ System Information")
        stats = st.session_state['system_stats']
        system = stats.get('system', {})

        system_data = {
            'Property': ['Operating System', 'CPU Cores', 'CPU Threads', 'Memory (GB)', 'Collection', 'Indexing Mode'],
            'Value': [
                system.get('os', 'N/A'),
                system.get('cpu_cores', 'N/A'),
                system.get('cpu_threads', 'N/A'),
                system.get('memory_gb', 'N/A'),
                stats.get('collection', 'N/A'),
                stats.get('indexing_mode', 'N/A')
            ]
        }

        system_df = pd.DataFrame(system_data)
        st.dataframe(system_df, use_container_width=True, hide_index=True)

    # Display counts table
    if st.session_state.show_counts and 'count_data' in st.session_state:
        st.subheader("📊 Data Count Statistics")
        data = st.session_state['count_data']

        count_data = {
            'Storage System': ['Total Count', 'Source Files', 'Buffer', 'Milvus Vector DB', 'Elasticsearch'],
            'Record Count': [
                data.get('actual_count', 0),
                data.get('source_file_count', 0),
                data.get('upsert_count', 0),
                data.get('milvus_count', 0),
                data.get('elasticsearch_count', 0)
            ],
            'Status': ['✅ Reference', '📁 Source', '⏳ Pending', '🔍 Indexed', '🔎 Searchable']
        }

        count_df = pd.DataFrame(count_data)
        st.dataframe(count_df, use_container_width=True, hide_index=True)

        actual = data.get('actual_count', 0)
        milvus = data.get('milvus_count', 0)
        elasticsearch = data.get('elasticsearch_count', 0)

        st.subheader("✅ Validation Summary")
        validation_data = {
            'Check': ['Milvus Sync', 'Elasticsearch Sync'],
            'Expected': [actual, actual],
            'Actual': [milvus, elasticsearch],
            'Status': [
                '✅ Synced' if actual == milvus else f'⚠️ Off by {abs(actual - milvus)}',
                '✅ Synced' if actual == elasticsearch else f'⚠️ Off by {abs(actual - elasticsearch)}'
            ]
        }

        validation_df = pd.DataFrame(validation_data)
        st.dataframe(validation_df, use_container_width=True, hide_index=True)
