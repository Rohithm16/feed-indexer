"""Cookie-based authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.user_prefs import UserPreferences
from app.schemas.auth import AuthCredentials, UserOut
from app.security import (
    create_session_token,
    hash_password,
    is_valid_email,
    normalize_email,
    verify_password,
    verify_session_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _cookie_security() -> bool:
    return settings.cookie_secure or settings.is_production


def _set_auth_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        create_session_token(user_id),
        max_age=settings.session_max_age_seconds,
        httponly=True,
        secure=_cookie_security(),
        samesite=settings.cookie_samesite,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")


def _get_user_from_token(db: Session, token: str | None) -> User | None:
    session = verify_session_token(token)
    if not session:
        return None
    return db.query(User).filter(User.id == session.user_id).first()


def get_current_user_optional(
    db: Session = Depends(get_db),
    session_cookie: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> User | None:
    return _get_user_from_token(db, session_cookie)


def get_current_user(user: User | None = Depends(get_current_user_optional)) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def _ensure_preferences(db: Session, user: User) -> UserPreferences:
    if user.preferences:
        return user.preferences
    prefs = UserPreferences(
        user_id=user.id,
        preferred_topics=[],
        trusted_publishers=[],
        country="us",
        city=None,
    )
    db.add(prefs)
    db.flush()
    db.refresh(user)
    return prefs


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(credentials: AuthCredentials, response: Response, db: Session = Depends(get_db)):
    email = normalize_email(credentials.email)
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Enter a valid email address")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email is already registered")

    user = User(email=email, password_hash=hash_password(credentials.password))
    db.add(user)
    db.flush()
    _ensure_preferences(db, user)
    db.commit()
    db.refresh(user)
    _set_auth_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserOut)
def login(credentials: AuthCredentials, response: Response, db: Session = Depends(get_db)):
    email = normalize_email(credentials.email)
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    _ensure_preferences(db, user)
    db.commit()
    _set_auth_cookie(response, user.id)
    return user


@router.post("/logout")
def logout(response: Response):
    _clear_auth_cookie(response)
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
