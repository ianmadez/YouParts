import json
from typing import Optional

import pandas as pd
import streamlit as st
from src.scrapers import MasterPriceAggregator
from src.utils.storage import save_manifest

WORKSPACE_SECTIONS = [
    {"key": "bom", "title": "Bill of Materials", "noun": "components"},
    {"key": "logic_gaps", "title": "Logic Gaps & Warnings", "noun": "warnings"},
    {"key": "resources", "title": "CAD & Resource Links", "noun": "links"},
    {"key": "pricing", "title": "Regional Price Search", "noun": "parts"},
]


def _set_workspace_tab(tab_key: str) -> None:
    """Callback: switch the active bento-card workspace section."""
    st.session_state.workspace_tab = tab_key


def _set_price_part(part_name: str) -> None:
    """Callback: select a part for the regional price search."""
    st.session_state.price_part = part_name
    st.session_state.price_results = []


def _set_bulk_query(query: str) -> None:
    """Callback: store a compiled bulk buy search query for copy-out."""
    st.session_state.bulk_query = query


def _fmt_timestamp(seconds) -> str:
    """Formats seconds as MM:SS for deep-link labels."""
    try:
        total = max(0, int(seconds))
    except (TypeError, ValueError):
        return "00:00"
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


def _try_numeric(qty) -> Optional[float]:
    """Returns a float if the quantity string is a plain number, else None."""
    if qty is None:
        return None
    try:
        return float(str(qty).strip())
    except (TypeError, ValueError):
        return None


def _merge_components(parts, keep_name: str, from_name: str) -> None:
    """Merges Item B into Item A: audit trail, bought preservation, quantity
    handling, then removes Item B from the active manifest."""
    master_data = st.session_state.get("master_bom", {})
    manifest = master_data.get("parts_manifest", [])
    keep_item = next((p for p in manifest if p["part_name"] == keep_name), None)
    from_item = next((p for p in manifest if p["part_name"] == from_name), None)
    if not keep_item or not from_item:
        st.session_state.merge_feedback = "Could not locate the components to merge."
        st.rerun()
        return

    # Audit trail: record the merged-from name(s)
    keep_item.setdefault("merged_from", [])
    if from_name not in keep_item["merged_from"]:
        keep_item["merged_from"].append(from_name)
    for src_name in from_item.get("merged_from") or []:
        if src_name not in keep_item["merged_from"]:
            keep_item["merged_from"].append(src_name)

    # Preserve purchase state
    keep_item["bought"] = bool(keep_item.get("bought", False)) or bool(
        from_item.get("bought", False)
    )

    # Quantity: sum when both are plain numbers, otherwise keep primary and
    # surface what happened (never silently drop a quantity).
    keep_qty = keep_item.get("quantity", "1")
    from_qty = from_item.get("quantity", "1")
    keep_num = _try_numeric(keep_qty)
    from_num = _try_numeric(from_qty)
    if keep_num is not None and from_num is not None:
        new_qty = keep_num + from_num
        keep_item["quantity"] = (
            str(int(new_qty)) if float(new_qty).is_integer() else str(new_qty)
        )
        st.session_state.merge_feedback = (
            f"Quantity updated: {keep_item['quantity']} ({keep_qty} + {from_qty})."
        )
    else:
        st.session_state.merge_feedback = (
            f"Kept quantity '{keep_qty}' — '{from_qty}' from '{from_name}' "
            f"recorded in merged_from."
        )

    # Remove the merged-from component from the active manifest
    manifest[:] = [p for p in manifest if p["part_name"] != from_name]
    master_data["parts_manifest"] = manifest
    st.session_state.master_bom = master_data
    st.rerun()


def _render_merge_tool(parts) -> None:
    """Post-hoc component merging form (manual dedupe of near-identical names)."""
    st.divider()
    st.markdown("#### Merge Components")
    if len(parts) < 2:
        st.caption("Add at least two components to merge.")
        return

    if st.session_state.get("merge_feedback"):
        st.info(st.session_state.pop("merge_feedback"))

    part_names = [p["part_name"] for p in parts]
    keep_default = part_names[0]
    from_default = part_names[1] if len(part_names) > 1 else part_names[0]

    col_keep, col_from, col_btn = st.columns([1, 1, 1])
    with col_keep:
        keep_name = st.selectbox(
            "Merge INTO (keep)", part_names, index=part_names.index(keep_default)
        )
    with col_from:
        from_name = st.selectbox(
            "Merge FROM (remove)",
            part_names,
            index=part_names.index(from_default),
        )
    with col_btn:
        st.write("")
        if st.button("MERGE COMPONENTS", use_container_width=True):
            if keep_name == from_name:
                st.warning("Choose two different components to merge.")
            else:
                _merge_components(parts, keep_name, from_name)


