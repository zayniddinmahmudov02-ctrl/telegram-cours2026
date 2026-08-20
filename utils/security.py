import hashlib
import secrets

# =========================================================
# PASSWORD HASHING (PBKDF2-HMAC-SHA256)
# =========================================================
# stdlib-only (no new dependency) salted hashing for category
# access passwords (see database.homework). Not for Telegram
# user auth - the bot already trusts Telegram's own identity.

_ITERATIONS = 200_000


def hash_password(password: str) -> tuple[str, str]:
    """Returns (password_hash_hex, salt_hex)."""

    salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        _ITERATIONS,
    )

    return digest.hex(), salt


def verify_password(
    password: str,
    password_hash: str | None,
    salt: str | None,
) -> bool:
    if not password_hash or not salt:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        _ITERATIONS,
    )

    return secrets.compare_digest(digest.hex(), password_hash)
