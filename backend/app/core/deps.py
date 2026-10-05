import ipaddress

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.errors import Forbidden, Unauthorized
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Role, User

bearer = HTTPBearer(auto_error=False)


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if creds is None:
        raise Unauthorized("Authentication required")
    try:
        data = decode_access_token(creds.credentials)
    except InvalidTokenError:
        raise Unauthorized("Invalid or expired token", code="invalid_token") from None
    user = db.get(User, int(data["sub"]))
    if user is None or not user.is_active:
        raise Unauthorized("Invalid or expired token", code="invalid_token")
    return user


def require_roles(*roles: Role):
    """RBAC step 1: is this role allowed on the route? (Step 2 - ownership - lives in the services.)"""
    allowed = set(roles)

    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in allowed:
            raise Forbidden("You do not have permission to do this")
        return user

    return dep


def client_ip(request: Request) -> str | None:
    host = request.client.host if request.client else None
    try:
        return str(ipaddress.ip_address(host)) if host else None
    except ValueError:  # e.g. unix sockets or the test client; the audit column only accepts real IPs
        return None


def optional_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User | None:
    """Like current_user but returns None for anonymous visitors (or an invalid token) instead of failing."""
    if creds is None:
        return None
    try:
        return current_user(creds, db)
    except Unauthorized:
        return None
