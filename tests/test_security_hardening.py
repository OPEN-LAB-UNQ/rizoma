import io,time,uuid,zipfile
from types import SimpleNamespace
import pytest,jwt
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
import main,models,auth
from database import Base,get_db
from config import Settings,settings
from services import auth_limits,privacy_notice
from routers.projects import _can_review_project
from routers.copilot import _extract_docx,MAX_DOCX_XML_BYTES

@pytest.fixture
def env(tmp_path):
    assert 'rizoma_security_test_' in settings.database_url
    engine=create_engine(settings.database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine)
    def db():
        with Session() as s:yield s
    main.app.dependency_overrides[get_db]=db
    with Session() as s:privacy_notice.asegurar_publicacion(s)
    client=TestClient(main.app,base_url='https://testserver',headers={'origin':'https://testserver'})
    yield client,Session
    client.close();main.app.dependency_overrides.clear();engine.dispose()

def register(client,email='security@example.com',role='teacher'):
    return client.post('/auth/register',json={'name':'Security Test','email':email,'password':'Secure-testing-1234','role':role,'institution':'Example','aviso_version':privacy_notice.NOTICE_VERSION})

def login(client,email='security@example.com'):
    return client.post('/auth/login',json={'email':email,'password':'Secure-testing-1234'})

def test_registration_cookie_logout_and_csrf(env):
    client,Session=env
    a=register(client);b=register(client)
    assert a.status_code==b.status_code==202 and a.json()==b.json()
    assert 'access_token' not in a.json()
    with Session() as db:
        u=db.query(models.User).one();assert u.role=='student' and not u.institution_verified
    r=login(client);assert r.status_code==200,r.text
    cookie=r.headers['set-cookie'];assert 'HttpOnly' in cookie and 'Secure' in cookie and 'SameSite=lax' in cookie
    old=client.cookies.get(auth.COOKIE_NAME)
    assert client.get('/api/users/me').status_code==200
    assert client.post('/api/projects',json={'title':'Example project','description':'Example project description'}).status_code==403
    assert client.post('/auth/logout',headers={'origin':'https://evil.invalid'}).status_code==403
    assert client.get('/api/users/me').status_code==200
    assert client.post('/auth/logout').status_code==200
    assert client.get('/api/users/me',headers={'authorization':'Bearer '+old}).status_code==401
    assert login(client).status_code==200
    assert client.get('/api/users/me').status_code==200
    assert 'script-src' in client.get('/').headers['content-security-policy']

def test_shared_rate_limit(env):
    _,Session=env
    for i in range(10):
        with Session() as db:auth_limits.consume(db,'shared-test',10)
    with Session() as db,pytest.raises(HTTPException) as e:auth_limits.consume(db,'shared-test',10)
    assert e.value.status_code==429

def test_approval_and_institution_lock(env):
    client,Session=env;register(client);login(client)
    with Session() as db:
        target=db.query(models.User).one();target_id=str(target.id)
        admin=models.User(email='admin',name='Admin',role='admin',password_hash=auth.hash_password('Admin-testing-1234'))
        db.add(admin);db.commit();token=auth.create_access_token(str(admin.id))
    url='/api/admin/security/users/'+target_id+'/authorization'
    body={'role':'teacher','institution':'Approved','evidence':'Approval documented by administrator'}
    assert client.put(url,json=body).status_code==403
    assert client.put(url,json=body,headers={'authorization':'Bearer '+token}).status_code==200
    assert client.get('/api/users/me').status_code==401
    assert login(client).status_code==200
    assert client.put('/api/users/me',json={'institution':'Forged'}).status_code==403
    r=client.post('/api/projects',json={'title':'Real project','description':'Example project description','institution':'Forged'})
    assert r.status_code==200,r.text
    assert r.json()['institution']=='Approved'
    with Session() as db:assert db.query(models.SecurityAudit).count()==1

def test_project_creator_cannot_impersonate_institution():
    uid=uuid.uuid4();project=SimpleNamespace(created_by=uid,institution='Other')
    user=SimpleNamespace(id=uid,role='student',institution='Other',institution_verified=False)
    assert not _can_review_project(project,user)
    user.role='teacher';user.institution_verified=True;user.institution='Approved'
    assert not _can_review_project(project,user)
    project.institution='Approved';assert _can_review_project(project,user)

def docx(xml):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('word/document.xml',xml)
    return b.getvalue()

def test_docx_limits_and_valid_document():
    assert _extract_docx(docx('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:t>Example</w:t></w:p></w:document>'))=='Example'
    for data,status in [(docx('x'*(MAX_DOCX_XML_BYTES+1)),413),(docx('<!DOCTYPE x [<!ENTITY a "x">]><x/>'),400),(b'not a zip',400)]:
        with pytest.raises(HTTPException) as e:_extract_docx(data)
        assert e.value.status_code==status

def test_settings_refuse_weak_secret_and_long_session():
    for kw in [{'secret_key':'short'},{'access_token_expire_minutes':10080}]:
        with pytest.raises(ValueError):Settings(_env_file=None,database_url='sqlite:///test',**kw)

def test_old_long_and_revoked_tokens(env):
    client,Session=env;register(client)
    with Session() as db:
        user=db.query(models.User).one();uid=str(user.id)
        for payload in [{'sub':uid,'exp':time.time()+1000},{'sub':uid,'iat':time.time(),'exp':time.time()+604800}]:
            token=jwt.encode(payload,settings.secret_key,algorithm='HS256')
            assert client.get('/api/users/me',headers={'authorization':'Bearer '+token}).status_code==401


def test_verified_credential_workflow(env):
    client,Session=env;register(client);login(client)
    with Session() as db:
        student=db.query(models.User).one()
        reviewer=models.User(email='reviewer@example.com',name='Reviewer',role='teacher',institution='Approved',institution_verified=True,password_hash='disabled')
        db.add(reviewer);db.flush()
        project=models.Project(title='Reviewed project',description='Reviewed real participation',institution='Approved',created_by=reviewer.id)
        db.add(project);db.flush()
        application=models.ProjectApplication(user_id=student.id,project_id=project.id,status='pending')
        db.add(application);db.commit();aid=str(application.id);token=auth.create_access_token(str(reviewer.id));reviewer_id=reviewer.id
        legacy=models.Credential(user_id=student.id,title='Legacy untraceable',type='extension',verified=True)
        db.add(legacy);db.commit();legacy_id=str(legacy.id)
    assert client.get('/api/credentials/public/'+legacy_id).status_code==404
    url='/api/projects/applications/'+aid+'/accept'
    body={'hours':12,'evidence_note':'Participation reviewed with supporting evidence'}
    assert client.post(url,json=body).status_code==403
    response=client.post(url,json=body,headers={'authorization':'Bearer '+token})
    assert response.status_code==200,response.text
    cid=response.json()['credential']['id']
    assert client.get('/api/credentials/public/'+cid).status_code==200
    with Session() as db:
        c=db.query(models.Credential).filter(models.Credential.id==uuid.UUID(cid)).one()
        assert c.verified_by==reviewer_id and c.verified and c.project_id

def test_login_limits_and_wrong_password(env):
    client,_=env
    for i in range(10):
        assert client.post('/auth/login',json={'email':'absent@example.com','password':'not-valid'}).status_code==401
    r=client.post('/auth/login',json={'email':'absent@example.com','password':'not-valid'})
    assert r.status_code==429 and 'retry-after' in r.headers
