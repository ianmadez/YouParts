import streamlit as st
from config.settings import settings
from src.ui.components.settings_drawer import render_settings_drawer
from src.utils.storage import list_saved_manifests, load_manifest


def render_landing_page(on_start_callback):
    """Renders the YouParts landing page with local branding assets."""

    st.markdown(
        """
        <div class="hero-container">
            <span class="badge-tag hero-eyebrow">DIY PARTS PLANNER</span>
            <p class="hero-tagline">
                From Watch Later to Built. Extract comprehensive component manifests directly from YouTube build series.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_settings_drawer()

    # Saved Manifest Quick Loader
    saved_files = list_saved_manifests()
    if saved_files:
        st.markdown("#### LOAD RECENT SAVED BUILD")
        selected_file = st.selectbox(
            "Select saved build project:",
            ["-- Choose a saved manifest --"] + saved_files,
        )

        if selected_file != "-- Choose a saved manifest --":
            if st.button("OPEN SAVED MANIFEST", type="primary"):
                saved_data = load_manifest(selected_file)
                st.session_state.build_focus = saved_data.get(
                    "build_focus", "Loaded Build"
                )
                st.session_state.master_bom = saved_data.get("master_bom", {})
                st.session_state.analyzed_videos = saved_data.get("analyzed_videos", [])
                st.session_state.page = "workspace"
                st.rerun()
        st.divider()

    st.markdown("#### 1. YOUTUBE SOURCES")
    urls_input = st.text_area(
        "Paste Playlist or Video URLs (one link per line):",
        placeholder="https://www.youtube.com/watch?v=gSKSSxwpuKU\nhttps://www.youtube.com/playlist?list=...",
        height=110,
    )

    st.markdown("#### 2. TARGET BUILD SPECIFICATION")
    build_focus = st.text_area(
        "Specify what you are building:",
        value="DIY Force Feedback (FFB) Steering Wheel with Clutch Pedal for BeamNG.drive",
        height=70,
        help="Context used by the AI to filter out non-relevant build videos.",
    )

    st.write("")
    if st.button("EXTRACT PARTS MANIFEST", type="primary", use_container_width=True):
        if not settings.GROQ_API_KEY:
            st.error(
                "API key missing. Enter your Groq API key in the configuration drawer above."
            )
            return

        raw_urls = [u.strip() for u in urls_input.strip().split("\n") if u.strip()]
        if not raw_urls:
            st.warning("Provide at least one valid YouTube URL.")
            return

        on_start_callback(raw_urls, build_focus)
