import streamlit as st
import json
from frontend.services.upsert_service import upsert_document, upsert_file
from frontend.components.response_handler import handle_response
from frontend.components.css_loader import dashboard_css

def render_upsert():
    dashboard_css()
    st.markdown("""
    <style>
    .upsert-container {
        max-width: 1000px;
        margin: 0 auto;
    }

    .upsert-tab {
        background: var(--esewa-card);
        border-radius: var(--esewa-radius);
        padding: 1.5rem;
        box-shadow: var(--esewa-shadow);
    }

    .file-uploader {
        border: 2px dashed var(--esewa-border);
        border-radius: var(--esewa-radius-sm);
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }

    .file-uploader:hover {
        border-color: var(--esewa-orange);
    }

    .json-input {
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="esewa-header">
        <div class="header-content">
            <h1>📤 Upsert Documents</h1>
            <p>Add or update documents in the vector database</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="upsert-container">', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📝 Direct Input", "📂 File Upload"])

    with tab1:
        st.markdown('<div class="upsert-tab">', unsafe_allow_html=True)

        st.subheader("JSON Document Input")
        input_type = st.radio("Input format:", ["Single Document", "Batch Documents"],
                              horizontal=True)

        doc_input = st.text_area(
            "Enter JSON:",
            height=300,
            value=st.session_state.get("doc_input", ""),
            key="doc_input_area"
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🚀 Upsert",
                         type="primary",
                         use_container_width=True,
                         key="direct_upsert"):
                process_document(doc_input, input_type)

        with col2:
            if st.button("🗑️ Clear",
                         type="secondary",
                         use_container_width=True,
                         key="clear_input"):
                st.session_state.doc_input = ""
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="upsert-tab">', unsafe_allow_html=True)

        st.subheader("File Upload")
        uploaded_file = st.file_uploader(
            "Upload JSON or CSV file",
            type=["json", "csv"],
            accept_multiple_files=False,
            label_visibility="collapsed"
        )

        if uploaded_file:
            st.info(f"📄 Selected file: {uploaded_file.name}")

            if st.button("🚀 Upsert File",
                         type="primary",
                         use_container_width=True,
                         key="file_upsert"):
                process_file(uploaded_file)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def process_document(doc_input, input_type):
    if not doc_input.strip():
        st.error("Please input data")
        return

    try:
        data = json.loads(doc_input)
        is_batch = input_type == "Batch Documents"

        # Validate structure
        if is_batch and not isinstance(data, list):
            raise ValueError("Batch input must be a JSON array")
        if not is_batch and not isinstance(data, dict):
            raise ValueError("Single document must be a JSON object")

        # Send to backend
        with st.spinner("Upserting..."):
            response = upsert_document(data)
            if handle_response(response, "Upsert successful!"):
                st.session_state.doc_input = ""
                st.toast("✅ Document upserted successfully", icon="✅")

    except json.JSONDecodeError:
        st.error("Invalid JSON format")
    except Exception as e:
        st.error(f"Input error: {str(e)}")


def process_file(uploaded_file):
    try:
        with st.spinner("Processing file..."):
            response = upsert_file(uploaded_file)
            if handle_response(response, "File upsert successful!"):
                st.toast("✅ File upserted successfully", icon="✅")
    except Exception as e:
        st.error(f"Upload error: {str(e)}")