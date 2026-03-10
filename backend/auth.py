"""
Clerk JWT doğrulama ve kredi yönetimi.
Krediler Clerk private_metadata.credits alanında saklanır.
"""

import os
import jwt
import httpx
from datetime import datetime, timedelta
from typing import Optional

CLERK_SECRET_KEY: str = os.environ.get("CLERK_SECRET_KEY", "")
CLERK_DOMAIN: str = os.environ.get("CLERK_DOMAIN", "")   # örn: vocal-cobra-12.clerk.accounts.dev
INITIAL_CREDITS: int = 5
CLERK_API = "https://api.clerk.com/v1"

# ——— JWKS in-memory cache ———
_jwks_cache: Optional[dict] = None
_jwks_cache_time: Optional[datetime] = None
_JWKS_TTL = timedelta(minutes=10)


async def _get_jwks() -> dict:
    global _jwks_cache, _jwks_cache_time
    now = datetime.utcnow()
    if _jwks_cache and _jwks_cache_time and (now - _jwks_cache_time) < _JWKS_TTL:
        return _jwks_cache

    if not CLERK_DOMAIN:
        raise ValueError("CLERK_DOMAIN ortam değişkeni ayarlanmamış")

    url = f"https://{CLERK_DOMAIN}/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_cache_time = now
        return _jwks_cache


async def verify_clerk_jwt(token: str) -> str:
    """
    Clerk JWT'yi doğrular ve user_id (sub) döner.
    Hatalıysa ValueError fırlatır.
    """
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        jwks = await _get_jwks()
        key_data = next((k for k in jwks["keys"] if k.get("kid") == kid), None)
        if not key_data:
            raise ValueError(f"JWKS'te kid={kid} anahtarı bulunamadı")

        from jwt.algorithms import RSAAlgorithm
        public_key = RSAAlgorithm.from_jwk(key_data)

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk tokens genelde aud içermez
        )
        user_id: str = payload["sub"]
        return user_id

    except jwt.ExpiredSignatureError:
        raise ValueError("Token süresi dolmuş")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Geçersiz token: {e}")
    except Exception as e:
        raise ValueError(f"Token doğrulama hatası: {e}")


def _clerk_headers() -> dict:
    if not CLERK_SECRET_KEY:
        raise ValueError("CLERK_SECRET_KEY ortam değişkeni ayarlanmamış")
    return {"Authorization": f"Bearer {CLERK_SECRET_KEY}"}


async def get_credits(user_id: str) -> int:
    """
    Clerk private_metadata.credits değerini döner.
    İlk kullanımda INITIAL_CREDITS değerini atar.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{CLERK_API}/users/{user_id}",
            headers=_clerk_headers(),
        )
        resp.raise_for_status()
        user = resp.json()

    credits = user.get("private_metadata", {}).get("credits")
    if credits is None:
        # İlk kez giriş yapan kullanıcı — başlangıç kredisi ver
        await set_credits(user_id, INITIAL_CREDITS)
        return INITIAL_CREDITS

    return int(credits)


async def set_credits(user_id: str, credits: int) -> None:
    """Clerk private_metadata.credits değerini günceller."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.patch(
            f"{CLERK_API}/users/{user_id}/metadata",
            headers={**_clerk_headers(), "Content-Type": "application/json"},
            json={"private_metadata": {"credits": credits}},
        )
        resp.raise_for_status()
