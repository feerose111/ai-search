import streamlit as st
import requests
import time
from datetime import datetime
from backend.utils.config import ADMIN_API
from frontend.components.css_loader import dashboard_css

from frontend.components.charts import (
    load_query_data,
    chart_intent_frequency,
    chart_word_frequency,
    chart_query_volume,
    chart_query_heatmap,
)


def render_system_stats():
    dashboard_css()

    st.markdown("""
    <style>
    .stats-container { max-width: 1400px; margin: 0 auto; }
    .stats-refresh {
        text-align: center;
        margin: 1rem 0;
    }
    .last-updated {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="esewa-header">
        <div class="header-content">
            <h1>📊 System Statistics Dashboard</h1>
            <p>Comprehensive monitoring of system performance and user interactions</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="stats-container">', unsafe_allow_html=True)

    # Initialize session state
    if 'last_updated' not in st.session_state:
        st.session_state.last_updated = None
    if 'stats_data' not in st.session_state:
        st.session_state.stats_data = None
    if 'stats_status' not in st.session_state:
        st.session_state.stats_status = None

    # Refresh controls
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="stats-refresh">', unsafe_allow_html=True)
            auto_refresh = st.checkbox("🔄 Auto-refresh (10s)", key="auto_refresh")
            refresh_clicked = st.button("🚀 Refresh Data", use_container_width=True, type="primary")
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.last_updated:
            st.markdown(f'<div class="last-updated">Last updated: {st.session_state.last_updated}</div>',
                        unsafe_allow_html=True)

    # Auto-refresh logic
    if auto_refresh:
        countdown_placeholder = st.empty()
        current_time = time.time()
        if 'last_refresh_time' not in st.session_state:
            st.session_state.last_refresh_time = current_time

        time_since_refresh = current_time - st.session_state.last_refresh_time

        if time_since_refresh >= 10:
            st.session_state.last_refresh_time = current_time
            st.rerun()
        else:
            remaining = 10 - int(time_since_refresh)
            countdown_placeholder.info(f"⏱️ Next refresh in {remaining} seconds...")
            time.sleep(1)
            st.rerun()

    # Fetch API stats
    should_fetch_data = (
        refresh_clicked or
        st.session_state.stats_data is None or
        (auto_refresh and 'last_refresh_time' in st.session_state and
         time.time() - st.session_state.last_refresh_time >= 10)
    )

    if should_fetch_data:
        with st.spinner("🔍 Retrieving system statistics..."):
            try:
                res = requests.get(f"{ADMIN_API}/stats", timeout=10)
                res.raise_for_status()
                stats = res.json()

                if not isinstance(stats, dict):
                    raise ValueError("Invalid response format from API")

                st.session_state.stats_data = stats
                st.session_state.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.stats_status = "success"

                if refresh_clicked:
                    st.toast("✅ Statistics retrieved successfully", icon="✅")

            except Exception as e:
                st.session_state.stats_status = "error"
                st.error(f"❌ Error: {str(e)}")
                return

    # Display system stats using simple HTML cards
    if st.session_state.stats_data and st.session_state.stats_status == "success":
        stats = st.session_state.stats_data
        numeric_stats = {k: v for k, v in stats.items() if isinstance(v, (int, float))}

        metrics_list = list(numeric_stats.items())
        rows = [metrics_list[i:i + 4] for i in range(0, len(metrics_list), 4)]

        for row in rows:
            cols = st.columns(len(row))
            for i, (key, value) in enumerate(row):
                with cols[i]:
                    if key in ['memory_usage', 'cpu_usage', 'error_rate']:
                        formatted_value = f"{value}%"
                    elif key == 'uptime':
                        formatted_value = f"{value / 3600:.1f} hrs" if value > 0 else "0 hrs"
                    elif key == 'database_size':
                        formatted_value = f"{value / 1024 / 1024:.1f} MB" if value > 0 else "0 MB"
                    elif isinstance(value, int) and value > 1000:
                        formatted_value = f"{value / 1000:.1f}K"
                    else:
                        formatted_value = str(value)

                    metric_icons = {
                        'active_connections': '👥',
                        'total_requests': '📈',
                        'memory_usage': '💾',
                        'cpu_usage': '⚡',
                        'uptime': '⏱️',
                        'database_size': '🗃️',
                        'cache_hits': '🎯',
                        'error_rate': '⚠️'
                    }

                    icon = metric_icons.get(key, '📊')
                    display_label = key.replace('_', ' ').title()

                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%);
                        padding: 20px;
                        border-radius: 15px;
                        box-shadow: 0 8px 25px rgba(255,107,107,0.3);
                        text-align: center;
                        color: white;
                        margin-bottom: 10px;
                        transition: transform 0.3s ease;
                    ">
                        <div style="font-size: 2.5rem; margin-bottom: 10px;">{icon}</div>
                        <div style="font-size: 1.8rem; font-weight: bold; margin-bottom: 5px;">{formatted_value}</div>
                        <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.5px;">{display_label}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Charts Section - Each chart with unique background
        st.markdown("---")
        st.subheader("📈 Real-Time User Query Insights")

        try:
            import plotly.io as pio
            import streamlit.components.v1 as components

            with st.spinner("Loading query insights..."):
                df = load_query_data()

                if df is None or df.empty:
                    st.warning("📊 No query data available for visualization")
                else:
                    chart_backgrounds = {
                        'query_volume': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        'intent_frequency': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                        'word_frequency': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                        'query_heatmap': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
                    }

                    def render_styled_chart(fig, chart_type, height=500):
                        if fig:
                            plot_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
                            background = chart_backgrounds.get(chart_type, 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')
                            styled_html = f"""
                            <div style="
                                background: {background}; 
                                padding: 2rem; 
                                border-radius: 20px; 
                                box-shadow: 0 15px 35px rgba(0,0,0,0.1); 
                                margin-bottom: 2rem; 
                                border: 1px solid rgba(255,255,255,0.2);
                                backdrop-filter: blur(10px);
                                position: relative;
                                overflow: hidden;
                            ">
                                <div style="
                                    position: absolute;
                                    top: 0;
                                    left: 0;
                                    right: 0;
                                    bottom: 0;
                                    background: rgba(255,255,255,0.05);
                                    border-radius: 20px;
                                "></div>
                                <div style="position: relative; z-index: 1;">
                                    {plot_html}
                                </div>
                            </div>
                            """
                            components.html(styled_html, height=height + 100)
                        else:
                            st.error("Unable to generate chart")

                    # Charts
                    st.markdown("### 📊 Daily Query Volume Trends")
                    fig = chart_query_volume(df)
                    render_styled_chart(fig, 'query_volume', height=450)

                    st.markdown("### 🎯 Query Intent Distribution")
                    fig = chart_intent_frequency(df)
                    render_styled_chart(fig, 'intent_frequency', height=400)

                    st.markdown("### 📝 Most Frequent Words")
                    fig = chart_word_frequency(df)
                    render_styled_chart(fig, 'word_frequency', height=400)

                    st.markdown("### 🌡️ Query Activity Heatmap")
                    fig = chart_query_heatmap(df)
                    render_styled_chart(fig, 'query_heatmap', height=450)

        except Exception as e:
            st.error(f"❌ Error loading query data: {str(e)}")

    elif st.session_state.stats_status == "error":
        st.error("❌ Unable to load system statistics. Please try refreshing the data.")
    else:
        st.info("📊 Click 'Refresh Data' to load system statistics")

    st.markdown('</div>', unsafe_allow_html=True)
