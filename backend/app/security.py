import hashlib, secrets
from datetime import timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from .db import db_session, User, LoginSession, now
passwords=PasswordHash.recommended()
bearer=HTTPBearer(auto_error=False)
# A dummy hash keeps unknown-account login on the same expensive verification path.
DUMMY=passwords.hash(secrets.token_urlsafe(32))
def digest(token): return hashlib.sha256(token.encode()).hexdigest()
def current_user(cred:HTTPAuthorizationCredentials=Depends(bearer), db:Session=Depends(db_session)):
    session=db.get(LoginSession,digest(cred.credentials)) if cred else None
    if not session or session.expires_at.replace(tzinfo=timezone.utc)<now():
        raise HTTPException(401,'Please sign in again')
    return db.get(User,session.user_id)
def issue(db,user):
    token=secrets.token_urlsafe(48)
    db.add(LoginSession(token_hash=digest(token),user_id=user.id,expires_at=now()+timedelta(hours=12)))
    db.commit()
    return {'access_token':token,'token_type':'bearer','expires_in':43200}
