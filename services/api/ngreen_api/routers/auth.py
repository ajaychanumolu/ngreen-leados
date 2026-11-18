from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ngreen_api.db import get_db
from ngreen_api.deps import ApiError
from ngreen_api.models import User
from ngreen_api.security import issue_demo_token, login_is_limited, verify_password
from ngreen_api.settings import get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    auth_mode: str = "demo"


@router.post("/demo/login", response_model=LoginResponse)
def demo_login(body: LoginBody, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    settings = get_settings()
    if not settings.demo_auth_enabled:
        raise ApiError(403, "demo_disabled", "Demo sign-in is disabled.")
    client = request.client.host if request.client else "unknown"
    if login_is_limited(f"{client}:{body.email.strip().lower()}"):
        raise ApiError(429, "rate_limited", "Too many sign-in attempts. Wait a minute.")
    email = body.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise ApiError(401, "invalid_credentials", "Email or password is wrong.")
    return LoginResponse(access_token=issue_demo_token(user.id), auth_mode="demo")
