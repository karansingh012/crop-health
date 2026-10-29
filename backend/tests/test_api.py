import io, os
from datetime import timedelta
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db import Base, db_session, now
from backend.app.main import app, buckets
from backend.app.services.storage import storage

@pytest.fixture
def client(tmp_path,monkeypatch):
    engine=create_engine('sqlite:///'+str(tmp_path/'test.db'),connect_args={'check_same_thread':False})
    Base.metadata.create_all(engine);factory=sessionmaker(engine,expire_on_commit=False)
    def session():
        with factory() as s:yield s
    app.dependency_overrides[db_session]=session
    monkeypatch.setattr(storage,'root',tmp_path)
    monkeypatch.setenv('MODEL_PATH','');buckets.clear()
    with TestClient(app) as c:yield c
    app.dependency_overrides.clear();engine.dispose()
def account(client,email='one@example.com'):
    r=client.post('/api/auth/register',json={'name':'Test Farmer','email':email,'password':'secure-password-123'})
    assert r.status_code==201,r.text
    return {'Authorization':'Bearer '+r.json()['access_token']}
def image_bytes():
    b=io.BytesIO();Image.new('RGB',(160,160),(80,120,40)).save(b,format='PNG');return b.getvalue()
def scan(client,headers,field=None):
    return client.post('/api/scans',headers=headers,files={'file':('leaf.png',image_bytes(),'image/png')},data={'notes':'Yellow spots observed',**({'field_id':field} if field else {})})
def test_auth_validation_and_revocation(client):
    assert client.get('/api/me').status_code==401
    assert client.post('/api/auth/register',json={'name':'x','email':'bad','password':'short'}).status_code==422
    h=account(client)
    assert client.post('/api/auth/register',json={'name':'Duplicate','email':'one@example.com','password':'secure-password-123'}).status_code==409
    assert client.post('/api/auth/login',json={'email':'one@example.com','password':'wrong-password-123'}).status_code==401
    assert client.get('/api/me',headers=h).json()['name']=='Test Farmer'
    assert client.patch('/api/me',headers=h,json={'name':'Updated'}).json()['name']=='Updated'
    assert client.post('/api/auth/logout',headers=h).status_code==204
    assert client.get('/api/me',headers=h).status_code==401
    assert client.post('/api/auth/login',json={'email':'one@example.com','password':'secure-password-123'}).status_code==200

def test_complete_observation_workflow_and_isolation(client):
    h=account(client);other=account(client,'two@example.com')
    f=client.post('/api/fields',headers=h,json={'name':'North plot','crop':'Tomato','area':1.5,'location':'Farm'}).json()
    assert client.get('/api/fields',headers=other).json()==[]
    assert client.patch(f"/api/fields/{f['id']}",headers=other,json={'name':'attack','crop':'x','area':1}).status_code==404
    assert client.patch(f"/api/fields/{f['id']}",headers=h,json={'name':'North','crop':'Tomato','area':2}).status_code==200
    r=scan(client,h,f['id']);assert r.status_code==201,r.text;s=r.json();sid=s['id']
    assert s['prediction']['status']=='model_unavailable' and s['prediction']['score'] is None
    assert client.get('/api/scans',headers=other).json()==[]
    for suffix in ('','/image','/report'):
        assert client.get(f'/api/scans/{sid}{suffix}',headers=other).status_code==404
        assert client.get(f'/api/scans/{sid}{suffix}',headers=h).status_code==200
    report=client.get(f'/api/scans/{sid}/report',headers=h)
    assert report.content.startswith(b'%PDF')
    assert scan(client,other,f['id']).status_code==404
    follow=client.post('/api/followups',headers=h,json={'scan_id':sid});assert follow.status_code==201
    fid=follow.json()['id']
    assert client.post('/api/followups',headers=other,json={'scan_id':sid}).status_code==404
    assert client.patch(f'/api/followups/{fid}',headers=other,json={'done':True}).status_code==404
    assert client.patch(f'/api/followups/{fid}',headers=h,json={'done':True}).json()['done']
    assert client.delete(f'/api/followups/{fid}',headers=h).status_code==204
    assert client.delete(f"/api/fields/{f['id']}",headers=h).status_code==204
    assert client.get(f'/api/scans/{sid}',headers=h).json()['field_id'] is None

def test_image_validation(client):
    h=account(client)
    assert client.post('/api/scans',headers=h,files={'file':('x.jpg',b'not an image','image/jpeg')}).status_code==422
    assert client.post('/api/scans',headers=h,files={'file':('big.jpg',b'x'*(8*1024*1024+1),'image/jpeg')}).status_code==413
    b=io.BytesIO();Image.new('RGB',(10,10)).save(b,format='PNG')
    assert client.post('/api/scans',headers=h,files={'file':('small.png',b.getvalue(),'image/png')}).status_code==422

