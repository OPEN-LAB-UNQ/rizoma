"""CSP restricts scripts/resources; cookie writes require a trusted same-site origin."""
import re,hashlib,base64
from pathlib import Path
from functools import lru_cache
from fastapi.responses import JSONResponse
from config import settings
from auth import COOKIE_NAME

def check_origin(request):
    if request.method in ('GET','HEAD','OPTIONS'):return None
    origin=request.headers.get('origin')
    if (origin and origin not in settings.cors_origins) or (COOKIE_NAME in request.cookies and not origin):
        return JSONResponse({'detail':'Origen de la solicitud no permitido'},status_code=403)
    return None

@lru_cache(maxsize=1)
def content_policy():
    hashes=set()
    for p in (Path(__file__).resolve().parents[1]/'static').rglob('*.html'):
        for code in re.findall(r'<script\b[^>]*>(.*?)</script>',p.read_text(),re.S|re.I):
            if code.strip():hashes.add("'sha256-"+base64.b64encode(hashlib.sha256(code.encode()).digest()).decode()+"'")
    return ("default-src 'self'; script-src 'self' "+' '.join(sorted(hashes))+"; "
            "script-src-attr 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https://images.unsplash.com; font-src 'self'; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")
