"""Password hashing and JWT checks.

Demo tokens are HS256 and labeled with issuer ngreen-leados-demo.
Supabase tokens are verified against the project JWKS when SUPABASE_URL is set.
The JWT role claim is never used as the application role.
"""

from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from dataclasses import dataclass

import jwt
from jwt import PyJWKClient

from ngreen_api.settings import get_settings

DEMO_ISSUER = "ngreen-leados-demo"
_TOKEN_TTL_SECONDS = 60 * 60 * 12
_jwks_client: PyJWKClient | None = None
_login_hits: dict[str, list[float]] = {}


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or hashlib.sha256(uuid.uuid4().bytes).digest()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$", 1)
    candidate = hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, f"{salt_hex}${digest_hex}")


def issue_demo_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "iss": DEMO_ISSUER,
        "iat": now,
        "exp": now + _TOKEN_TTL_SECONDS,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


@dataclass(frozen=True)
class VerifiedToken:
    user_id: uuid.UUID
    issuer: str


def login_is_limited(key: str, *, limit: int = 10, window_seconds: float = 60) -> bool:
    now = time.monotonic()
    recent = [stamp for stamp in _login_hits.get(key, []) if now - stamp < window_seconds]
    if len(recent) >= limit:
        _login_hits[key] = recent
        return True
    recent.append(now)
    _login_hits[key] = recent
    return False


def reset_login_limits() -> None:
    _login_hits.clear()


def verify_access_token(token: str) -> VerifiedToken:
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(token)
        claims = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError as exc:
        raise PermissionError("Sign in required.") from exc
    issuer = str(claims.get("iss") or "")
    if issuer == DEMO_ISSUER:
        if not settings.demo_auth_enabled:
            raise PermissionError("Demo sign-in is disabled.")
        if header.get("alg") != "HS256":
            raise PermissionError("Sign in required.")
        verified = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=DEMO_ISSUER,
        )
        return VerifiedToken(user_id=uuid.UUID(str(verified["sub"])), issuer=issuer)
    if settings.supabase_url and issuer.startswith(settings.supabase_url):
        verified = _verify_supabase(token)
        return VerifiedToken(user_id=uuid.UUID(str(verified["sub"])), issuer=issuer)
    raise PermissionError("Sign in required.")


def _verify_supabase(token: str) -> dict[str, object]:
    global _jwks_client
    settings = get_settings()
    if _jwks_client is None:
        jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256", "ES256"],
        audience="authenticated",
        issuer=f"{settings.supabase_url}/auth/v1",
    )
