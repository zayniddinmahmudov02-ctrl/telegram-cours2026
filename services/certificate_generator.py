from pathlib import Path
from datetime import datetime

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
# =========================================================
# ROOT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CERTIFICATES_DIR = (
    BASE_DIR / "certificates"
)

ASSETS_DIR = (
    CERTIFICATES_DIR / "assets"
)

FONTS_DIR = (
    ASSETS_DIR / "fonts"
)

GENERATED_DIR = (
    CERTIFICATES_DIR / "generated"
)
# =========================================================
# LEVEL PATHS
# =========================================================

LEVEL_PATHS = {

    "A1": ASSETS_DIR / "a1",

    "A2": ASSETS_DIR / "a2",

    "B1": ASSETS_DIR / "b1",

    "B2": ASSETS_DIR / "b2",

    "C1": ASSETS_DIR / "c1",

}
# =========================================================
# GRADE FILES
# =========================================================

GRADE_FILES = {

    "🥇 Gold": {

        "header": "gold-header.png",

        "footer": "gold-footer.png",

    },

    "🥈 Silver": {

        "header": "silver-header.png",

        "footer": "silver-footer.png",

    },

    "🥉 Bronze": {

        "header": "bronze-header.png",

        "footer": "bronze-footer.png",

    },

    "✅ Pass": {

        "header": "pass-header.png",

        "footer": "pass-footer.png",

    },

}
# =========================================================
# COLORS
# =========================================================

PRIMARY = HexColor("#0B1F3A")

SECONDARY = HexColor("#3D5A80")

TEXT = HexColor("#2E2E2E")

GRAY = HexColor("#666666")

GOLD = HexColor("#C9A227")

SILVER = HexColor("#8E8E8E")

BRONZE = HexColor("#8B5A2B")
# =========================================================
# PAGE SETTINGS
# =========================================================

PAGE_WIDTH, PAGE_HEIGHT = A4

TOP_MARGIN = 20 * mm

BOTTOM_MARGIN = 20 * mm

LEFT_MARGIN = 20 * mm

RIGHT_MARGIN = 20 * mm
# =========================================================
# FONT NAMES
# =========================================================

TITLE_FONT = "Cinzel-Bold"

NAME_FONT = "Cinzel-Bold"

TEXT_FONT = "Montserrat-Regular"

TEXT_BOLD = "Montserrat-Bold"
# =========================================================
# DATE
# =========================================================

def today():

    return datetime.now().strftime(
        "%d.%m.%Y"
    )
# =========================================================
# REGISTER FONTS
# =========================================================

def register_fonts():

    fonts = {

        "Cinzel-Bold":
            "Cinzel-Bold.ttf",

        "Montserrat-Regular":
            "Montserrat-Regular.ttf",

        "Montserrat-Bold":
            "Montserrat-Bold.ttf",

    }

    for font_name, file_name in fonts.items():

        font_path = FONTS_DIR / file_name

        if not font_path.exists():

            raise FileNotFoundError(
                f"Font topilmadi: {font_path}"
            )

        pdfmetrics.registerFont(
            TTFont(
                font_name,
                str(font_path),
            )
        )
# =========================================================
# STYLES
# =========================================================

styles = getSampleStyleSheet()


TITLE_STYLE = ParagraphStyle(

    "Title",

    parent=styles["Normal"],

    fontName=TITLE_FONT,

    fontSize=26,

    leading=32,

    alignment=TA_CENTER,

    textColor=PRIMARY,

    spaceAfter=10,

)


NAME_STYLE = ParagraphStyle(

    "Name",

    parent=styles["Normal"],

    fontName=NAME_FONT,

    fontSize=22,

    leading=28,

    alignment=TA_CENTER,

    textColor=TEXT,

    spaceAfter=14,

)


BODY_STYLE = ParagraphStyle(

    "Body",

    parent=styles["Normal"],

    fontName=TEXT_FONT,

    fontSize=13,

    leading=20,

    alignment=TA_CENTER,

    textColor=TEXT,

)


GRADE_STYLE = ParagraphStyle(

    "Grade",

    parent=styles["Normal"],

    fontName=TEXT_BOLD,

    fontSize=18,

    leading=24,

    alignment=TA_CENTER,

    textColor=PRIMARY,

)


FOOTER_STYLE = ParagraphStyle(

    "Footer",

    parent=styles["Normal"],

    fontName=TEXT_FONT,

    fontSize=11,

    leading=16,

    alignment=TA_CENTER,

    textColor=GRAY,

)
# =========================================================
# CREATE GENERATED DIRECTORY
# =========================================================

def ensure_directories():

    GENERATED_DIR.mkdir(

        parents=True,

        exist_ok=True,

    )
# =========================================================
# GET TEMPLATE FILES
# =========================================================

