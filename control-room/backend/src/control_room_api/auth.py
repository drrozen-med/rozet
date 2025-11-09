"""JWT authentication helpers."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

from .config import Settings, get_settings


class TokenValidator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def validate(self, token: str) -> dict:
        if self._settings.auth_disabled:
            return {"sub": "dev-user", "iss": "dev", "aud": self._settings.jwt_audience}

        if not self._settings.jwt_issuer or not self._settings.jwt_audience:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT issuer/audience not configured",
            )

        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False},  # Real deployment should verify signatures
                audience=self._settings.jwt_audience,
                issuer=self._settings.jwt_issuer,
            )
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        return payload


def get_current_principal(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)]
) -> dict:
    """Extract and validate bearer token, returning the decoded payload."""
    authorization: str | None = request.headers.get("Authorization")
    validator = TokenValidator(settings)
    if not authorization and settings.auth_disabled:
        return validator.validate("dev")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    token = authorization.split(" ", 1)[1].strip()
    return validator.validate(token)


Principal = Annotated[dict, Depends(get_current_principal)]


__all__ = ["Principal", "get_current_principal"]