def test_weather_disabled_and_provider_failure(client,monkeypatch):
    h=account(client)
    monkeypatch.setenv('WEATHER_ENABLED','false')
    assert client.get('/api/weather?latitude=20&longitude=70',headers=h).status_code==503
    assert client.get('/api/weather?latitude=100&longitude=70',headers=h).status_code==422
    monkeypatch.setenv('WEATHER_ENABLED','true')
    import httpx
    async def failed(*args,**kwargs):raise httpx.ConnectError('offline')
    monkeypatch.setattr(httpx.AsyncClient,'get',failed)
    assert client.get('/api/weather?latitude=20&longitude=70',headers=h).status_code==502

def test_bad_model_and_dates(client,monkeypatch,tmp_path):
    h=account(client);s=scan(client,h).json()
    assert client.post('/api/followups',headers=h,json={'scan_id':s['id'],'due_at':(now()-timedelta(days=1)).isoformat()}).status_code==422
    assert client.post('/api/followups',headers=h,json={'scan_id':s['id'],'due_at':'2027-01-01T12:00:00'}).status_code==422
    assert client.post('/api/fields',headers=h,json={'name':'bad','crop':'Tomato','area':-1}).status_code==422
    assert client.get('/api/experts',headers=h).json()['configured']==False

def test_login_rate_limit(client):
    for _ in range(20):client.post('/api/auth/login',json={'email':'invalid','password':'short'})
    assert client.post('/api/auth/login',json={'email':'invalid','password':'short'}).status_code==429

def test_corrupt_checkpoint_is_configuration_error(client,monkeypatch,tmp_path):
    from backend.app.services.inference import load_model
    h=account(client)
    path=tmp_path/'broken.pt';path.write_bytes(b'invalid checkpoint')
    monkeypatch.setenv('MODEL_PATH',str(path));load_model.cache_clear()
    assert scan(client,h).status_code==503
    assert client.get('/api/scans',headers=h).json()==[]
    load_model.cache_clear()

def test_weather_success_preserves_units_and_source(client,monkeypatch):
    import httpx
    h=account(client);monkeypatch.setenv('WEATHER_ENABLED','true')
    async def response(*args,**kwargs):
        return httpx.Response(200,json={'current':{'time':'2026-10-29T00:00','temperature_2m':25,'relative_humidity_2m':90,'precipitation':2},'current_units':{'temperature_2m':'°C','relative_humidity_2m':'%','precipitation':'mm'}},request=httpx.Request('GET','https://api.open-meteo.com/v1/forecast'))
    monkeypatch.setattr(httpx.AsyncClient,'get',response)
    result=client.get('/api/weather?latitude=20&longitude=70',headers=h)
    assert result.status_code==200
    assert result.json()['units']['relative_humidity_2m']=='%'
    assert result.json()['source']=='Open-Meteo'
    assert any('High humidity' in line for line in result.json()['context'])

def test_place_search_and_validation(client,monkeypatch):
    import httpx
    h=account(client)
    async def response(*args,**kwargs):
        assert kwargs['params']['language']=='hi'
        return httpx.Response(200,json={'results':[{'id':1264733,'name':'लखनऊ','admin1':'उत्तर प्रदेश','country':'भारत','latitude':26.84,'longitude':80.94}]},request=httpx.Request('GET','https://geocoding-api.open-meteo.com/v1/search'))
    monkeypatch.setattr(httpx.AsyncClient,'get',response)
    r=client.get('/api/locations?q=Lucknow&language=hi',headers=h)
    assert r.status_code==200 and r.json()[0]['name']=='लखनऊ'
    assert client.get('/api/locations?q=a',headers=h).status_code==422
    assert client.get('/api/locations?q=Delhi&language=xx',headers=h).status_code==422
    assert client.get('/api/locations?q=Delhi').status_code==401

def test_place_search_empty_and_failure(client,monkeypatch):
    import httpx
    h=account(client)
    async def empty(*args,**kwargs):return httpx.Response(200,json={},request=httpx.Request('GET','https://geocoding-api.open-meteo.com/v1/search'))
    monkeypatch.setattr(httpx.AsyncClient,'get',empty)
    assert client.get('/api/locations?q=nowhere',headers=h).json()==[]
    async def failed(*args,**kwargs):raise httpx.ConnectError('offline')
    monkeypatch.setattr(httpx.AsyncClient,'get',failed)
    assert client.get('/api/locations?q=Delhi',headers=h).status_code==502

def test_reanalysis_ownership_and_missing_model(client):
    h=account(client);other=account(client,'other@example.com');s=scan(client,h).json()
    assert client.post(f"/api/scans/{s['id']}/reanalyze",headers=other).status_code==404
    assert client.post(f"/api/scans/{s['id']}/reanalyze",headers=h).status_code==503
    assert len(client.get('/api/scans',headers=h).json())==1
    r=client.get(f"/api/scans/{s['id']}/report?language=hi",headers=h)
    assert r.status_code==200 and r.content.startswith(b'%PDF')
