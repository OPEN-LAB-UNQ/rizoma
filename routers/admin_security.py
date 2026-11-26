"""Institutional authorization is assigned by an authenticated administrator and audited."""
import time
from uuid import UUID
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
import models
from auth import require_admin
from database import get_db
router=APIRouter(prefix='/api/admin/security',tags=['administracion'])


class Authorization(BaseModel):
    role: Literal['student','teacher','org']
    institution: str=Field(default='',max_length=120)
    evidence: str=Field(min_length=12,max_length=2000)


@router.put('/users/{user_id}/authorization')
def authorize(user_id:UUID,body:Authorization,admin=Depends(require_admin),db:Session=Depends(get_db)):
    target=db.query(models.User).filter(models.User.id==user_id).first()
    if not target:raise HTTPException(404,'Cuenta no encontrada')
    if target.role=='admin':raise HTTPException(403,'Este procedimiento no modifica administradores')
    institution=body.institution.strip()
    if body.role!='student' and not institution:raise HTTPException(422,'La habilitación requiere institución')
    before={'role':target.role,'institution':target.institution,'verified':target.institution_verified}
    changed=target.role!=body.role or target.institution!=institution
    target.role=body.role;target.institution=institution;target.institution_verified=body.role!='student'
    target.sessions_valid_after=time.time()
    if changed:
        db.query(models.Credential).filter(models.Credential.verified_by==target.id).update({'verified':False})
    db.add(models.SecurityAudit(actor_id=admin.id,subject_id=target.id,action='institutional_authorization',
        details={'before':before,'role':body.role,'institution':institution,'evidence':body.evidence}))
    db.commit()
    return {'id':str(target.id),'role':target.role,'institution':target.institution,'institution_verified':target.institution_verified}


@router.post('/users/{user_id}/revoke-sessions')
def revoke(user_id:UUID,admin=Depends(require_admin),db:Session=Depends(get_db)):
    target=db.query(models.User).filter(models.User.id==user_id).first()
    if not target:raise HTTPException(404,'Cuenta no encontrada')
    target.sessions_valid_after=time.time()
    db.add(models.SecurityAudit(actor_id=admin.id,subject_id=target.id,action='revoke_sessions',details={}))
    db.commit();return {'ok':True}
