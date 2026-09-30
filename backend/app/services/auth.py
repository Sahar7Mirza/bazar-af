import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, Conflict, Forbidden, TooManyRequests, Unauthorized
from app.core.security import DUMMY_HASH, create_access_token, hash_password, hash_token, new_refresh_token, verify_password
from app.models import RefreshToken, Role, SellerProfile, SellerStatus, User
from app.schemas.auth import RegisterIn
from app.services import audit

BAD_LOGIN = "Invalid email or password"


def register(db: Session, data: RegisterIn, ip: str | None = None) -> User:
    email = data.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise Conflict("An account with this email already exists", code="email_taken")
    if data.role == "seller" and not data.business_name:
        raise AppError(
            "business_name is required for sellers",
            code="validation_error",
            status_code=422,
            details=[{"field": "business_name", "message": "Required for sellers"}],
        )
    user = User(
        email=email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
        district=data.district,
        role=Role(data.role),
    )
    db.add(user)
    db.flush()
    if user.role == Role.seller:
        db.add(
            SellerProfile(user_id=user.id, business_name=data.business_name, district=data.district, phone=data.phone, status=SellerStatus.pending)
        )
    audit.record(db, "user.register", actor_id=user.id, entity_type="user", entity_id=user.id, detail={"role": user.role.value}, ip=ip)
    db.commit()
    return user


def _issue(db: Session, user: User, family_id: str | None = None) -> tuple[str, str, int]:
    s = get_settings()
    access, ttl = create_access_token(user.id, user.role.value)
    raw, h = new_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            family_id=family_id or str(uuid.uuid4()),
            token_hash=h,
            expires_at=datetime.now(UTC) + timedelta(days=s.refresh_token_days),
        )
    )
    return access, raw, ttl


def login(db: Session, email: str, password: str, ip: str | None = None):
    s = get_settings()
    now = datetime.now(UTC)
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None:
        verify_password(password, DUMMY_HASH)  # equalise timing, no user enumeration
        audit.record(db, "auth.login_failed", detail={"reason": "unknown_email"}, ip=ip)
        db.commit()
        raise Unauthorized(BAD_LOGIN, code="invalid_credentials")
    if user.locked_until and user.locked_until > now:
        audit.record(db, "auth.login_blocked", actor_id=user.id, detail={"reason": "locked"}, ip=ip)
        db.commit()
        raise TooManyRequests("Too many failed attempts. Try again later.", code="account_locked")
    if not verify_password(password, user.password_hash):
        user.failed_logins += 1
        if user.failed_logins >= s.lockout_threshold:
            user.locked_until = now + timedelta(minutes=s.lockout_minutes)
            user.failed_logins = 0
            audit.record(db, "auth.locked", actor_id=user.id, ip=ip)
        audit.record(db, "auth.login_failed", actor_id=user.id, detail={"reason": "bad_password"}, ip=ip)
        db.commit()
        raise Unauthorized(BAD_LOGIN, code="invalid_credentials")
    if not user.is_active:
        audit.record(db, "auth.login_blocked", actor_id=user.id, detail={"reason": "inactive"}, ip=ip)
        db.commit()
        raise Forbidden("This account is deactivated", code="account_disabled")
    user.failed_logins, user.locked_until, user.last_login_at = 0, None, now
    access, raw, ttl = _issue(db, user)
    audit.record(db, "auth.login", actor_id=user.id, ip=ip)
    db.commit()
    return user, access, raw, ttl


def refresh(db: Session, raw: str, ip: str | None = None):
    now = datetime.now(UTC)
    tok = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw)).with_for_update())
    if tok is None or tok.revoked_at or tok.expires_at <= now:
        raise Unauthorized("Invalid refresh token", code="invalid_refresh")
    if tok.used_at:
        # Reuse of an already-rotated token means it may have been stolen: kill the whole family.
        db.execute(update(RefreshToken).where(RefreshToken.family_id == tok.family_id, RefreshToken.revoked_at.is_(None)).values(revoked_at=now))
        audit.record(db, "auth.refresh_reuse", actor_id=tok.user_id, ip=ip)
        db.commit()
        raise Unauthorized("Invalid refresh token", code="invalid_refresh")
    user = db.get(User, tok.user_id)
    if not user or not user.is_active:
        raise Unauthorized("Invalid refresh token", code="invalid_refresh")
    tok.used_at = now
    access, new_raw, ttl = _issue(db, user, family_id=tok.family_id)
    db.commit()
    return user, access, new_raw, ttl


def logout(db: Session, raw: str, actor_id: int | None = None):
    tok = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw)))
    if tok:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == tok.family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        audit.record(db, "auth.logout", actor_id=tok.user_id)
        db.commit()
