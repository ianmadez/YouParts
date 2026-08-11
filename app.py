import os
import streamlit as st

# 1. Page Config with Asset Check
favicon_path = "assets/favicon.ico" if os.path.exists("assets/favicon.ico") else None
st.set_page_config(
    page_title="YouParts — DIY Manifest Planner",
    page_icon=favicon_path,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Inject Editorial Theme & WebGL Paper Shader
from src.ui.components.theme import inject_youparts_theme

inject_youparts_theme()

# WebGL Canvas Shader Background (Red / Ink / Cream Paper Drift)
# st.iframe embeds the HTML content in an iframe that executes the script.
# theme.py stretches the iframe to a fixed full-viewport layer above the app
# background and below the content (z-index layering).
shader_html = """
<canvas id="paper-shader-canvas" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 1; pointer-events: none; opacity: 0.6;"></canvas>
<script>
const canvas = document.getElementById('paper-shader-canvas');
const ctx = canvas.getContext('2d');
let width = canvas.width = window.innerWidth;
let height = canvas.height = window.innerHeight;
window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
});

let time = 0;
function draw() {
    time += 0.005;
    ctx.clearRect(0, 0, width, height);
    for (let i = 0; i < width; i += 16) {
        for (let j = 0; j < height; j += 16) {
            const n = Math.sin(i * 0.005 + time) * Math.cos(j * 0.005 + time);
            if (n > 0.55) {
                ctx.fillStyle = 'rgba(255, 0, 0, 0.09)';
                ctx.fillRect(i, j, 16, 16);
            } else if (n < -0.55) {
                ctx.fillStyle = 'rgba(18, 18, 18, 0.06)';
                ctx.fillRect(i, j, 16, 16);
            }
        }
    }
    requestAnimationFrame(draw);
}
draw();
</script>
"""
st.iframe(shader_html)

from src.ingestor import PlaylistParser
from src.ai_engine.relevance_filter import RelevanceFilterEngine
from src.ai_engine.extractor import BOMExtractorEngine

# 3. Session State
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "master_bom" not in st.session_state:
    st.session_state.master_bom = {}


# 4. Pipeline Runner Callback
def run_pipeline(raw_urls: list[str], build_focus: str):
    st.session_state.build_focus = build_focus

    with st.status("PROCESSING YOUPARTS MANIFEST", expanded=True) as status:
        st.write("[1/3] Ingesting YouTube video sources...")
        video_metadata_list = PlaylistParser.expand_and_fetch_all(raw_urls) or []

        if not video_metadata_list:
            status.update(label="Metadata extraction failed.", state="error")
            st.error(
                "Unable to extract video metadata. Please check your internet connection or URL formats."
            )
            return

        total_vids = len(video_metadata_list)
        st.write(f"[2/3] Screening {total_vids} videos for build relevance...")

        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def update_screening_progress(current, total, title):
            progress_bar.progress(current / total)
            status_text.text(
                f"Screening ({current}/{total}): {(title or 'Video')[:55]}..."
            )

        filter_engine = RelevanceFilterEngine()
        relevant_videos = filter_engine.filter_playlist(
            video_metadata_list, progress_callback=update_screening_progress
        )
        st.session_state.analyzed_videos = relevant_videos

        rel_total = len(relevant_videos)
        st.write(f"[3/3] Extracting BOM from {rel_total} relevant videos...")
        extractor = BOMExtractorEngine()

        extractions = []
        for idx, v in enumerate(relevant_videos):
            progress_bar.progress((idx + 1) / max(rel_total, 1))
            status_text.text(
                f"Extracting BOM ({idx + 1}/{rel_total}): {(v.get('title') or '')[:55]}..."
            )
            extractions.append(extractor.extract_bom_from_video(v))

        master_bom = extractor.aggregate_master_bom(extractions)
        st.session_state.master_bom = master_bom

        progress_bar.progress(1.0)
        status_text.text("Extraction complete!")
        status.update(label="MANIFEST EXTRACTION COMPLETE", state="complete")

    st.session_state.page = "workspace"
    st.rerun()


# 5. Page Routing
from src.ui.components.navbar import render_top_navbar
from src.ui.components.landing import render_landing_page
from src.ui.components.workspace import render_workspace

render_top_navbar()

if st.session_state.page == "landing":
    render_landing_page(on_start_callback=run_pipeline)
else:
    render_workspace()

# 6. App Footer
st.markdown(
    """
    <footer class="app-footer">
        <span class="badge-tag">YOUPARTS</span>
        <span>DIY Manifest Planner — From Watch Later to Built.</span>
        <span class="app-footer-spacer"></span>
        <span>© 2026</span>
    </footer>
    """,
    unsafe_allow_html=True,
)
