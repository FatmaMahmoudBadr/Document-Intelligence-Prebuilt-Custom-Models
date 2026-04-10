import fitz  # PyMuPDF
from PIL import Image, ImageDraw
from utils.config import FIELD_COLORS


def field_color(fields, field_name):
    try:
        return FIELD_COLORS[fields.index(field_name) % len(FIELD_COLORS)]
    except ValueError:
        return "#888888"


def render_page_pil(pdf_bytes: bytes, page_num: int, dpi: int = 150):
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_num]
    mat  = fitz.Matrix(dpi / 72, dpi / 72)
    pix  = page.get_pixmap(matrix=mat)
    img  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img, pix.width, pix.height


def get_page_count(pdf_bytes: bytes) -> int:
    return len(fitz.open(stream=pdf_bytes, filetype="pdf"))


def extract_text_from_box(
    pdf_bytes: bytes,
    page_num: int,
    x_px: int, y_px: int, w_px: int, h_px: int,
    img_w: int, img_h: int,
) -> str:
    doc   = fitz.open(stream=pdf_bytes, filetype="pdf")
    page  = doc[page_num]
    pw    = page.rect.width
    ph    = page.rect.height
    sx    = pw / img_w
    sy    = ph / img_h
    clip  = fitz.Rect(x_px*sx, y_px*sy, (x_px+w_px)*sx, (y_px+h_px)*sy)
    words = page.get_text("words", clip=clip, sort=True)
    text  = " ".join(w[4] for w in words).strip()
    if not text:
        text = page.get_text("text", clip=clip).strip()
    return text


def draw_annotations_on_img(img, annotations, fields, page_num):
    out  = img.copy()
    draw = ImageDraw.Draw(out)
    iw, ih = out.size
    for a in annotations:
        if a["page"] != page_num:
            continue
        color = field_color(fields, a["field"])
        sx = iw / a.get("img_width",  iw)
        sy = ih / a.get("img_height", ih)
        x0 = int(a["x"] * sx);  y0 = int(a["y"] * sy)
        x1 = int((a["x"] + a["w"]) * sx); y1 = int((a["y"] + a["h"]) * sy)
        draw.rectangle([x0, y0, x1, y1], outline=color, width=3)
        label = a["field"] + (f': {a["text"][:20]}' if a.get("text") else "")
        draw.rectangle([x0, max(0, y0-18), x0+len(label)*7+6, y0], fill=color)
        draw.text((x0+3, max(0, y0-16)), label, fill="white")
    return out