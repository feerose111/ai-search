import streamlit as st
from datetime import datetime
import html
import re


def render_search_results(results, search_performed=False):
    if results:
        st.success(f"🔎 Found {len(results)} result(s):")
        for i, res in enumerate(results, 1):
            # Escape HTML special characters to prevent rendering issues
            title = html.escape(res.get('title', 'No title'))
            category = html.escape(res.get("category", "-"))

            # Format date
            date_val = res.get("date", "-")
            if date_val != "-":
                try:
                    if isinstance(date_val, str):
                        dt = datetime.fromisoformat(date_val)
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

            # Handle service type differently to avoid HTML structure breaking
            if res["type"] == "service":
                # Create a simpler card structure for service type with only relevant fields
                content = res.get("content", "-")
                # Clean the content - remove problematic HTML tags that could break structure
                content = re.sub(r'</div>|</section>|</article>', '', content)

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
                        <div class="result-column">
                            <div class="service-content">
                                {content}
                            </div>
                        </div>
                    </div>
                </div>
                """
            else:
                # Build the standard card HTML for other types
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
                """

                # Add amount/price information
                if res["type"] == "transaction":
                    amount = res.get('amount', 0)
                    card_html += f'<p><strong>Amount:</strong> Rs. {amount:,.2f}</p>'
                elif res["type"] == "product":
                    price = res.get('price', 0)
                    card_html += f'<p><strong>Price:</strong> Rs. {price:,.2f}</p>'
                elif res["type"] == "saved_payment":
                    amount = res.get('amount', 0)
                    card_html += f'<p><strong>Amount:</strong> Rs. {amount:,.2f}</p>'

                # Close first column and open second column
                card_html += f"""
                        </div>
                        <div class="result-column">
                            <p><strong>Category:</strong> {category}</p>
                """

                # Add type-specific details
                if res["type"] == "transaction":
                    merchant = html.escape(res.get("merchant", "-"))
                    card_html += f'<p><strong>Merchant:</strong> {merchant}</p>'
                elif res["type"] == "product":
                    vendor = html.escape(res.get("vendor", "-"))
                    card_html += f'<p><strong>Vendor:</strong> {vendor}</p>'
                elif res["type"] == "saved_payment":
                    payee = html.escape(res.get("payee", "-"))
                    card_html += f'<p><strong>Payee:</strong> {payee}</p>'

                # Close all divs for non-service types
                card_html += """
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