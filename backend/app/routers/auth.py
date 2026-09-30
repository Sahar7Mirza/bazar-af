from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.deps import client_ip, current_user
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenOut, UserOut
from app.services import auth as svc

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn, request: Request, db: Session = Depends(get_db)):
    return svc.register(db, data, ip=client_ip(request))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    user, access, raw, ttl = svc.login(db, data.email, data.password, ip=client_ip(request))
    return TokenOut(access_token=access, refresh_token=raw, expires_in=ttl, user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenOut)
def refresh(data: RefreshIn, request: Request, db: Session = Depends(get_db)):
    user, access, raw, ttl = svc.refresh(db, data.refresh_token, ip=client_ip(request))
    return TokenOut(access_token=access, refresh_token=raw, expires_in=ttl, user=UserOut.model_validate(user))


@router.post("/logout", status_code=204)
def logout(data: RefreshIn, db: Session = Depends(get_db)):
    svc.logout(db, data.refresh_token)
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
