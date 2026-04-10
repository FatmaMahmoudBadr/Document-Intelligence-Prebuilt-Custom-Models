import streamlit as st

from utils.config import SESSION_DEFAULTS
from steps.step1_upload import render_step1
from steps.step2_fields import render_step2
from steps.step3_annotate import render_step3
from steps.step4_train import render_step4

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Azure DI — Custom Model Trainer",
    page_icon="📄",
    layout="wide",
)

st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; }
    .stButton>button { border-radius: 6px; font-weight: 600; }
    .annotation-pill {
        display: inline-block; padding: 3px 10px; border-radius: 20px;
        font-size: 12px; font-weight: 700; color: white; margin: 2px;
    }
    .step-header { font-size: 1.4rem; font-weight: 700; margin-bottom: 0.5rem; }
    .extracted-text-box {
        background: #f0fff4; border: 1px solid #38a169; border-radius: 6px;
        padding: 8px 12px; font-family: monospace; font-size: 13px;
        color: #276749; margin: 4px 0;
    }
    .no-text-box {
        background: #fff5f5; border: 1px solid #fc8181; border-radius: 6px;
        padding: 8px 12px; font-size: 13px; color: #c53030; margin: 4px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("📄 Azure Document Intelligence — Custom Model Trainer")

# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────
for k, v in SESSION_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("🔑 Azure Configuration")
    di_endpoint    = st.text_input("DI Endpoint", placeholder="https://<resource>.cognitiveservices.azure.com/")
    di_key         = st.text_input("DI Key", type="password")
    blob_conn_str  = st.text_input("Blob Connection String", type="password")
    blob_container = st.text_input("Blob Container", placeholder="training-docs")

    st.divider()
    st.markdown("**Progress**")
    step_labels = ["Upload PDFs", "Define Fields", "Annotate", "Train Model"]
    for i, label in enumerate(step_labels, 1):
        icon = "✅" if st.session_state.step > i else ("▶️" if st.session_state.step == i else "○")
        st.markdown(f"{icon} {label}")

# ─────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────
if st.session_state.step == 1:
    render_step1()

elif st.session_state.step == 2:
    render_step2()

elif st.session_state.step == 3:
    render_step3()

elif st.session_state.step == 4:
    render_step4(di_endpoint=di_endpoint, di_key=di_key)
