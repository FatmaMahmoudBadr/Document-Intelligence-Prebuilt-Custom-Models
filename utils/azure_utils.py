import json
from datetime import datetime, timezone

from azure.storage.blob import BlobServiceClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from utils.config import account_url, sas_token, container


def upload_to_blob(file_name: str, file_data: bytes) -> None:
    client = BlobServiceClient(account_url=account_url, credential=sas_token)
    container_client = client.get_container_client(container)
    container_client.upload_blob(
        name=file_name,
        data=file_data,
        overwrite=True,
    )
    print("successfuly uploaded")


def apply_ocr_and_build_json(
    pdf_bytes: bytes,
    filename: str,
    di_endpoint: str,
    di_key: str,
) -> dict:
    """
    Runs Azure Document Intelligence prebuilt-layout on a PDF and returns
    a dict that exactly matches the *.ocr.json schema used by DI Studio.
    """
    client = DocumentIntelligenceClient(
        endpoint=di_endpoint,
        credential=AzureKeyCredential(di_key),
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    poller = client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=pdf_bytes,
        content_type="application/octet-stream",
    )
    result = poller.result()

    # ── pages ─────────────────────────────────────────────
    pages_out = []
    for page in (result.pages or []):
        words_out = [
            {
                "content":    w.content,
                "polygon":    list(w.polygon) if w.polygon else [],
                "confidence": w.confidence,
                "span": {
                    "offset": w.span.offset,
                    "length": w.span.length,
                },
            }
            for w in (page.words or [])
        ]
        lines_out = [
            {
                "content": l.content,
                "polygon": list(l.polygon) if l.polygon else [],
                "spans": [
                    {"offset": s.offset, "length": s.length}
                    for s in (l.spans or [])
                ],
            }
            for l in (page.lines or [])
        ]
        spans_out = [
            {"offset": s.offset, "length": s.length}
            for s in (page.spans or [])
        ]
        pages_out.append({
            "pageNumber": page.page_number,
            "angle":      page.angle,
            "width":      page.width,
            "height":     page.height,
            "unit":       page.unit,
            "words":      words_out,
            "lines":      lines_out,
            "spans":      spans_out,
        })

    # ── tables ────────────────────────────────────────────
    tables_out = []
    for table in (result.tables or []):
        cells_out = []
        for cell in (table.cells or []):
            cell_dict = {
                "rowIndex":    cell.row_index,
                "columnIndex": cell.column_index,
                "content":     cell.content,
                "boundingRegions": [
                    {
                        "pageNumber": br.page_number,
                        "polygon":    list(br.polygon) if br.polygon else [],
                    }
                    for br in (cell.bounding_regions or [])
                ],
                "spans": [
                    {"offset": s.offset, "length": s.length}
                    for s in (cell.spans or [])
                ],
            }
            if cell.kind and cell.kind != "content":
                cell_dict["kind"] = cell.kind
            if cell.elements:
                cell_dict["elements"] = list(cell.elements)
            cells_out.append(cell_dict)

        tables_out.append({
            "rowCount":    table.row_count,
            "columnCount": table.column_count,
            "cells":       cells_out,
            "boundingRegions": [
                {
                    "pageNumber": br.page_number,
                    "polygon":    list(br.polygon) if br.polygon else [],
                }
                for br in (table.bounding_regions or [])
            ],
            "spans": [
                {"offset": s.offset, "length": s.length}
                for s in (table.spans or [])
            ],
        })

    # ── paragraphs ────────────────────────────────────────
    paragraphs_out = []
    for para in (result.paragraphs or []):
        para_dict = {
            "spans": [
                {"offset": s.offset, "length": s.length}
                for s in (para.spans or [])
            ],
            "boundingRegions": [
                {
                    "pageNumber": br.page_number,
                    "polygon":    list(br.polygon) if br.polygon else [],
                }
                for br in (para.bounding_regions or [])
            ],
            "content": para.content,
        }
        if para.role:
            para_dict["role"] = para.role
        paragraphs_out.append(para_dict)

    # ── figures ───────────────────────────────────────────
    figures_out = []
    for fig in (result.figures or []):
        fig_dict = {
            "id": fig.figure_id,
            "boundingRegions": [
                {
                    "pageNumber": br.page_number,
                    "polygon":    list(br.polygon) if br.polygon else [],
                }
                for br in (fig.bounding_regions or [])
            ],
            "spans": [
                {"offset": s.offset, "length": s.length}
                for s in (fig.spans or [])
            ],
        }
        if fig.elements:
            fig_dict["elements"] = list(fig.elements)
        if fig.caption:
            fig_dict["caption"] = {
                "content": fig.caption.content,
                "boundingRegions": [
                    {
                        "pageNumber": br.page_number,
                        "polygon":    list(br.polygon) if br.polygon else [],
                    }
                    for br in (fig.caption.bounding_regions or [])
                ],
                "spans": [
                    {"offset": s.offset, "length": s.length}
                    for s in (fig.caption.spans or [])
                ],
            }
        figures_out.append(fig_dict)

    # ── sections ──────────────────────────────────────────
    sections_out = []
    for sec in (result.sections or []):
        sec_dict = {
            "spans": [
                {"offset": s.offset, "length": s.length}
                for s in (sec.spans or [])
            ],
        }
        if sec.elements:
            sec_dict["elements"] = list(sec.elements)
        sections_out.append(sec_dict)

    # ── styles ────────────────────────────────────────────
    styles_out = []
    for style in (result.styles or []):
        style_dict = {
            "confidence": style.confidence,
            "spans": [
                {"offset": s.offset, "length": s.length}
                for s in (style.spans or [])
            ],
        }
        if style.is_handwritten is not None:
            style_dict["isHandwritten"] = style.is_handwritten
        styles_out.append(style_dict)

    # ── assemble final structure ──────────────────────────
    return {
        "status":              "succeeded",
        "createdDateTime":     now,
        "lastUpdatedDateTime": now,
        "analyzeResult": {
            "apiVersion":      "2024-11-30",
            "modelId":         "prebuilt-layout",
            "stringIndexType": "utf16CodeUnit",
            "content":         result.content or "",
            "pages":           pages_out,
            "tables":          tables_out,
            "paragraphs":      paragraphs_out,
            "styles":          styles_out,
            "contentFormat":   "text",
            "sections":        sections_out,
            "figures":         figures_out,
        },
    }