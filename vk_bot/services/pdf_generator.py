from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from PIL import Image as PILImage, ImageOps
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import DOCS_DIR, FONTS_DIR, LOGO_PATH
from services.report_service import get_defects, get_report

PAGE_WIDTH, PAGE_HEIGHT = A4
CONTENT_WIDTH = 180 * mm
TEXT_COL_WIDTH = 14 * mm
DESC_COL_WIDTH = 166 * mm
PHOTO_MAX_WIDTH_FULL = 168
PHOTO_MAX_HEIGHT_FULL = 105
PHOTO_MAX_WIDTH_HALF = 82
PHOTO_MAX_HEIGHT_HALF = 112

_FONT_CACHE: dict[str, str] | None = None


def _candidate_font_paths() -> list[dict[str, str]]:
    fonts_dir = Path(FONTS_DIR)
    return [
        {
            "regular": str(fonts_dir / "times.ttf"),
            "bold": str(fonts_dir / "timesbd.ttf"),
            "italic": str(fonts_dir / "timesi.ttf"),
            "bold_italic": str(fonts_dir / "timesbi.ttf"),
            "family": "Times New Roman",
        },
        {
            "regular": str(fonts_dir / "Times New Roman.ttf"),
            "bold": str(fonts_dir / "Times New Roman Bold.ttf"),
            "italic": str(fonts_dir / "Times New Roman Italic.ttf"),
            "bold_italic": str(fonts_dir / "Times New Roman Bold Italic.ttf"),
            "family": "Times New Roman",
        },
        {
            "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "italic": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
            "bold_italic": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
            "family": "DejaVu Serif",
        },
    ]


def _register_fonts() -> dict[str, str]:
    global _FONT_CACHE
    if _FONT_CACHE is not None:
        return _FONT_CACHE

    for candidate in _candidate_font_paths():
        regular = Path(candidate["regular"])
        bold = Path(candidate["bold"])
        italic = Path(candidate["italic"])
        bold_italic = Path(candidate["bold_italic"])
        if not all(path.exists() for path in (regular, bold, italic, bold_italic)):
            continue
        try:
            pdfmetrics.registerFont(TTFont("AppRegular", str(regular)))
            pdfmetrics.registerFont(TTFont("AppBold", str(bold)))
            pdfmetrics.registerFont(TTFont("AppItalic", str(italic)))
            pdfmetrics.registerFont(TTFont("AppBoldItalic", str(bold_italic)))
            _FONT_CACHE = {
                "regular": "AppRegular",
                "bold": "AppBold",
                "italic": "AppItalic",
                "bold_italic": "AppBoldItalic",
                "family": candidate["family"],
            }
            return _FONT_CACHE
        except Exception:
            continue

    _FONT_CACHE = {
        "regular": "Times-Roman",
        "bold": "Times-Bold",
        "italic": "Times-Italic",
        "bold_italic": "Times-BoldItalic",
        "family": "Times",
    }
    return _FONT_CACHE


def _styles() -> dict[str, ParagraphStyle]:
    fonts = _register_fonts()
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title_app",
            parent=styles["Title"],
            fontName=fonts["bold"],
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "subtitle_app",
            parent=styles["Normal"],
            fontName=fonts["bold"],
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "label": ParagraphStyle(
            "label_app",
            parent=styles["Normal"],
            fontName=fonts["bold"],
            fontSize=9.8,
            leading=12,
        ),
        "value": ParagraphStyle(
            "value_app",
            parent=styles["Normal"],
            fontName=fonts["regular"],
            fontSize=9.8,
            leading=12,
        ),
        "body": ParagraphStyle(
            "body_app",
            parent=styles["Normal"],
            fontName=fonts["regular"],
            fontSize=9.6,
            leading=12,
            spaceAfter=0,
        ),
        "small": ParagraphStyle(
            "small_app",
            parent=styles["Normal"],
            fontName=fonts["regular"],
            fontSize=8.2,
            leading=10,
        ),
        "small_bold": ParagraphStyle(
            "small_bold_app",
            parent=styles["Normal"],
            fontName=fonts["bold"],
            fontSize=8.2,
            leading=10,
        ),
        "section": ParagraphStyle(
            "section_app",
            parent=styles["Normal"],
            fontName=fonts["bold"],
            fontSize=10.5,
            leading=13,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "footer": ParagraphStyle(
            "footer_app",
            parent=styles["Normal"],
            fontName=fonts["bold"],
            fontSize=8.2,
            leading=10,
            alignment=TA_RIGHT,
        ),
    }


