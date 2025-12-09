import streamlit as st
from datetime import datetime
import html
import re

def render_search_results(results, search_performed=False):
    if results:
        st.success(f"🔎 Found {len(results)} result(s):")
        for i, res in enumerate(results, 1):
            # Get metadata
            metadata = res.get('metadata', {})

            # Format date
            date_val = res.get("date", "-")
            if date_val != "-":
                try:
                    if isinstance(date_val, str):
                        dt = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                        date_val = dt.strftime("%b %d, %Y")
                except:
                    pass

            # Get icon based on type
            icon_map = {
                "transaction": "💸",
                "product": "🛒",
                "saved_payment": "💳",
                "service": "🛠️"
            }
            icon = icon_map.get(res.get("type", "service"), "🔍")
            result_type = res.get("type", "-").capitalize()
            category = html.escape(res.get("category", "-"))

            if res["type"] == "transaction":
                title = html.escape(metadata.get('description', 'No description'))
                amount = res.get('amount', 0)
                status = html.escape(metadata.get('status', '-'))
                service_name = html.escape(metadata.get('properties', {}).get('service_name', '-'))

                card_html = f"""
                <div class="result-card">
                    <div class="result-header">
                        <span class="result-icon">{icon}</span>
                        <span class="result-title">{title}</span>
                        <span class="result-type">{result_type}</span>
                    </div>
                    <div class="result-content">
                        <div class="result-column">
                            <p><strong>Amount:</strong> Rs. {amount:,.2f}</p>
                            <p><strong>Date:</strong> {date_val}</p>
                            <p><strong>Status:</strong> {status}</p>
                        </div>
                        <div class="result-column">
                            <p><strong>Service:</strong> {service_name}</p>
                            <p><strong>Category:</strong> {category}</p>
                        </div>
                    </div>
                </div>
                """

            elif res["type"] == "saved_payment":
                title = html.escape(metadata.get('description', 'No description'))
                amount = res.get('amount', 0)
                payee_name = html.escape(metadata.get('payee_name', '-'))

                card_html = f"""
                <div class="result-card">
                    <div class="result-header">
                        <span class="result-icon">{icon}</span>
                        <span class="result-title">{title}</span>
                        <span class="result-type">{result_type}</span>
                    </div>
                    <div class="result-content">
                        <div class="result-column">
                            <p><strong>Amount:</strong> Rs. {amount:,.2f}</p>
                            <p><strong>Date:</strong> {date_val}</p>
                        </div>
                        <div class="result-column">
                            <p><strong>Category:</strong> {category}</p>
                            <p><strong>Payee:</strong> {payee_name}</p>
                        </div>
                    </div>
                </div>
                """

            elif res["type"] == "service":
                title = html.escape(metadata.get('title', 'No title'))
                content = metadata.get('content', '-')
                # Clean content from HTML tags
                content = re.sub(r'</div>|</section>|</article>', '', content)

                card_html = f"""
                <div class="result-card">
                    <div class="result-header">
                        <span class="result-icon">{icon}</span>
                        <span class="result-title">{title}</span>
                        <span class="result-type">{result_type}</span>
                    </div>
                    <div class="result-content">
                        <div class="service-content">
                            <p>{content}</p>
                        </div>
                    </div>
                </div>
                """

            elif res["type"] == "product":
                title = html.escape(metadata.get('product_name', 'No product name'))
                amount = res.get('amount', 0)
                vendor = html.escape(metadata.get('vendor', '-'))

                card_html = f"""
                <div class="result-card">
                    <div class="result-header">
                        <span class="result-icon">{icon}</span>
                        <span class="result-title">{title}</span>
                        <span class="result-type">{result_type}</span>
                    </div>
                    <div class="result-content">
                        <div class="result-column">
                            <p><strong>Amount:</strong> Rs. {amount:,.2f}</p>
                            <p><strong>Date:</strong> {date_val}</p>
                        </div>
                        <div class="result-column">
                            <p><strong>Vendor:</strong> {vendor}</p>
                            <p><strong>Category:</strong> {category}</p>
                        </div>
                    </div>
                </div>
                """

            else:
                # Default case for unknown types
                title = html.escape(res.get('title', metadata.get('title', 'Unknown')))

                card_html = f"""
                <div class="result-card">
                    <div class="result-header">
                        <span class="result-icon">{icon}</span>
                        <span class="result-title">{title}</span>
                        <span class="result-type">{result_type}</span>
                    </div>
                    <div class="result-content">
                        <div class="result-column">
                            <p><strong>Date:</strong> {date_val}</p>
                            <p><strong>Category:</strong> {category}</p>
                        </div>
                    </div>
                </div>
                """

            # Render the complete card
            st.markdown(card_html, unsafe_allow_html=True)
            st.write("")

    elif search_performed:
        # Only show "no results" if a search was actually performed
        st.markdown(
            '<div class="empty-state">'
            '<h3>🔍 No results found</h3>'
            '<p>Try a different search query or adjust your filters</p>'
            '</div>',
            unsafe_allow_html=True
        )