from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.deps import client_ip, current_user
from app.db.session import get_db
from app.models import User
from app.schemas.auth import ForgotIn, LoginIn, RefreshIn, RegisterIn, ResetIn, TokenIn, TokenOut, UserOut
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


@router.post("/forgot-password", status_code=202)
def forgot_password(data: ForgotIn, request: Request, db: Session = Depends(get_db)):
    svc.request_password_reset(db, data.email, ip=client_ip(request))
    return {"message": "If an account exists for that email, a reset link is on its way."}


@router.post("/reset-password")
def reset_password(data: ResetIn, request: Request, db: Session = Depends(get_db)):
    svc.reset_password(db, data.token, data.password, ip=client_ip(request))
    return {"message": "Password changed. Please sign in."}


@router.post("/verify-email")
def verify_email(data: TokenIn, db: Session = Depends(get_db)):
    svc.verify_email(db, data.token)
    return {"message": "Email confirmed."}


@router.post("/resend-verification", status_code=202)
def resend_verification(user: User = Depends(current_user), db: Session = Depends(get_db)):
    svc.send_verification(db, user)
    return {"message": "If your email is not confirmed yet, a new link is on its way."}
