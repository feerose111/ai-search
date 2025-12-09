import streamlit as st
from frontend.services.admin_service import get_indexing_errors
from datetime import datetime
import time
from frontend.components.css_loader import dashboard_css



def render_indexing_errors():
    dashboard_css()

    st.markdown("""
    <style>

    .error-container {
        background: var(--esewa-card);
        border-left: 4px solid var(--esewa-error);
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: var(--esewa-radius);
        box-shadow: var(--esewa-shadow);
        transition: var(--esewa-transition);
        border: 1px solid rgba(220, 53, 69, 0.1);
    }

    .error-container:hover {
        transform: translateY(-2px);
        box-shadow: var(--esewa-shadow-hover);
    }

    .error-header {
        color: var(--esewa-error);
        font-weight: 600;
        margin-bottom: 0.75rem;
        font-size: 1.1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .error-message {
        background: var(--esewa-light);
        padding: 1rem;
        border-radius: var(--esewa-radius-sm);
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        white-space: pre-wrap;
        word-break: break-word;
        color: var(--esewa-text);
        border: 1px solid var(--esewa-border);
        line-height: 1.5;
    }

    .error-time {
        color: var(--esewa-text-light);
        font-size: 0.85rem;
        margin-top: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .no-errors {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 4px solid var(--esewa-success);
        padding: 2rem;
        text-align: center;
        border-radius: var(--esewa-radius);
        color: #155724;
        box-shadow: var(--esewa-shadow);
        margin: 2rem 0;
    }

    .no-errors h3 {
        color: var(--esewa-success);
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }

    .error-stats {
        background: linear-gradient(135deg, var(--esewa-error) 0%, #c82333 100%);
        padding: 1.5rem;
        border-radius: var(--esewa-radius);
        text-align: center;
        margin-bottom: 2rem;
        color: white;
        font-weight: 600;
        font-size: 1.1rem;
        box-shadow: var(--esewa-shadow);
    }

    .controls-container {
        background: var(--esewa-card);
        padding: 1.5rem;
        border-radius: var(--esewa-radius);
        box-shadow: var(--esewa-shadow);
        margin-bottom: 2rem;
        border: 1px solid var(--esewa-border);
    }

    .refresh-info {
        background: linear-gradient(135deg, var(--esewa-info) 0%, #138496 100%);
        color: white;
        padding: 1rem;
        border-radius: var(--esewa-radius-sm);
        text-align: center;
        margin: 1rem 0;
        font-weight: 500;
    }

    .last-update {
        background: var(--esewa-light);
        border-left: 4px solid var(--esewa-trust-blue);
        padding: 1rem;
        border-radius: var(--esewa-radius-sm);
        color: var(--esewa-text);
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .error-level-badge {
        background: var(--esewa-error);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .error-id {
        background: var(--esewa-light);
        color: var(--esewa-text-light);
        padding: 0.25rem 0.5rem;
        border-radius: var(--esewa-radius-sm);
        font-family: monospace;
        font-size: 0.8rem;
        border: 1px solid var(--esewa-border);
    }

    /* Button styling overrides */
    .stButton > button {
        background: linear-gradient(135deg, var(--esewa-green) 0%, #00C148 100%);
        color: white;
        border: none;
        border-radius: var(--esewa-radius-sm);
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: var(--esewa-transition);
        font-size: 1rem;
        width: 100%;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #00C148 0%, var(--esewa-green) 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 177, 64, 0.3);
    }

    /* Toggle styling */
    .stCheckbox > label {
        color: var(--esewa-text);
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header with eSewa styling
    st.markdown("""
    <div class="esewa-header">
        <div class="header-content">
            <h1>🔍 Indexing Errors</h1>
            <p>Monitor and troubleshoot indexing issues</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'errors' not in st.session_state:
        st.session_state.errors = []
    if 'last_update' not in st.session_state:
        st.session_state.last_update = None

    # Controls with styling
    st.markdown('<div class="controls-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.button("🔄 Refresh Errors", use_container_width=True):
            fetch_errors()

    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.errors = []
            st.session_state.last_update = None
            st.rerun()

    with col3:
        auto_refresh = st.toggle("Auto-refresh", value=False)

    st.markdown('</div>', unsafe_allow_html=True)

    # Auto-refresh functionality
    if auto_refresh:
        # Auto-refresh every 30 seconds
        if st.session_state.get('last_auto_refresh', 0) + 30 < time.time():
            fetch_errors()
            st.session_state.last_auto_refresh = time.time()

        # Show countdown
        remaining = 30 - int(time.time() - st.session_state.get('last_auto_refresh', 0))
        if remaining > 0:
            st.markdown(f"""
            <div class="refresh-info">
                ⏱️ Next refresh in {remaining} seconds
            </div>
            """, unsafe_allow_html=True)

        # Auto-refresh the page
        time.sleep(1)
        st.rerun()

    # Display last update time
    if st.session_state.last_update:
        st.markdown(f"""
        <div class="last-update">
            🕒 Last updated: {st.session_state.last_update.strftime('%H:%M:%S')}
        </div>
        """, unsafe_allow_html=True)

    # Display errors
    display_errors()


def fetch_errors():
    """Fetch errors from the API"""
    try:
        with st.spinner("Fetching errors..."):
            response = get_indexing_errors()
            response.raise_for_status()

            errors = response.json().get("errors", [])
            st.session_state.errors = errors
            st.session_state.last_update = datetime.now()

            if errors:
                st.warning(f"⚠️ Found {len(errors)} error(s)")
            else:
                st.success("✅ No errors found!")

    except Exception as e:
        st.error(f"❌ Failed to fetch errors: {str(e)}")


def display_errors():
    """Display the fetched errors"""
    errors = st.session_state.errors

    if not errors:
        if st.session_state.last_update:
            st.markdown("""
            <div class="no-errors">
                <h3>🎉 All Clear!</h3>
                <p>No indexing errors found. System is running smoothly.</p>
            </div>
            """, unsafe_allow_html=True)
        return

    # Error statistics
    st.markdown(f"""
    <div class="error-stats">
        📊 Total Errors: {len(errors)}
    </div>
    """, unsafe_allow_html=True)

    # Display each error
    for i, error in enumerate(errors, 1):
        error_id = error.get('id', f'error-{i}')
        error_message = error.get('message', 'Unknown error')
        error_timestamp = error.get('timestamp', 'Unknown time')
        error_level = error.get('level', 'ERROR')

        # Format timestamp
        try:
            if error_timestamp and error_timestamp != 'Unknown time':
                dt = datetime.fromisoformat(error_timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                formatted_time = error_timestamp
        except:
            formatted_time = error_timestamp

        st.markdown(f"""
        <div class="error-container">
            <div class="error-header">
                ⚠️ Error #{i}
                <span class="error-level-badge">{error_level}</span>
                <span class="error-id">{error_id}</span>
            </div>
            <div class="error-message">{error_message}</div>
            <div class="error-time">
                🕒 {formatted_time}
            </div>
        </div>
        """, unsafe_allow_html=True)