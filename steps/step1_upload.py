import streamlit as st
from utils.pdf_utils import render_page_pil


def render_step1():
    st.markdown('<p class="step-header">Step 1 — Upload PDF Documents</p>', unsafe_allow_html=True)
    st.info("Upload **at least 5 PDFs** (invoices, forms, etc.) to train a robust custom model.")

    uploaded = st.file_uploader("Choose PDFs", type=["pdf"], accept_multiple_files=True)
    if uploaded:
        for f in uploaded:
            if f.name not in st.session_state.uploaded_files:
                st.session_state.uploaded_files[f.name] = f.read()

    count = len(st.session_state.uploaded_files)
    if count:
        st.success(f"✅ {count} document(s) ready")
        cols = st.columns(min(count, 4))
        for i, fname in enumerate(st.session_state.uploaded_files):
            with cols[i % 4]:
                try:
                    thumb, _, _ = render_page_pil(st.session_state.uploaded_files[fname], 0, dpi=72)
                    st.image(thumb, caption=fname[:25], use_container_width=True)
                except Exception:
                    st.markdown(f"📄 {fname}")

        if count < 5:
            st.warning(f"Need {5 - count} more PDF(s) to continue.")
        else:
            if st.button("➡️ Define Fields", type="primary"):
                st.session_state.step = 2
                st.rerun()
