import hashlib
import time
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import models,schemas
from auth import hash_password,verify_password,create_access_token,get_current_user,COOKIE_NAME,bearer_scheme
from database import get_db
from routers.users import _completeness
from services import privacy_notice
from services.auth_limits import consume_auth
router=APIRouter(prefix='/auth',tags=['auth'])
MESSAGE='Si los datos permiten crear la cuenta, ya podés ingresar. Si ya tenías una cuenta, usá tu contraseña habitual.'
# Constant valid hash: missing accounts still pay the password-verification cost.
DUMMY_HASH=hash_password('synthetic-non-account-password')


@router.post('/register',status_code=202)
def register(body: schemas.RegisterRequest, request: Request, db: Session=Depends(get_db)):
    email=body.email.lower().strip()
    consume_auth(db,request,email,'register')
    hashed=hash_password(body.password)
    if db.query(models.User).filter(models.User.email==email).first():return {'message':MESSAGE}
    user=models.User(email=email,password_hash=hashed,name=body.name,role='student',institution=body.institution,
                     institution_verified=False,sessions_valid_after=0)
    db.add(user)
    try:db.commit()
    except IntegrityError:
        db.rollback();return {'message':MESSAGE}
    db.refresh(user);user.profile_completeness=_completeness(user,db);db.commit()
    if body.aviso_version==privacy_notice.NOTICE_VERSION:privacy_notice.registrar_lectura(db,user.id,body.aviso_version)
    return {'message':MESSAGE}


@router.post('/login')
def login(body: schemas.LoginRequest, request: Request, response: Response, db: Session=Depends(get_db)):
    email=body.email.lower().strip()
    consume_auth(db,request,email,'login')
    user=db.query(models.User).filter(models.User.email==email).first()
    valid=verify_password(body.password,user.password_hash if user else DUMMY_HASH)
    if not user or not valid:raise HTTPException(401,'Email o contraseña incorrectos')
    token=create_access_token(str(user.id))
    from config import settings
    response.set_cookie(COOKIE_NAME,token,max_age=settings.access_token_expire_minutes*60,
                        secure=True,httponly=True,samesite='lax',path='/')
    return {'authenticated':True}


@router.post('/logout')
def logout(response: Response, request: Request, db: Session=Depends(get_db), credentials=Depends(bearer_scheme)):
    try:user=get_current_user(credentials=credentials,db=db,request=request)
    except HTTPException:user=None
    if user:
        user.sessions_valid_after=time.time();db.commit()
    response.delete_cookie(COOKIE_NAME,path='/',secure=True,httponly=True,samesite='lax')
    return {'ok':True}
