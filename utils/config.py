import os
from dotenv import load_dotenv

load_dotenv()

conn_string                  = os.getenv("CONNECTION_STRING")
container                    = os.getenv("CONTAINER")
account_url                  = os.getenv("ACCOUNT_URL")
sas_token                    = os.getenv("SAS_TOKEN")
document_entelligence_endpoint = os.getenv("AZURE_DI_ENDPOINT")
document_entelligence_key    = os.getenv("AZURE_DI_KEY")
sas_url                      = os.getenv("AZURE_BLOB_SAS_URL")

FIELD_COLORS = [
    "#E53935", "#1E88E5", "#43A047", "#FB8C00", "#8E24AA",
    "#00ACC1", "#F4511E", "#6D4C41", "#D81B60", "#546E7A", "#FFB300", "#00897B",
]

SESSION_DEFAULTS = {
    "step": 1,
    "uploaded_files": {},
    "fields": [],
    "field_types": {},
    "field_formats": {},
    "annotations": {},
    "model_id": "",
    "training_done": False,
    "anno_pdf": None,
    "anno_page": 0,
    "anno_field_idx": 0,
    "canvas_key": 0,
    "pending_box": None,
}
