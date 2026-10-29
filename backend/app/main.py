import os, time, logging, uuid, threading
from collections import defaultdict, deque
from datetime import timedelta
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query, Request
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, delete, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .db import db_session, User, Field, Scan, Followup, LoginSession, now
from .schemas import Credentials, Registration, Profile, FieldInput, FieldOut, UserOut, ScanOut, FollowupInput, FollowupUpdate, FollowupOut
from .security import current_user, passwords, DUMMY, issue, digest, bearer
from .services.inference import decode_image, predict, MAX_BYTES
from .services.storage import storage
from .services.reports import render_report
from .services.weather import weather_at, search_places
from .services.guidance import guidance, CATALOG
logging.basicConfig(level=logging.INFO,format='%(message)s')
log=logging.getLogger('canopy')
app=FastAPI(title='Canopy Crop Health API',version='1.0.0',docs_url='/api/docs',openapi_url='/api/openapi.json',redoc_url=None)
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5173,http://localhost:8080').split(','),allow_methods=['GET','POST','PATCH','DELETE'],allow_headers=['Authorization','Content-Type'])
buckets=defaultdict(deque)
lock=threading.Lock()

@app.middleware('http')
async def controls(request:Request,call_next):
    started=time.monotonic()
    request_id=uuid.uuid4().hex
    # One-worker local limit. Use WAF/Redis before horizontally scaling.
    key=(request.client.host, 'auth' if '/auth/' in request.url.path else 'api')
    limit=20 if key[1]=='auth' else 180
    with lock:
        queue=buckets[key]
        while queue and queue[0]<started-60: queue.popleft()
        if len(queue)>=limit: return JSONResponse({'detail':'Too many requests'},429,headers={'Retry-After':'60'})
        queue.append(started)
        if len(buckets)>10000:
            for old in list(buckets):
                if buckets[old][-1]<started-60: del buckets[old]
    length=request.headers.get('content-length')
    if length and (not length.isdigit() or int(length)>MAX_BYTES+65536):
        return JSONResponse({'detail':'Upload exceeds 8 MB'},413)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Request-ID']=request_id
    response.headers['Cache-Control']='no-store'
    log.info('{"request_id":"%s","method":"%s","path":"%s","status":%d,"ms":%.1f}',request_id,request.method,request.url.path,response.status_code,(time.monotonic()-started)*1000)
    return response

@app.exception_handler(Exception)
async def unexpected(request,exc):
    log.exception('Unhandled request failure',exc_info=exc)
    return JSONResponse({'detail':'Unexpected server error. Please try again.'},500)

def owned(db,model,id,user):
    item=db.scalar(select(model).where(model.id==id,model.user_id==user.id))
    if not item: raise HTTPException(404,'Record not found')
    return item

@app.get('/api/health')
def health(db:Session=Depends(db_session)):
    db.execute(text('SELECT 1'))
    path=os.getenv('MODEL_PATH','')
    return {'status':'ok','model':'configured' if path and Path(path).is_file() else 'unavailable'}
@app.post('/api/auth/register',status_code=201)
def register(body:Registration,db:Session=Depends(db_session)):
    user=User(email=str(body.email).lower(),name=body.name.strip(),password_hash=passwords.hash(body.password))
    db.add(user)
    try: db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'An account with this email already exists')
    return issue(db,user)
@app.post('/api/auth/login')
def login(body:Credentials,db:Session=Depends(db_session)):
    user=db.scalar(select(User).where(User.email==str(body.email).lower()))
    valid=passwords.verify(body.password,user.password_hash if user else DUMMY)
    if not user or not valid: raise HTTPException(401,'Invalid email or password')
    return issue(db,user)
@app.post('/api/auth/logout',status_code=204)
def logout(user=Depends(current_user),cred=Depends(bearer),db:Session=Depends(db_session)):
    db.execute(delete(LoginSession).where(LoginSession.token_hash==digest(cred.credentials)))
    db.commit()
@app.get('/api/me',response_model=UserOut)
def me(user=Depends(current_user)): return user
@app.patch('/api/me',response_model=UserOut)
def profile(body:Profile,user=Depends(current_user),db:Session=Depends(db_session)):
    user.name=body.name.strip();db.add(user);db.commit();return user
@app.get('/api/fields',response_model=list[FieldOut])
def fields(user=Depends(current_user),db:Session=Depends(db_session)):
    return db.scalars(select(Field).where(Field.user_id==user.id).order_by(Field.id.desc())).all()
@app.post('/api/fields',response_model=FieldOut,status_code=201)
def add_field(body:FieldInput,user=Depends(current_user),db:Session=Depends(db_session)):
    item=Field(**body.model_dump(),user_id=user.id);db.add(item);db.commit();return item
@app.patch('/api/fields/{id}',response_model=FieldOut)
def edit_field(id:int,body:FieldInput,user=Depends(current_user),db:Session=Depends(db_session)):
    item=owned(db,Field,id,user)
    for key,value in body.model_dump().items(): setattr(item,key,value)
    db.commit();return item
@app.delete('/api/fields/{id}',status_code=204)
def remove_field(id:int,user=Depends(current_user),db:Session=Depends(db_session)):
    item=owned(db,Field,id,user)
    for scan in db.scalars(select(Scan).where(Scan.field_id==id)): scan.field_id=None
    db.delete(item);db.commit()
