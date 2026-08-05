import asyncio
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

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

WATERMARK_PATH = ASSETS_DIR / "background" / "watermark-berlin.svg"

# One static seal asset per rank tier - the rank word itself is
# already computed by services/certificate.py's calculate_rank();
# this is only a presentation asset lookup, not a scoring rule.
SEAL_PATH_BY_RANK = {
    "Gold": ASSETS_DIR / "background" / "gold-seal.svg",
    "Silver": ASSETS_DIR / "background" / "silver-seal.svg",
    "Bronze": ASSETS_DIR / "background" / "bronze-seal.svg",
}

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


async def _accuracy_text(user_id: int) -> str:
    accuracy = await get_accuracy(user_id)
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

async def get_certificate_user(user_id: int):
    user = await get_user(user_id)

    if not user:
        raise ValueError("User topilmadi.")

    return user


async def get_certificate_data(
    user_id: int,
    level: str,
    admin_override: bool = False,
):
    status = await build_level_status(user_id, level)

    if not status["ready"] and not admin_override:
        raise ValueError("Sertifikat hali tayyor emas.")

    if not status["ready"]:
        # Admin test/preview mode - grade a placeholder certificate
        # from whatever progress exists, so the layout can be
        # reviewed without completing a level for real.
        status = dict(status)
        status["rank"] = calculate_rank(status["average"])

    return status


async def get_certificate_id(
    user_id: int,
    level: str,
    average: int,
    grade: str,
):
    certificate = await get_level_certificate(user_id, "W", level)

    if certificate:
        return certificate["certificate_id"]

    return await create_certificate(
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

async def generate_certificate(
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

    user = await get_certificate_user(user_id)

    status = await get_certificate_data(
        user_id,
        level,
        admin_override=admin_override,
    )

    certificate_id = await get_certificate_id(
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

    rank_label = _rank_label(status["rank"])
    seal_path = SEAL_PATH_BY_RANK.get(rank_label, SEAL_PATH_BY_RANK["Bronze"])

    accuracy_text = await _accuracy_text(user_id)

    # weasyprint pulls in native cairo/pango/gdk-pixbuf libraries -
    # heavy to import (hundreds of ms, several MB of RAM) and only
    # ever needed here, so it's loaded lazily on first certificate
    # request instead of on every bot startup. Python caches the
    # import, so this cost is paid at most once per process.
    from weasyprint import HTML

    html = _jinja_env.get_template(TEMPLATE_NAME).render(
        css_path=_file_uri(CSS_PATH),
        logo_path=_file_uri(LOGO_PATH),
        signature_path=_file_uri(SIGNATURE_PATH),
        seal_path=_file_uri(seal_path),
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
        accuracy_text=accuracy_text,
        rank=rank_label,
        completion_date=today(),
        director_name="Zayniddinkhuja Makhmudov",
        certificate_id=certificate_id,
    )

    # PDF rendering (weasyprint) is CPU/IO-heavy and synchronous -
    # offload it to a worker thread so it never blocks the event
    # loop (and other users' updates) while a certificate renders.
    await asyncio.to_thread(
        lambda: HTML(
            string=html,
            base_url=str(TEMPLATES_DIR),
        ).write_pdf(str(pdf_path))
    )

    return str(pdf_path)