def _render_bom(parts):
    st.markdown("#### Component Manifest")

    # Purchase progress bar, bound to each item's "bought" state
    if not parts:
        st.info("No parts extracted.")
        return

    total = len(parts)
    bought = sum(1 for p in parts if p.get("bought", False))
    ratio = bought / total
    st.progress(ratio)
    st.caption(f"{bought} / {total} Components Acquired ({int(ratio * 100)}%)")

    # Copyable bulk buy query from the last category button click
    if st.session_state.get("bulk_query"):
        st.code(st.session_state["bulk_query"], language="text")

    categories = []
    for p in parts:
        cat = p.get("category") or "General"
        if cat not in categories:
            categories.append(cat)

    for cat in categories:
        cat_parts = [p for p in parts if (p.get("category") or "General") == cat]

        cat_col, bulk_col = st.columns([3, 1], vertical_alignment="center")
        with cat_col:
            st.markdown(f"**Category: {cat}**")
        with bulk_col:
            st.button(
                "COPY BULK BUY QUERY",
                key=f"bulk_{cat}",
                use_container_width=True,
                on_click=_set_bulk_query,
                args=(", ".join(p["part_name"] for p in cat_parts),),
            )

        for idx, item in enumerate(cat_parts):
            item_key = f"bought_{cat}_{item['part_name']}"
            checked = st.checkbox(
                f"**{item['part_name']}** | Qty: {item.get('quantity', '1')} | Specs: {item.get('specs_and_dimensions') or 'N/A'}",
                value=bool(item.get("bought", False)),
                key=item_key,
            )
            # Sync the widget state back into the manifest dict so "SAVE
            # MANIFEST TO DISK" persists purchase state. Mutating the item dict
            # (a live reference into session_state.master_bom) is safe here —
            # callback args would be copies and are never mutated.
            item["bought"] = bool(checked)
            if item.get("logic_gap_warning"):
                st.markdown(
                    f"""
                    <div class="logic-gap-card">
                        <b>LOGIC GAP NOTICE:</b> {item['logic_gap_warning']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.divider()

    _render_merge_tool(parts)


def _render_logic_gaps(logic_gaps):
    st.markdown("#### Hallucination-Guard Directives")
    st.caption(
        "Specifications requiring manual verification in video descriptions or timestamps."
    )
    if not logic_gaps:
        st.success("No critical logic gaps detected.")
        return

    for gap in logic_gaps:
        # Normalize: structured dict / LogicGap (new) vs legacy plain string
        if isinstance(gap, dict):
            description = str(gap.get("description") or "Unspecified logic gap")
            timestamp = gap.get("approx_timestamp_seconds")
            source_title = gap.get("source_video_title")
            source_url = gap.get("source_video_url")
        elif hasattr(gap, "model_dump"):
            gap = gap.model_dump()
            description = str(gap.get("description") or "Unspecified logic gap")
            timestamp = gap.get("approx_timestamp_seconds")
            source_title = gap.get("source_video_title")
            source_url = gap.get("source_video_url")
        else:
            description = str(gap)
            timestamp = source_title = source_url = None

        # Deep-link only when we have BOTH a timestamp AND a source URL;
        # otherwise render plain text (graceful no-link fallback for legacy data).
        ts_link = ""
        if timestamp is not None and source_url:
            ts_link = (
                f'<a class="logic-gap-link" href="{source_url}?t={int(timestamp)}" '
                f'target="_blank" rel="noopener">View Video at '
                f"{_fmt_timestamp(timestamp)}</a>"
            )

        source_tag = ""
        if source_title:
            source_tag = f'<span class="logic-gap-source">Source: {source_title}</span>'

        st.markdown(
            f"""
            <div class="logic-gap-card">
                <b>FLAG:</b> {description}
                {source_tag}
                {ts_link}
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_resources(resources):
    st.markdown("#### Resource & Design Files")
    if not resources:
        st.info("No external links found in description text.")
        return

    drive_links = []
    cad_links = []
    youtube_links = []
    other_links = []

    for res in resources:
        url_lower = res.get("url", "").lower()
        res_type = res.get("resource_type", "").lower()

        if "drive.google.com" in url_lower or "mega.nz" in url_lower:
            drive_links.append(res)
        elif (
            "github.com" in url_lower
            or "thingiverse" in url_lower
            or "printables" in url_lower
            or "cad" in res_type
            or "stl" in res_type
        ):
            cad_links.append(res)
        elif "youtube.com" in url_lower or "youtu.be" in url_lower:
            youtube_links.append(res)
        else:
            other_links.append(res)

    if drive_links:
        st.markdown("##### CAD Models, Diagrams & Cloud Drives")
        for res in drive_links:
            st.markdown(
                f"- **[{res['resource_type']}]** [{res['title']}]({res['url']}) *(Source: {res.get('source_video_title', 'Video')})*"
            )
        st.divider()

    if cad_links:
        st.markdown("##### 3D Models & Repositories")
        for res in cad_links:
            st.markdown(
                f"- **[{res['resource_type']}]** [{res['title']}]({res['url']}) *(Source: {res.get('source_video_title', 'Video')})*"
            )
        st.divider()

    if youtube_links:
        st.markdown("##### Video Tutorials & References")
        for res in youtube_links:
            st.markdown(
                f"- **[{res['resource_type']}]** [{res['title']}]({res['url']}) *(Source: {res.get('source_video_title', 'Video')})*"
            )
        st.divider()

    if other_links:
        st.markdown("##### External Web & Purchase Links")
        for res in other_links:
            st.markdown(
                f"- **[{res['resource_type']}]** [{res['title']}]({res['url']}) *(Source: {res.get('source_video_title', 'Video')})*"
            )


def _render_pricing(parts):
    st.markdown("#### Regional E-Commerce Price Search")
    if not parts:
        st.info("No parts to price check. Run a manifest extraction first.")
        return

    part_names = [p["part_name"] for p in parts]
    if (
        "price_part" not in st.session_state
        or st.session_state.get("price_part") not in part_names
    ):
        st.session_state.price_part = part_names[0]
    if "price_results" not in st.session_state:
        st.session_state.price_results = []

    selected = st.session_state.price_part
    st.markdown("Select a component card to price check:")

    cols = st.columns(3)
    for idx, item in enumerate(parts):
        with cols[idx % 3]:
            active = item["part_name"] == selected
            st.button(
                f"**{item['part_name']}**\n\nQty {item.get('quantity', '1')} · {item.get('specs_and_dimensions') or 'N/A'}",
                key=f"part_{idx}_{item['part_name']}",
                type="primary" if active else "secondary",
                use_container_width=True,
                on_click=_set_price_part,
                args=(item["part_name"],),
            )

    if st.button("SEARCH REGIONAL STORES", type="primary", use_container_width=True):
        part_obj = next((p for p in parts if p["part_name"] == selected), None)
        with st.spinner(f"Querying stores for '{selected}'..."):
            if part_obj:
                specs = part_obj.get("specs_and_dimensions") or ""
                st.session_state.price_results = (
                    MasterPriceAggregator.fetch_all_matches(selected, specs)
                )
        st.rerun()

    if st.session_state.price_results:
        st.markdown(
            f'<div class="selection-banner">SELECTED: {selected}</div>',
            unsafe_allow_html=True,
        )
        for match in st.session_state.price_results:
            st.markdown(
                f"**[{match['platform']}]** [{match['title']}]({match['product_url']}) — *{match['price']} {match['currency']}*"
            )


def render_workspace():
    """Renders the BOM itinerary workspace with bento-card navigation, CAD resources, logic gaps, and price lookups."""
    master_data = st.session_state.get("master_bom", {})
    parts = master_data.get("parts_manifest", [])
    resources = master_data.get("external_resources", [])
    logic_gaps = master_data.get("logic_gaps", [])

    if "workspace_tab" not in st.session_state:
        st.session_state.workspace_tab = "bom"

    st.markdown(
        f"""
        <div class="workspace-subtitle">
            <span class="badge-tag-red">ACTIVE MANIFEST WORKSPACE</span>
            <h3 class="workspace-focus">{st.session_state.get('build_focus', 'DIY Build')}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Save & Export Toolbar
    col_save, col_csv, col_json = st.columns([2, 1, 1])

    with col_save:
        if st.button("SAVE MANIFEST TO DISK", use_container_width=True):
            build_focus = st.session_state.get("build_focus", "build")
            saved_path = save_manifest(
                build_focus=build_focus,
                master_data=master_data,
                analyzed_videos=st.session_state.get("analyzed_videos", []),
            )
            st.success(f"Manifest saved to `{saved_path}`!")

    with col_csv:
        if parts:
            df_export = pd.DataFrame(parts)
            csv_data = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "EXPORT CSV",
                data=csv_data,
                file_name="youparts_manifest.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with col_json:
        if master_data:
            json_str = json.dumps(master_data, indent=2).encode("utf-8")
            st.download_button(
                "EXPORT JSON",
                data=json_str,
                file_name="youparts_manifest.json",
                mime="application/json",
                use_container_width=True,
            )

    st.write("")

    # Metric Counters
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TOTAL COMPONENTS", len(parts))
    m2.metric("EXTERNAL RESOURCES", len(resources))
    m3.metric("LOGIC GAP WARNINGS", len(logic_gaps))
    m4.metric("ANALYZED VIDEOS", len(st.session_state.get("analyzed_videos", [])))

    st.write("")

    # Bento Card Navigation (replaces tabs)
    counts = {
        "bom": len(parts),
        "logic_gaps": len(logic_gaps),
        "resources": len(resources),
        "pricing": len(parts),
    }
    nav_cols = st.columns(4)
    for col, section in zip(nav_cols, WORKSPACE_SECTIONS):
        key = section["key"]
        active = st.session_state.workspace_tab == key
        with col:
            st.button(
                f"**{section['title']}**\n\n`{counts[key]}` {section['noun']}",
                key=f"nav_{key}",
                type="primary" if active else "secondary",
                use_container_width=True,
                on_click=_set_workspace_tab,
                args=(key,),
            )

    st.write("")

    active_tab = st.session_state.workspace_tab
    if active_tab == "bom":
        _render_bom(parts)
    elif active_tab == "logic_gaps":
        _render_logic_gaps(logic_gaps)
    elif active_tab == "resources":
        _render_resources(resources)
    elif active_tab == "pricing":
        _render_pricing(parts)
