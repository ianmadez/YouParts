import os
import streamlit as st


def resolve_logo_path() -> str | None:
    """Resolves the YouParts logo asset path, or None if no logo asset exists."""
    for path in ["yp-nobg.png", "assets/yp-nobg.png", "yp.png", "assets/yp.png"]:
        if os.path.exists(path):
            return path
    return None


def inject_youparts_theme():
    """Injects editorial red/black/paper CSS with paper grain texture and a bento-card button system."""
    theme_css = """
    <style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;0,6..72,700;1,6..72,400&family=Inter:wght@400;500;600;700&display=swap');

/* Tactile Paper Grain Background */
.stApp {
    background-color: #FAF8F5 !important;
    background-image:
        url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.04'/%3E%3C/svg%3E"),
        radial-gradient(circle at 10% 10%, rgba(255, 0, 0, 0.025) 0%, transparent 40%),
        radial-gradient(circle at 90% 90%, rgba(18, 18, 18, 0.02) 0%, transparent 40%) !important;
    background-attachment: fixed !important;
    color: #121212 !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}

/* WebGL paper-shader: the component iframe is stretched to a fixed full-viewport
   layer above the app background and below the content. Its wrapper is pulled
   out of flow (height 0) so it does not reserve a big empty gap at page top. */
div[data-testid="stElementContainer"]:has(> iframe[data-testid="stIFrame"]) {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
    z-index: 1 !important;
    pointer-events: none !important;
}
iframe[data-testid="stIFrame"] {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 1 !important;
    border: 0 !important;
    pointer-events: none !important;
    background: transparent !important;
}
#paper-shader-canvas {
    z-index: 1 !important;
}
.block-container {
    position: relative;
    z-index: 2;
    padding-top: 1.5rem !important;
}
[data-testid="stSidebar"] {
    z-index: 2;
}
/* Streamlit default top bar is hidden for a clean editorial header */
[data-testid="stHeader"] {
    display: none !important;
}

/* Headings */
h1, h2, h3, h4 {
    font-family: 'Newsreader', Georgia, serif !important;
    color: #121212 !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

.mono-text, .stCaption, label, .stMetric, div[data-testid="stMetricLabel"] {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Zero Radius & Sharp Ink Borders */
div[data-testid="stForm"],
div[data-testid="stExpander"],
div[data-testid="stMetric"] {
    border-radius: 0px !important;
    border: 1px solid #121212 !important;
    background-color: #FFFFFF !important;
    box-shadow: none !important;
}

/* Opaque form surfaces: the paper shader must never show through controls.
   Covers the field container, the baseweb wrapper, and the input/textarea
   element so it holds regardless of Streamlit's DOM nesting. */
div[data-testid="stTextInput"] > div:last-child,
div[data-testid="stTextArea"] > div:last-child,
div[data-testid="stNumberInput"] > div:last-child,
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextArea"] div[data-baseweb="textarea"],
div[data-testid="stNumberInput"] div[data-baseweb="input"],
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input {
    border-radius: 0px !important;
    border: 1px solid #121212 !important;
    background-color: #FFFFFF !important;
    box-shadow: none !important;
}

/* Bento Card Button System */
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stButton"] button[kind="secondary"] {
    border-radius: 0px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 0.85rem 1.25rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
    line-height: 1.35 !important;
    transition-property: background-color, color, border-color, transform !important;
    transition-duration: 0.12s !important;
    transition-timing-function: ease-in-out !important;
}
div[data-testid="stButton"] button[kind="primary"] > div,
div[data-testid="stButton"] button[kind="secondary"] > div {
    flex: 1 !important;
}
div[data-testid="stButton"] button[kind="primary"]:active,
div[data-testid="stButton"] button[kind="secondary"]:active {
    transform: scale(0.96) !important;
}

/* Primary: filled ink card (primary actions) */
div[data-testid="stButton"] button[kind="primary"] {
    background-color: #121212 !important;
    color: #FAF8F5 !important;
    border: 1.5px solid #121212 !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #FF0000 !important;
    color: #FFFFFF !important;
    border-color: #FF0000 !important;
}

/* Secondary: outlined white bento card (navigation / selection) */
div[data-testid="stButton"] button[kind="secondary"] {
    min-height: 6.5rem;
    background-color: #FFFFFF !important;
    color: #121212 !important;
    border: 1px solid #121212 !important;
    border-left: 4px solid #121212 !important;
    box-shadow: 3px 3px 0 rgba(18, 18, 18, 0.08) !important;
}
div[data-testid="stButton"] button[kind="secondary"]:hover {
    background-color: #FFF5F5 !important;
    color: #FF0000 !important;
    border-color: #FF0000 !important;
    border-left-color: #FF0000 !important;
}

/* Tertiary: compact outline button (nav back link) */
div[data-testid="stButton"] button[kind="tertiary"] {
    border-radius: 0px !important;
    border: 1px solid #121212 !important;
    background-color: #FFFFFF !important;
    color: #121212 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 0.4rem 0.85rem !important;
    transition-property: background-color, color, border-color, transform !important;
    transition-duration: 0.12s !important;
    transition-timing-function: ease-in-out !important;
}
div[data-testid="stButton"] button[kind="tertiary"]:hover {
    background-color: #FF0000 !important;
    color: #FFFFFF !important;
    border-color: #FF0000 !important;
}
div[data-testid="stButton"] button[kind="tertiary"]:active {
    transform: scale(0.96) !important;
}

/* Selection banner for the active price part */
.selection-banner {
    background-color: #121212;
    color: #FAF8F5;
    border-left: 4px solid #FF0000;
    padding: 0.6rem 1rem;
    margin: 0.5rem 0 1rem 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Logic Gap Alert Banner */
.logic-gap-card {
    background-color: #FFF5F5;
    border: 1px solid #FF0000;
    border-left: 4px solid #FF0000;
    padding: 0.85rem 1rem;
    margin-bottom: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: #121212;
}

/* Header & Badge Layout */
.hero-container {
    border-bottom: 2px solid #121212;
    padding-bottom: 1.25rem;
    margin-bottom: 1.75rem;
}

.badge-tag {
    background-color: #121212;
    color: #FAF8F5;
    padding: 3px 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.badge-tag-red {
    background-color: #FF0000;
    color: #FFFFFF;
    padding: 3px 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Top navigation bar */
.navbar-wordmark {
    font-family: 'Newsreader', Georgia, serif;
    font-weight: 700;
    font-size: 1.4rem;
    letter-spacing: -0.01em;
    color: #121212;
    white-space: nowrap;
}
.navbar-step {
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #555555;
    white-space: nowrap;
}
.navbar-step-num {
    color: #FF0000;
}
.navbar-divider {
    border-bottom: 2px solid #121212;
    margin: 0.75rem 0 1.5rem 0;
}

/* Landing hero */
.hero-eyebrow {
    display: inline-block;
    margin-bottom: 0.6rem;
}
.hero-tagline {
    font-family: 'Newsreader', Georgia, serif;
    font-size: 1.35rem;
    color: #222222;
    margin: 0.2rem 0 0 0;
}

/* Workspace subtitle (badge + build focus) */
.workspace-subtitle {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 1rem;
    border-bottom: 2px solid #121212;
    padding-bottom: 0.5rem;
    margin-bottom: 1.5rem;
}
.workspace-focus {
    margin: 0;
    font-family: 'Newsreader', Georgia, serif;
    font-weight: 700;
    letter-spacing: -0.02em;
}

/* App footer */
.app-footer {
    border-top: 2px solid #121212;
    margin-top: 3rem;
    padding-top: 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #555555;
}
.app-footer-spacer {
    flex: 1;
}
</style>
"""
    st.markdown(theme_css, unsafe_allow_html=True)
