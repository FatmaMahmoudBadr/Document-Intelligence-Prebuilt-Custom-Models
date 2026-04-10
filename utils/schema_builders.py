import fitz  # PyMuPDF


def build_labels_json(filename: str, annotations: list, pdf_bytes: bytes) -> dict:
    """
    Produces a <pdf>.labels.json matching the Azure DI schema exactly:

      boundingBoxes  — flat 8-float list of NORMALISED (0–1) coordinates
                       order: [x0,y0, x1,y0, x1,y1, x0,y1]  (TL→TR→BR→BL)
      labelType      — "region" for every drawn box
      text           — auto-extracted text (empty string for scanned PDFs)
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    labels = []
    for ann in annotations:
        page = doc[ann["page"]]
        iw   = ann.get("img_width",  1)
        ih   = ann.get("img_height", 1)

        # Normalised corner coords (0-1 range, relative to page size)
        x0n = ann["x"]              / iw
        y0n = ann["y"]              / ih
        x1n = (ann["x"] + ann["w"]) / iw
        y1n = (ann["y"] + ann["h"]) / ih

        # Flat 8-element bbox:  TL, TR, BR, BL
        bbox = [x0n, y0n,  x1n, y0n,  x1n, y1n,  x0n, y1n]

        labels.append({
            "label": ann["field"],
            "value": [
                {
                    "page":          ann["page"] + 1,   # 1-based page number
                    "text":          ann.get("text", ""),
                    "boundingBoxes": [bbox],
                }
            ],
            "labelType": "region",
        })

    return {
        "$schema":  "https://schema.cognitiveservices.azure.com/formrecognizer/2021-03-01/labels.json",
        "document": filename,
        "labels":   labels,
    }


def build_fields_json(fields: list, field_types: dict, field_formats: dict) -> dict:
    """
    Produces a single shared fields.json matching the Azure DI schema:

      { "fieldKey": "…", "fieldType": "string", "fieldFormat": "not-specified" }
    """
    return {
        "$schema": "https://schema.cognitiveservices.azure.com/formrecognizer/2021-03-01/fields.json",
        "fields": [
            {
                "fieldKey":    f,
                "fieldType":   field_types.get(f, "string"),
                "fieldFormat": field_formats.get(f, "not-specified"),
            }
            for f in fields
        ],
        "definitions": {},
    }