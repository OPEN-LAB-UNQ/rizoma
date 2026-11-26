from datetime import datetime, timedelta, timezone
from typing import Optional
import time
import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from config import settings
from database import get_db
import models

COOKIE_NAME = '__Host-rizoma_session'
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_access_token(user_id: str) -> str:
    issued = time.time()
    return jwt.encode({'sub':user_id,'iat':issued,'exp':issued+settings.access_token_expire_minutes*60},
                      settings.secret_key,algorithm='HS256')


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
                     db: Session = Depends(get_db), request: Request = None) -> models.User:
    token = credentials.credentials if credentials else (request.cookies.get(COOKIE_NAME) if request else None)
    if not token:
        raise HTTPException(401,'No autenticado')
    try:
        payload=jwt.decode(token,settings.secret_key,algorithms=['HS256'],options={'require':['sub','iat','exp']})
        issued=float(payload['iat']);expires=float(payload['exp'])
        if not payload['sub'] or expires-issued>43200 or time.time()-issued>=43200 or expires<=issued:
            raise ValueError()
        from uuid import UUID
        user_id=UUID(payload['sub'])
    except (jwt.PyJWTError,ValueError,TypeError):
        raise HTTPException(401,'Sesión inválida o vencida')
    user=db.query(models.User).filter(models.User.id==user_id).first()
    if not user or issued < float(getattr(user,'sessions_valid_after',0) or 0):
        raise HTTPException(401,'Sesión inválida o vencida')
    if user.role in ('teacher','org') and not user.institution_verified:
        raise HTTPException(403,'La habilitación institucional requiere revisión administrativa')
    return user


def institutional_user(user):
    return user.role=='admin' or (user.role in ('teacher','org') and bool(user.institution_verified) and bool(user.institution.strip()))


def require_admin(user: models.User = Depends(get_current_user)):
    if user.role!='admin':raise HTTPException(403,'Solo administración')
    return user