@app.post('/api/scans',response_model=ScanOut,status_code=201)
def analyze(file:UploadFile=File(...),field_id:int|None=Form(None),notes:str=Form('',max_length=2000),user=Depends(current_user),db:Session=Depends(db_session)):
    field=owned(db,Field,field_id,user) if field_id else None
    data=file.file.read(MAX_BYTES+1)
    image=decode_image(data)
    result=predict(image,field.crop if field else None)
    key=storage.save(image)
    try:
        item=Scan(user_id=user.id,field_id=field_id,image_key=key,notes=notes,prediction=result)
        db.add(item);db.commit();return item
    except Exception:
        storage.delete(key);raise
@app.get('/api/scans',response_model=list[ScanOut])
def scans(field_id:int|None=None,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0),user=Depends(current_user),db:Session=Depends(db_session)):
    query=select(Scan).where(Scan.user_id==user.id)
    if field_id: query=query.where(Scan.field_id==field_id)
    return db.scalars(query.order_by(Scan.id.desc()).offset(offset).limit(limit)).all()
@app.get('/api/scans/{id}',response_model=ScanOut)
def scan(id:int,user=Depends(current_user),db:Session=Depends(db_session)):return owned(db,Scan,id,user)
@app.get('/api/scans/{id}/image')
def scan_image(id:int,user=Depends(current_user),db:Session=Depends(db_session)):
    return FileResponse(storage.path(owned(db,Scan,id,user).image_key),media_type='image/jpeg')
@app.get('/api/scans/{id}/report')
def report(id:int,language:str=Query('en',pattern='^(en|hi)$'),user=Depends(current_user),db:Session=Depends(db_session)):
    item=owned(db,Scan,id,user)
    field=db.get(Field,item.field_id) if item.field_id else None
    return Response(render_report(item,field,language),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="canopy-scan-{id}.pdf"'})
@app.get('/api/followups',response_model=list[FollowupOut])
def followups(user=Depends(current_user),db:Session=Depends(db_session)):
    return db.scalars(select(Followup).where(Followup.user_id==user.id).order_by(Followup.due_at)).all()
@app.post('/api/followups',response_model=FollowupOut,status_code=201)
def add_followup(body:FollowupInput,user=Depends(current_user),db:Session=Depends(db_session)):
    owned(db,Scan,body.scan_id,user)
    due=body.due_at or now()+timedelta(days=int(os.getenv('FOLLOWUP_DAYS','7')))
    if due<now():raise HTTPException(422,'Follow-up date must be in the future')
    item=Followup(user_id=user.id,scan_id=body.scan_id,due_at=due);db.add(item);db.commit();return item
@app.patch('/api/followups/{id}',response_model=FollowupOut)
def complete_followup(id:int,body:FollowupUpdate,user=Depends(current_user),db:Session=Depends(db_session)):
    item=owned(db,Followup,id,user);item.done=body.done;db.commit();return item
@app.delete('/api/followups/{id}',status_code=204)
def delete_followup(id:int,user=Depends(current_user),db:Session=Depends(db_session)):
    db.delete(owned(db,Followup,id,user));db.commit()
@app.get('/api/weather')
async def weather(latitude:float=Query(ge=-90,le=90),longitude:float=Query(ge=-180,le=180),user=Depends(current_user)):
    result=await weather_at(latitude,longitude)
    result['context']=guidance(weather=result['current'])['warnings']
    return result
@app.get('/api/diseases')
def diseases(user=Depends(current_user)):return CATALOG
@app.get('/api/risk/{id}')
def risk(id:int,user=Depends(current_user),db:Session=Depends(db_session)):
    return owned(db,Scan,id,user).prediction.get('guidance')
@app.get('/api/experts')
def experts(user=Depends(current_user)):
    email=os.getenv('EXPERT_EMAIL','')
    return {'configured':bool(email),'name':os.getenv('EXPERT_NAME','Agricultural support'),'email':email,
            'note':'Download a report and attach it in your email client. No report is sent automatically.'}

@app.get('/api/locations')
async def locations(q:str=Query(min_length=2,max_length=120),language:str=Query('en',pattern='^(en|hi)$'),user=Depends(current_user)):
    if len(q.strip())<2:raise HTTPException(422,'Enter at least two characters of a place name.')
    return await search_places(q,language)

@app.post('/api/scans/{id}/reanalyze',response_model=ScanOut)
def reanalyze(id:int,user=Depends(current_user),db:Session=Depends(db_session)):
    original=owned(db,Scan,id,user)
    field=db.get(Field,original.field_id) if original.field_id else None
    image=decode_image(storage.path(original.image_key).read_bytes())
    assessment=predict(image,field.crop if field else None)
    if assessment['status']=='model_unavailable':raise HTTPException(503,'No trained checkpoint is installed. Please try again after model setup.')
    # Preserve the original observation and report. Reanalysis becomes a new record.
    key=storage.save(image)
    try:
        item=Scan(user_id=user.id,field_id=original.field_id,image_key=key,notes=original.notes,prediction={**assessment,'reanalysis_of':original.id})
        db.add(item);db.commit();return item
    except Exception:
        storage.delete(key);raise