def _safe(value: object) -> str:
    text = str(value).strip() if value is not None else ""
    return text or "—"


def _fit_image_dimensions(width_px: int, height_px: int, max_width_mm: float, max_height_mm: float) -> tuple[float, float]:
    if width_px <= 0 or height_px <= 0:
        return max_width_mm * mm, max_height_mm * mm
    width_pt = width_px * 72.0 / 96.0
    height_pt = height_px * 72.0 / 96.0
    max_w = max_width_mm * mm
    max_h = max_height_mm * mm
    ratio = min(max_w / width_pt, max_h / height_pt, 1.0)
    return width_pt * ratio, height_pt * ratio


def _read_image_meta(path: Path) -> dict | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        with PILImage.open(path) as img:
            img = ImageOps.exif_transpose(img)
            width, height = img.size
            return {
                "path": path,
                "width": width,
                "height": height,
                "orientation": "vertical" if height > width else "horizontal",
            }
    except Exception:
        return None


def _build_rl_image(meta: dict, max_width_mm: float, max_height_mm: float) -> Image:
    img = Image(str(meta["path"]))
    img._restrictSize(max_width_mm * mm, max_height_mm * mm)
    img.hAlign = "CENTER"
    return img


def _logo_story(styles: dict, max_width_mm: float = 52) -> list:
    logo_path = Path(LOGO_PATH)
    if logo_path.exists() and logo_path.is_file():
        try:
            meta = _read_image_meta(logo_path)
            if meta:
                img = _build_rl_image(meta, max_width_mm, 22)
                return [img, Spacer(1, 3 * mm)]
        except Exception:
            pass
    return [
        Paragraph('ООО "Техноком"', styles["subtitle"]),
        Paragraph("Логотип не задан", styles["small"]),
        Spacer(1, 3 * mm),
    ]


