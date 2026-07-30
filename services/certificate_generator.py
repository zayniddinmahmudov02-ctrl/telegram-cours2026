from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from config import LEVEL_CONFIG

from database.users import get_user
from database.certificates import (
    create_certificate,
    get_level_certificate,
)
from database.leaderboard import get_accuracy

from services.certificate import (
    build_level_status,
    calculate_rank,
)

# =========================================================
# ROOT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = BASE_DIR / "assets"
TEMPLATES_DIR = BASE_DIR / "templates"
STYLES_DIR = BASE_DIR / "styles"

CERTIFICATES_DIR = BASE_DIR / "certificates"
GENERATED_DIR = CERTIFICATES_DIR / "generated"

BRANDING_DIR = ASSETS_DIR / "branding"

LOGO_PATH = BRANDING_DIR / "logo.png"
SIGNATURE_PATH = BRANDING_DIR / "signature.png"

SEAL_PATH = ASSETS_DIR / "background" / "gold-seal.svg"
WATERMARK_PATH = ASSETS_DIR / "background" / "watermark-berlin.svg"

ICON_BOOK = ASSETS_DIR / "icons" / "book.svg"
ICON_TARGET = ASSETS_DIR / "icons" / "target.svg"
ICON_AWARD = ASSETS_DIR / "icons" / "award.svg"
ICON_CALENDAR = ASSETS_DIR / "icons" / "calendar.svg"

CSS_PATH = STYLES_DIR / "certificate.css"
TEMPLATE_NAME = "certificate.html"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
)


# =========================================================
# HELPERS
# =========================================================

def _file_uri(path: Path) -> str:
    return path.resolve().as_uri()


def today() -> str:
    return datetime.now().strftime("%d.%m.%Y")


def _name_size_class(full_name: str) -> str:
    length = len(full_name.strip())

    if length <= 18:
        return "size-short"

    if length <= 28:
        return "size-medium"

    if length <= 40:
        return "size-long"

    return "size-xlong"


def _rank_label(rank: str) -> str:
    """Strip the medal emoji prefix stored in the DB (e.g. "🥇 Gold")
    down to the plain word used on the certificate itself."""

    return rank.split(" ")[-1] if rank else "Bronze"


def _accuracy_text(user_id: int) -> str:
    accuracy = get_accuracy(user_id)
    return f"{accuracy}%" if accuracy is not None else "—"


def _inline_svg(path: Path) -> str:
    """
    Raw SVG markup for direct embedding (rather than <img src>),
    so its `stroke="currentColor"` picks up the CSS `color` of
    its wrapper (e.g. gold on a navy circle) - an externally
    referenced image can't inherit page CSS this way.
    """

    return path.read_text(encoding="utf-8")


# =========================================================
# USER / CERTIFICATE DATA
# =========================================================

def get_certificate_user(user_id: int):
    user = get_user(user_id)

    if not user:
        raise ValueError("User topilmadi.")

    return user


def get_certificate_data(
    user_id: int,
    level: str,
    admin_override: bool = False,
):
    status = build_level_status(user_id, level)

    if not status["ready"] and not admin_override:
        raise ValueError("Sertifikat hali tayyor emas.")

    if not status["ready"]:
        # Admin test/preview mode - grade a placeholder certificate
        # from whatever progress exists, so the layout can be
        # reviewed without completing a level for real.
        status = dict(status)
        status["rank"] = calculate_rank(status["average"])

    return status


def get_certificate_id(
    user_id: int,
    level: str,
    average: int,
    grade: str,
):
    certificate = get_level_certificate(user_id, "W", level)

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
# FILE PATH
# =========================================================

def ensure_directories():
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def build_file_name(certificate_id: str):
    return GENERATED_DIR / f"{certificate_id}.pdf"


def get_certificate_file_path(certificate_id: str) -> Path:
    """
    Path to an already-generated certificate's PDF (admin
    browsing / profile retrieval - looks up by certificate_id
    directly, no readiness check, no regeneration).
    """

    return build_file_name(certificate_id)


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

    user = get_certificate_user(user_id)

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

    pdf_path = build_file_name(certificate_id)

    if pdf_path.exists():
        return str(pdf_path)

    config = LEVEL_CONFIG[level]
    vocab_total = config["blocks"] * config["size"]
    vocab_learned = min(sum(status["scores"]), vocab_total)

    html = _jinja_env.get_template(TEMPLATE_NAME).render(
        css_path=_file_uri(CSS_PATH),
        logo_path=_file_uri(LOGO_PATH),
        signature_path=_file_uri(SIGNATURE_PATH),
        seal_path=_file_uri(SEAL_PATH),
        watermark_path=_file_uri(WATERMARK_PATH),
        icon_book_svg=_inline_svg(ICON_BOOK),
        icon_target_svg=_inline_svg(ICON_TARGET),
        icon_award_svg=_inline_svg(ICON_AWARD),
        icon_calendar_svg=_inline_svg(ICON_CALENDAR),
        is_test=admin_override,
        full_name=(user["full_name"] or "").strip().upper(),
        name_size_class=_name_size_class(user["full_name"] or ""),
        level=level,
        vocab_learned=vocab_learned,
        vocab_total=vocab_total,
        accuracy_text=_accuracy_text(user_id),
        rank=_rank_label(status["rank"]),
        completion_date=today(),
        director_name="Zayniddinkhuja Makhmudov",
        certificate_id=certificate_id,
    )

    HTML(
        string=html,
        base_url=str(TEMPLATES_DIR),
    ).write_pdf(str(pdf_path))

    return str(pdf_path)
