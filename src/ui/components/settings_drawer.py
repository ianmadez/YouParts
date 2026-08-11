import streamlit as st
from config.settings import settings


def render_settings_drawer():
    """Renders configuration drawer for local API keys and scraper parameters."""
    with st.expander(
        "CONFIGURATION & API KEYS", expanded=not bool(settings.GROQ_API_KEY)
    ):
        st.caption("Settings persist locally to `config/youparts_config.json`.")

        col1, col2 = st.columns(2)
        with col1:
            groq_key = st.text_input(
                "Groq API Key",
                value=settings.GROQ_API_KEY,
                type="password",
                help="Obtain key from console.groq.com",
            )
            request_delay = st.number_input(
                "API Request Cooldown (Seconds)",
                value=float(settings.REQUEST_DELAY_SECONDS),
                min_value=0.5,
                max_value=10.0,
                step=0.5,
            )

            with col2:
                st.markdown("**Regional Search Scrapers:**")
                enable_ae = st.checkbox("AliExpress", value=settings.ENABLE_ALIEXPRESS)
                enable_shopee = st.checkbox("Shopee", value=settings.ENABLE_SHOPEE)
                enable_lazada = st.checkbox("Lazada", value=settings.ENABLE_LAZADA)

                st.write("")
                if st.button("SAVE CONFIGURATION"):
                    updates = {
                        "GROQ_API_KEY": groq_key,
                        "REQUEST_DELAY_SECONDS": request_delay,
                        "ENABLE_ALIEXPRESS": enable_ae,
                        "ENABLE_SHOPEE": enable_shopee,
                        "ENABLE_LAZADA": enable_lazada,
                    }
                    settings.save_user_config(updates)
                    st.success("Configuration updated successfully.")
                    st.rerun()
