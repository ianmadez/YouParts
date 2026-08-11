import streamlit as st
from src.ui.components.theme import resolve_logo_path


def render_top_navbar():
    """Renders the app-wide top navigation bar: logo + wordmark + view status."""
    logo_path = resolve_logo_path()
    in_workspace = st.session_state.get("page") == "workspace"
    step_num, step_label = ("02", "WORKSPACE") if in_workspace else ("01", "INPUTS")

    col_brand, col_step = st.columns([3, 7], vertical_alignment="center")

    # Brand: logo + aligned wordmark (tightened spacing)
    with col_brand:
        brand_logo, brand_word = st.columns([0.22, 0.78], vertical_alignment="center")
        with brand_logo:
            if logo_path:
                st.image(logo_path, width=54)
            else:
                st.markdown(
                    '<span class="navbar-wordmark">YouParts</span>',
                    unsafe_allow_html=True,
                )
        with brand_word:
            st.markdown(
                '<span class="navbar-wordmark" style="margin-left: -8px;">YouParts</span>',
                unsafe_allow_html=True,
            )

    # Numbered editorial step marker (+ context action in workspace)
    with col_step:
        if in_workspace:
            step_col, back_col = st.columns([2, 1], vertical_alignment="center")
            with step_col:
                st.markdown(
                    f'<div class="navbar-step"><span class="navbar-step-num">{step_num}</span> — {step_label}</div>',
                    unsafe_allow_html=True,
                )
            with back_col:
                if st.button(
                    "← BACK TO INPUTS",
                    key="back_to_inputs",
                    type="tertiary",
                ):
                    st.session_state.page = "landing"
                    st.rerun()
        else:
            st.markdown(
                f'<div class="navbar-step"><span class="navbar-step-num">{step_num}</span> — {step_label}</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="navbar-divider"></div>', unsafe_allow_html=True)