def _meta_table(report: dict, styles: dict) -> Table:
    rows = [
        [Paragraph("Номер ведомости", styles["label"]), Paragraph(_safe(report.get("report_number")), styles["value"])],
        [Paragraph("Дата создания", styles["label"]), Paragraph(_safe(report.get("created_at")), styles["value"])],
        [Paragraph("Заказчик", styles["label"]), Paragraph(_safe(report.get("client_name")), styles["value"])],
        [Paragraph("Телефон", styles["label"]), Paragraph(_safe(report.get("client_phone")), styles["value"])],
        [Paragraph("Объект", styles["label"]), Paragraph(_safe(report.get("object_name")), styles["value"])],
        [Paragraph("Техника / узел", styles["label"]), Paragraph(_safe(report.get("equipment")), styles["value"])],
        [Paragraph("Комментарий", styles["label"]), Paragraph(_safe(report.get("comment")), styles["value"])],
    ]
    table = Table(rows, colWidths=[48 * mm, 132 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _defects_table(defects: Iterable[dict], styles: dict) -> Table:
    rows: list[list] = [[Paragraph("№", styles["label"]), Paragraph("Описание дефекта", styles["label"]), Paragraph("Фото", styles["label"])]]
    defects = list(defects)
    if not defects:
        rows.append([Paragraph("1", styles["value"]), Paragraph("Дефекты не указаны.", styles["body"]), Paragraph("—", styles["value"])])
    else:
        for idx, defect in enumerate(defects, start=1):
            marker = "Да" if defect.get("photo_path") else "Нет"
            rows.append(
                [
                    Paragraph(str(idx), styles["value"]),
                    Paragraph(_safe(defect.get("description")), styles["body"]),
                    Paragraph(marker, styles["value"]),
                ]
            )
    table = Table(rows, colWidths=[TEXT_COL_WIDTH, 136 * mm, 30 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAEA")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _caption_for_defect(index: int, defect: dict, styles: dict) -> Paragraph:
    desc = _safe(defect.get("description"))
    if len(desc) > 110:
        desc = desc[:107].rstrip() + "…"
    return Paragraph(f"Дефект {index}. {desc}", styles["small"])


def _photo_cell(meta: dict, caption: Paragraph, half: bool, styles: dict) -> Table:
    img = _build_rl_image(
        meta,
        PHOTO_MAX_WIDTH_HALF if half else PHOTO_MAX_WIDTH_FULL,
        PHOTO_MAX_HEIGHT_HALF if half else PHOTO_MAX_HEIGHT_FULL,
    )
    table = Table([[img], [caption]], colWidths=[84 * mm if half else 170 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.45, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _empty_half_cell(styles: dict) -> Table:
    table = Table([[Paragraph("", styles["small"])]], colWidths=[84 * mm], rowHeights=[2 * mm])
    table.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0, colors.white)]))
    return table


def _photo_gallery(defects: Iterable[dict], styles: dict) -> list:
    items: list[dict] = []
    for index, defect in enumerate(defects, start=1):
        path_value = defect.get("photo_path")
        if not path_value:
            continue
        meta = _read_image_meta(Path(path_value))
        if not meta:
            continue
        meta["caption"] = _caption_for_defect(index, defect, styles)
        items.append(meta)

    if not items:
        return [Paragraph("Фотографии дефектов отсутствуют.", styles["body"])]

    story: list = []
    row_buffer: list[Table] = []
    for item in items:
        if item["orientation"] == "horizontal":
            if row_buffer:
                if len(row_buffer) == 1:
                    row_buffer.append(_empty_half_cell(styles))
                tbl = Table([row_buffer], colWidths=[85 * mm, 85 * mm])
                tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
                story.extend([tbl, Spacer(1, 3 * mm)])
                row_buffer = []
            full_tbl = Table([[_photo_cell(item, item["caption"], half=False, styles=styles)]], colWidths=[170 * mm])
            full_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story.extend([full_tbl, Spacer(1, 3 * mm)])
            continue

        row_buffer.append(_photo_cell(item, item["caption"], half=True, styles=styles))
        if len(row_buffer) == 2:
            tbl = Table([row_buffer], colWidths=[85 * mm, 85 * mm])
            tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story.extend([tbl, Spacer(1, 3 * mm)])
            row_buffer = []

    if row_buffer:
        row_buffer.append(_empty_half_cell(styles))
        tbl = Table([row_buffer], colWidths=[85 * mm, 85 * mm])
        tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(tbl)
    return story


def _first_page(canvas, doc):
    canvas.saveState()
    canvas.setTitle(doc.title or "Дефектная ведомость")
    canvas.setAuthor('ООО "Техноком"')
    canvas.setSubject("Дефектная ведомость")
    canvas.restoreState()


def _later_pages(canvas, doc):
    fonts = _register_fonts()
    canvas.saveState()
    canvas.setFont(fonts["regular"], 8)
    canvas.drawRightString(PAGE_WIDTH - 15 * mm, 10 * mm, f"Стр. {canvas.getPageNumber()}")
    canvas.restoreState()


def build_pdf(report_id: int) -> Path:
    report = get_report(report_id)
    if not report:
        raise ValueError(f"Ведомость {report_id} не найдена")

    defects = get_defects(report_id)
    styles = _styles()
    safe_number = (report.get("report_number", str(report_id)) or str(report_id)).replace("№ ", "").replace("/", "-")
    path = DOCS_DIR / f"defect_statement_{safe_number}.pdf"

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"Дефектная ведомость {report.get('report_number')}",
        author='ООО "Техноком"',
        pageCompression=1,
    )

    story: list = []
    story.extend(_logo_story(styles))
    story.append(Paragraph("ДЕФЕКТНАЯ ВЕДОМОСТЬ", styles["title"]))
    story.append(Paragraph(_safe(report.get("report_number")), styles["subtitle"]))
    story.append(_meta_table(report, styles))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("Таблица дефектов", styles["section"]))
    story.append(_defects_table(defects, styles))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("Фотоматериалы", styles["section"]))
    story.extend(_photo_gallery(defects, styles))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(f'Сформировано: {datetime.now().strftime("%d.%m.%Y %H:%M")}', styles["small"]))
    story.append(Paragraph('ООО "Техноком"', styles["footer"]))

    doc.build(story, onFirstPage=_first_page, onLaterPages=_later_pages)
    return path