def get_template_files(

    level: str,

    grade: str,

):

    level_dir = LEVEL_PATHS[level]

    grade_files = GRADE_FILES[grade]

    header = (
        level_dir /
        grade_files["header"]
    )

    footer = (
        level_dir /
        grade_files["footer"]
    )

    if not header.exists():

        raise FileNotFoundError(

            f"Header topilmadi: {header}"

        )

    if not footer.exists():

        raise FileNotFoundError(

            f"Footer topilmadi: {footer}"

        )

    return (

        str(header),

        str(footer),

    )
# =========================================================
# FILE NAME
# =========================================================

def build_file_name(

    certificate_id: str,

):

    return (

        GENERATED_DIR /

        f"{certificate_id}.pdf"

    )
# =========================================================
# FORMAT NAME
# =========================================================

def format_name(

    full_name: str,

):

    full_name = full_name.strip()

    full_name = " ".join(

        full_name.split()

    )

    return full_name.upper()
# =========================================================
# CREATE DOCUMENT
# =========================================================

def create_document(

    file_path,

):

    return SimpleDocTemplate(

        str(file_path),

        pagesize=A4,

        leftMargin=LEFT_MARGIN,

        rightMargin=RIGHT_MARGIN,

        topMargin=TOP_MARGIN,

        bottomMargin=BOTTOM_MARGIN,

    )
# =========================================================
# BUILD STORY
# =========================================================

def build_story(
    full_name: str,
    level: str,
    average: int,
    grade: str,
    certificate_id: str,
):

    story = []

    # Header rasmi uchun joy
    story.append(
        Spacer(
            1,
            110 * mm,
        )
    )

    story.append(
        Paragraph(
            "W-ZERTIFIKAT",
            TITLE_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "Visuales Institut für "
                "Zukunft und Unterricht"
            ),
            BODY_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "Ushbu sertifikat"
            ),
            BODY_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            format_name(full_name),
            NAME_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "nemis tili bo'yicha"
            ),
            BODY_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    story.append(
        Paragraph(
            level,
            TITLE_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "darajasini muvaffaqiyatli "
                "yakunlagani uchun taqdim etiladi."
            ),
            BODY_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            10 * mm,
        )
    )

    story.append(
        Paragraph(
            grade,
            GRADE_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    story.append(
        Paragraph(
            f"{average} %",
            GRADE_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            14 * mm,
        )
    )

    story.append(
        Paragraph(
            f"Certificate ID: {certificate_id}",
            FOOTER_STYLE,
        )
    )

    story.append(
        Paragraph(
            f"Berilgan sana: {today()}",
            FOOTER_STYLE,
        )
    )

    return story
# =========================================================
# HEADER / FOOTER
# =========================================================

def draw_background(
    canvas,
    doc,
    header,
    footer,
):

    canvas.saveState()

    canvas.drawImage(

        header,

        0,

        PAGE_HEIGHT - 70 * mm,

        width=PAGE_WIDTH,

        height=70 * mm,

        preserveAspectRatio=False,

        mask="auto",

    )

    canvas.drawImage(

        footer,

        0,

        0,

        width=PAGE_WIDTH,

        height=40 * mm,

        preserveAspectRatio=False,

        mask="auto",

    )

    canvas.restoreState()
# =========================================================
# GENERATE CERTIFICATE
# =========================================================

def generate_certificate(

    full_name: str,

    level: str,

    average: int,

    grade: str,

    certificate_id: str,

):

    register_fonts()

    ensure_directories()

    header, footer = get_template_files(

        level,

        grade,

    )

    pdf_path = build_file_name(

        certificate_id,

    )

    document = create_document(

        pdf_path,

    )

    story = build_story(

        full_name,

        level,

        average,

        grade,

        certificate_id,

    )

    document.build(

        story,

        onFirstPage=lambda c, d: draw_background(

            c,

            d,

            header,

            footer,

        ),

    )

    return str(pdf_path)
__all__ = [

    "generate_certificate",

]
def draw_title(story):

    story.append(
        Paragraph(
            "W-ZERTIFIKAT",
            TITLE_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    story.append(
        Paragraph(
            "Visuales Institut für Zukunft und Unterricht",
            BODY_STYLE,
        )
    )
def draw_student_name(
    story,
    full_name,
):

    story.append(
        Spacer(
            1,
            10 * mm,
        )
    )

    story.append(
        Paragraph(
            format_name(full_name),
            NAME_STYLE,
        )
    )
def draw_level(
    story,
    level,
):

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            level,
            TITLE_STYLE,
        )
    )
def draw_grade(
    story,
    grade,
):

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        Paragraph(
            grade,
            GRADE_STYLE,
        )
    )
def draw_average(
    story,
    average,
):

    story.append(
        Paragraph(
            f"{average} %",
            GRADE_STYLE,
        )
    )
def draw_certificate_id(
    story,
    certificate_id,
):

    story.append(
        Spacer(
            1,
            15 * mm,
        )
    )

    story.append(
        Paragraph(
            f"Certificate ID: {certificate_id}",
            FOOTER_STYLE,
        )
    )
def draw_issue_date(story):

    story.append(
        Paragraph(
            f"Issued: {today()}",
            FOOTER_STYLE,
        )
    )