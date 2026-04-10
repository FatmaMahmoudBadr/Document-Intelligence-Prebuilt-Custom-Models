import json
import uuid

import streamlit as st
from azure.ai.documentintelligence import DocumentIntelligenceAdministrationClient
from azure.ai.documentintelligence.models import BuildDocumentModelRequest, AzureBlobContentSource
from azure.core.credentials import AzureKeyCredential

from utils.config import document_entelligence_endpoint, document_entelligence_key, sas_url
from utils.pdf_utils import field_color
from utils.azure_utils import upload_to_blob, apply_ocr_and_build_json
from utils.schema_builders import build_labels_json, build_fields_json


def render_step4(di_endpoint: str, di_key: str):
    st.markdown('<p class="step-header">Step 4 — Train Custom Model</p>', unsafe_allow_html=True)

    model_id_input = st.text_input(
        "Model ID",
        value=st.session_state.model_id or f"custom-model-{uuid.uuid4().hex[:8]}",
        help="Alphanumeric + hyphens only. Must be unique in your Azure DI resource.",
    )
    description = st.text_input(
        "Description",
        value="Trained via Streamlit annotator",
    )
    st.session_state.model_id = model_id_input

    # ── Annotation summary ────────────────────────────────
    st.subheader("📋 Annotation Summary")
    for fname, anns in st.session_state.annotations.items():
        with st.expander(f"📄 {fname} — {len(anns)} annotation(s)"):
            for a in anns:
                color     = field_color(st.session_state.fields, a["field"])
                text_disp = f'`"{a["text"]}"` ✅' if a.get("text") else "*(no text)* ⚠️"
                st.markdown(
                    f'<span class="annotation-pill" style="background:{color}">{a["field"]}</span>'
                    f' page {a["page"]+1} — {text_disp}',
                    unsafe_allow_html=True,
                )

    st.divider()
    can_train = all([di_endpoint, di_key, model_id_input])
    if not can_train:
        st.warning("⚠️ Fill in all Azure credentials in the sidebar to enable training.")

    if can_train and not st.session_state.training_done:
        if st.button("🚀 Upload & Train", type="primary"):
            progress = st.progress(0, text="Starting…")

            # 1) Upload PDFs + OCR sidecars
            for i, (fname, pdf_bytes_item) in enumerate(st.session_state.uploaded_files.items()):
                try:
                    upload_to_blob(fname, pdf_bytes_item)
                    progress.progress(
                        (i+1) / len(st.session_state.uploaded_files) * 0.35 - 0.02,
                        text=f"Running OCR on {fname}…",
                    )
                    ocr_result = apply_ocr_and_build_json(
                        pdf_bytes_item, fname,
                        document_entelligence_endpoint,
                        document_entelligence_key,
                    )
                    upload_to_blob(
                        fname + ".ocr.json",
                        json.dumps(ocr_result, indent=2).encode(),
                    )
                    progress.progress(
                        (i+1) / len(st.session_state.uploaded_files) * 0.35,
                        text=f"✅ Uploaded PDF + OCR for {fname}",
                    )
                except Exception as e:
                    st.error(f"Upload failed for {fname}: {e}"); st.stop()

            # 2) Upload per-document labels.json
            for i, (fname, anns) in enumerate(st.session_state.annotations.items()):
                labels_data = build_labels_json(fname, anns, st.session_state.uploaded_files[fname])
                lbl_path    = fname + ".labels.json"
                try:
                    upload_to_blob(lbl_path, json.dumps(labels_data, indent="\t").encode())
                    progress.progress(
                        0.35 + (i+1) / len(st.session_state.annotations) * 0.30,
                        text=f"Uploaded labels for {fname}",
                    )
                except Exception as e:
                    st.error(f"Label upload failed: {e}"); st.stop()

            # 3) Upload shared fields.json
            fields_data = build_fields_json(
                st.session_state.fields,
                st.session_state.field_types,
                st.session_state.field_formats,
            )
            try:
                upload_to_blob("fields.json", json.dumps(fields_data, indent="\t").encode())
                progress.progress(0.70, text="Uploaded fields.json")
            except Exception as e:
                st.error(f"fields.json upload failed: {e}"); st.stop()

            # 4) Kick off training
            try:
                admin = DocumentIntelligenceAdministrationClient(
                    endpoint=di_endpoint,
                    credential=AzureKeyCredential(di_key),
                )
                progress.progress(0.75, text="Submitting training job…")

                request = BuildDocumentModelRequest(
                    model_id=model_id_input,
                    description=description,
                    build_mode="template",
                    azure_blob_source=AzureBlobContentSource(container_url=sas_url),
                )
                poller = admin.begin_build_document_model(request)

                progress.progress(0.88, text="Training in progress… (may take a few minutes)")
                result = poller.result()
                progress.progress(1.0, text="Done!")

                st.session_state.training_done = True
                st.success(f"🎉 Model `{result.model_id}` trained successfully!")
                st.balloons()
                # st.json({"model_id": result.model_id, "created_on": str(result.created_on)})

            except Exception as e:
                st.error(f"Training failed: {e}")
                st.exception(e)

    elif st.session_state.training_done:
        st.success(f"✅ Model `{st.session_state.model_id}` is ready to use.")

    if st.button("⬅️ Back to Annotations"):
        st.session_state.step = 3
        st.rerun()