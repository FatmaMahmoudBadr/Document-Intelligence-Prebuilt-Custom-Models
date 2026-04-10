import streamlit as st
from utils.pdf_utils import field_color


TYPE_OPTIONS = [
    "string", "number", "date", "integer", "selectionMark",
    "countryRegion", "signature", "array", "object",
    "currency", "address", "phoneNumber", "time",
]
FORMAT_OPTIONS = [
    "not-specified", "currency", "decimal", "mdy", "dmy", "ymd", "percentage",
]


def render_step2():
    st.markdown('<p class="step-header">Step 2 — Define Fields to Extract</p>', unsafe_allow_html=True)
    st.info("Enter the field names your model should learn, then configure their type and format.")

    # ── Preset quick-add buttons ──────────────────────────
    presets = ["invoice_number", "total_amount", "vendor_name", "date",
               "ship_to", "bill_to", "quantity", "unit_price"]
    preset_cols = st.columns(4)
    clicked = []
    for i, p in enumerate(presets):
        with preset_cols[i % 4]:
            if st.button(f"+ {p}", key=f"preset_{p}"):
                clicked.append(p)

    current = list(st.session_state.fields)
    for p in clicked:
        if p not in current:
            current.append(p)
    if clicked:
        st.session_state.fields = current

    raw = st.text_area(
        "Field names (one per line)",
        value="\n".join(st.session_state.fields),
        height=160,
        placeholder="invoice_number\ntotal_amount\nvendor_name\ndate",
    )

    # ── Per-field type / format table ────────────────────
    parsed_fields = [f.strip() for f in raw.strip().splitlines() if f.strip()]

    if parsed_fields:
        st.markdown("**Field types & formats** *(used to generate fields.json)*:")

        for f in parsed_fields:
            st.session_state.field_types.setdefault(f, "string")
            st.session_state.field_formats.setdefault(f, "not-specified")

        header = st.columns([3, 2, 2])
        header[0].markdown("**Field**")
        header[1].markdown("**Type**")
        header[2].markdown("**Format**")

        for f in parsed_fields:
            row = st.columns([3, 2, 2])
            color = field_color(parsed_fields, f)
            row[0].markdown(
                f'<span class="annotation-pill" style="background:{color}">{f}</span>',
                unsafe_allow_html=True,
            )
            chosen_type = row[1].selectbox(
                f"type_{f}", TYPE_OPTIONS,
                index=TYPE_OPTIONS.index(st.session_state.field_types.get(f, "string")),
                key=f"type_{f}", label_visibility="collapsed",
            )
            chosen_fmt = row[2].selectbox(
                f"fmt_{f}", FORMAT_OPTIONS,
                index=FORMAT_OPTIONS.index(st.session_state.field_formats.get(f, "not-specified")),
                key=f"fmt_{f}", label_visibility="collapsed",
            )
            st.session_state.field_types[f]   = chosen_type
            st.session_state.field_formats[f] = chosen_fmt

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Save & Continue ➡️", type="primary"):
            if not parsed_fields:
                st.error("Add at least 1 field.")
            else:
                st.session_state.fields = parsed_fields
                for fname in st.session_state.uploaded_files:
                    st.session_state.annotations.setdefault(fname, [])
                st.session_state.anno_pdf = list(st.session_state.uploaded_files.keys())[0]
                st.session_state.step = 3
                st.rerun()