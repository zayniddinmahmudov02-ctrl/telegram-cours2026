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
from database.users import get_user

from database.certificates import (
    create_certificate,
    get_level_certificate,
)

from services.certificate import (
    build_level_status,
    calculate_rank,
)
# =========================================================
# ROOT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CERTIFICATES_DIR = (
    BASE_DIR / "certificates"
)

FONTS_DIR = (
    BASE_DIR / "fonts"
)

GENERATED_DIR = (
    CERTIFICATES_DIR / "generated"
)
# =========================================================
# LEVEL PATHS
# =========================================================
# Real asset folders on disk: certificates/a1-level/, etc.

LEVEL_PATHS = {

    "A1": CERTIFICATES_DIR / "a1-level",

    "A2": CERTIFICATES_DIR / "a2-level",

    "B1": CERTIFICATES_DIR / "b1-level",

    "B2": CERTIFICATES_DIR / "b2-level",

    "C1": CERTIFICATES_DIR / "c1-level",

}
# =========================================================
# GRADE FILE SLUGS
# =========================================================
# Real filenames on disk are level-prefixed, e.g.
# certificates/a1-level/a1-gold-header.png. Only Gold/Silver/
# Bronze artwork exists (no "Participant" tier - calculate_rank
# in services/certificate.py never returns anything else).

GRADE_SLUGS = {

    "🥇 Gold": "gold",

    "🥈 Silver": "silver",

    "🥉 Bronze": "bronze",

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
# Real font files on disk are under fonts/: GreatVibes-Regular
# (a script/signature-style face, used for the title and name),
# Montserrat-Regular/Bold for body text.

TITLE_FONT = "GreatVibes-Regular"

NAME_FONT = "GreatVibes-Regular"

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

        "GreatVibes-Regular":
            "GreatVibes-Regular.ttf",

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
# USER DATA
# =========================================================

def get_certificate_user(
    user_id: int,
):

    user = get_user(user_id)

    if not user:
        raise ValueError(
            "User topilmadi."
        )

    return user


# =========================================================
# CERTIFICATE DATA
# =========================================================

def get_certificate_data(
    user_id: int,
    level: str,
    admin_override: bool = False,
):

    status = build_level_status(
        user_id,
        level,
    )

    if not status["ready"] and not admin_override:
        raise ValueError(
            "Sertifikat hali tayyor emas."
        )

    if not status["ready"]:
        # Admin test/preview mode - grade a placeholder
        # certificate from whatever progress exists so the
        # PDF layout can be reviewed without completing a
        # level for real.
        status = dict(status)
        status["rank"] = calculate_rank(status["average"])

    return status


# =========================================================
# CERTIFICATE ID
# =========================================================

def get_certificate_id(
    user_id: int,
    level: str,
    average: int,
    grade: str,
):

    certificate = get_level_certificate(
        user_id,
        "W",
        level,
    )

    if certificate:
        return certificate["certificate_id"]

    return create_certificate(
        user_id=user_id,
        certificate_type="W",
        level=level,
        score=average,
        percent=average,
        rank=grade,
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

    slug = GRADE_SLUGS[grade]

    level_slug = level.lower()

    header = (
        level_dir /
        f"{level_slug}-{slug}-header.png"
    )

    footer = (
        level_dir /
        f"{level_slug}-{slug}-footer.png"
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


def get_certificate_file_path(certificate_id: str) -> Path:
    """
    Path to an already-generated certificate's PDF (admin
    browsing - looks up by certificate_id directly, no
    readiness check, no regeneration).
    """

    return build_file_name(certificate_id)
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

    # Header rasmi uchun joy (header 70mm baland - draw_background)
    story.append(
        Spacer(
            1,
            78 * mm,
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
    user_id: int,
    level: str,
    admin_override: bool = False,
):
    """
    Returns the path to the user's PDF certificate for `level`.

    Idempotent: the same user+level always maps to the same
    certificate_id (get_certificate_id reuses an existing DB
    row instead of creating a duplicate), and if that
    certificate's PDF file already exists on disk it is
    returned as-is instead of being rebuilt.
    """

    user = get_certificate_user(
        user_id,
    )

    status = get_certificate_data(
        user_id,
        level,
        admin_override=admin_override,
    )

    certificate_id = get_certificate_id(
        user_id=user_id,
        level=level,
        average=status["average"],
        grade=status["rank"],
    )

    ensure_directories()

    pdf_path = build_file_name(
        certificate_id,
    )

    if pdf_path.exists():
        return str(pdf_path)

    register_fonts()

    header, footer = get_template_files(
        level,
        status["rank"],
    )

    document = create_document(
        pdf_path,
    )

    story = build_story(
        full_name=user["full_name"],
        level=level,
        average=status["average"],
        grade=status["rank"],
        certificate_id=certificate_id,
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