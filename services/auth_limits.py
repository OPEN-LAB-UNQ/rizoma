"""Atomic, shared login/register limits across workers; no cleartext email or IP stored."""
import hashlib,hmac,time
from fastapi import HTTPException
from sqlalchemy import text
from config import settings


def consume(db,key,maximum,window=900):
    now=time.time()
    bucket=hmac.new(settings.secret_key.encode(),key.encode(),hashlib.sha256).hexdigest()
    row=db.execute(text('''INSERT INTO auth_limits (bucket,hits,expires_at) VALUES (:bucket,1,:expiry)
        ON CONFLICT(bucket) DO UPDATE SET
        hits=CASE WHEN auth_limits.expires_at<=:now THEN 1 ELSE auth_limits.hits+1 END,
        expires_at=CASE WHEN auth_limits.expires_at<=:now THEN :expiry ELSE auth_limits.expires_at END
        RETURNING hits,expires_at'''),dict(bucket=bucket,expiry=now+window,now=now)).one()
    # A bounded-time retention; counts survive application restarts.
    db.execute(text('DELETE FROM auth_limits WHERE expires_at < :old'),{'old':now-900})
    db.commit()
    if row[0]>maximum:
        raise HTTPException(429,'Demasiados intentos. Esperá antes de volver a intentar.',headers={'Retry-After':str(max(1,int(row[1]-now)+1))})


def consume_auth(db,request,email,action):
    consume(db,action+':ip:'+request.client.host,30)
    consume(db,action+':account:'+email,10)


def limit_cv(user,db):consume(db,'cv:'+str(user.id),10,3600)
