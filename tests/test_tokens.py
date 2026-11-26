"""Tokens de sesión con PyJWT (HS256): válidos, vencidos, alterados y sin firma."""
from types import SimpleNamespace
import base64
import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

import auth
from config import settings


class _Consulta:
    def __init__(self, usuario):
        self.usuario = usuario

    def filter(self, *_):
        return self

    def first(self):
        return self.usuario


class _Base:
    """Base mínima: devuelve siempre el mismo usuario, sin tocar PostgreSQL."""

    def __init__(self, usuario=SimpleNamespace(role="student", sessions_valid_after=0)):
        self.usuario = usuario

    def query(self, _modelo):
        return _Consulta(self.usuario)


def _usar(token, base=None):
    cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    return auth.get_current_user(credentials=cred, db=base or _Base())


def test_token_emitido_se_acepta():
    token = auth.create_access_token("1b4e28ba-2fa1-11d2-883f-0016d3cca427")
    assert isinstance(token, str)
    assert jwt.decode(token, settings.secret_key, algorithms=["HS256"])["sub"] == "1b4e28ba-2fa1-11d2-883f-0016d3cca427"
    assert _usar(token).role == "student"


def test_token_vencido_se_rechaza():
    vencido = jwt.encode({"sub": "x", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
                         settings.secret_key, algorithm="HS256")
    with pytest.raises(HTTPException) as e:
        _usar(vencido)
    assert e.value.status_code == 401


def test_token_firmado_con_otra_clave_se_rechaza():
    ajeno = jwt.encode({"sub": "x", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
                       "otra-clave-que-no-es-la-del-servicio-0123456789", algorithm="HS256")
    with pytest.raises(HTTPException):
        _usar(ajeno)


def test_token_sin_firma_se_rechaza():
    def b64(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
    sin_firma = b64({"alg": "none", "typ": "JWT"}) + "." + b64({"sub": "x"}) + "."
    with pytest.raises(HTTPException):
        _usar(sin_firma)


def test_token_sin_sub_o_usuario_inexistente_se_rechaza():
    sin_sub = jwt.encode({"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
                         settings.secret_key, algorithm="HS256")
    with pytest.raises(HTTPException):
        _usar(sin_sub)
    with pytest.raises(HTTPException):
        _usar(auth.create_access_token("nadie"), base=_Base(usuario=None))
