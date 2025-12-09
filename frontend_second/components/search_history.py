import streamlit as st
import requests
from datetime import datetime
import html
from backend_second.utils.config import HISTORY_API_SECOND


def render_search_history():
    with st.container():
        st.markdown('<div class="esewa-card">', unsafe_allow_html=True)
        st.markdown("## 🕒 Search History")

        with st.spinner("Fetching history..."):
            try:
                response = requests.get(HISTORY_API_SECOND)
                data = response.json()

                if "error" in data:
                    st.error(f"Error retrieving history: {data['error']}")
                else:
                    history = data.get("history", [])
                    if not history:
                        st.info("No search history found.")
                    else:
                        # Debug: show count
                        st.markdown(f"### 🔍 Total History Items: {len(history)}")

                        sorted_history = sorted(
                            history,
                            key=lambda x: x.get("timestamp", ""),
                            reverse=True
                        )[:10]

                        st.markdown(f"**Displaying latest {len(sorted_history)} searches:**")

                        # Use columns for better layout
                        for i, hq in enumerate(sorted_history):
                            raw_query = html.escape(hq.get("raw_query", "No query"))
                            timestamp = hq.get("timestamp", "-")

                            # Format timestamp
                            if timestamp != "-":
                                try:
                                    dt = datetime.fromisoformat(timestamp)
                                    formatted_ts = dt.strftime("%b %d, %Y %H:%M")
                                except:
                                    formatted_ts = timestamp
                            else:
                                formatted_ts = "Unknown date"

                            # Use Streamlit components instead of custom HTML
                            with st.container():
                                # Create a styled container using Streamlit's built-in styling
                                col1, col2 = st.columns([4, 1])

                                with col1:
                                    st.markdown(f"**🔍 {raw_query}**")

                                with col2:
                                    st.markdown(f"*{formatted_ts}*")

                                # Unique expander for each item
                                with st.expander(f"View Query Details #{i + 1}", expanded=False):
                                    parsed_query = hq.get("parsed_query", {})
                                    if parsed_query:
                                        st.markdown("### Query Analysis")

                                        st.markdown(f"**Original Query:** {raw_query}")

                                        if "intent" in parsed_query:
                                            st.markdown(f"**Detected Intent:** {parsed_query['intent']}")

                                        if "entities" in parsed_query and parsed_query["entities"]:
                                            st.markdown("**Extracted Entities:**")
                                            for entity, value in parsed_query["entities"].items():
                                                st.markdown(f"- **{entity.capitalize()}:** {value}")

                                        if "filters" in parsed_query and parsed_query["filters"]:
                                            st.markdown("**Applied Filters:**")
                                            has_filters = False
                                            for filter_name, filter_value in parsed_query["filters"].items():
                                                if filter_value:
                                                    if isinstance(filter_value, list):
                                                        filter_value = ", ".join(filter_value)
                                                    st.markdown(f"- **{filter_name.capitalize()}:** {filter_value}")
                                                    has_filters = True
                                            if not has_filters:
                                                st.markdown("No filters applied")

                                        if st.button("Show Raw JSON", key=f"raw_json_btn_{i}_{hash(raw_query)}"):
                                            st.json(parsed_query)
                                    else:
                                        st.info("No parsed query details available")

                                # Add separator
                                st.markdown("---")

            except Exception as e:
                st.error(f"Error fetching history: {e}")

        st.markdown('</div>', unsafe_allow_html=True)