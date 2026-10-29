from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, AwareDatetime
class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
class Registration(Credentials):
    name: str = Field(min_length=1, max_length=100)
class Profile(BaseModel):
    name: str = Field(min_length=1, max_length=100)
class FieldInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    crop: str = Field(min_length=1, max_length=100)
    area: float = Field(gt=0, le=1e7, allow_inf_nan=False)
    location: str = Field(default='', max_length=200)
class FollowupInput(BaseModel):
    scan_id: int
    due_at: AwareDatetime | None = None
class FollowupUpdate(BaseModel):
    done: bool
class ORM(BaseModel):
    model_config=ConfigDict(from_attributes=True)
class UserOut(ORM):
    id:int
    name:str
    email:str
class FieldOut(FieldInput, ORM):
    id:int
    created_at:datetime
class ScanOut(ORM):
    id:int
    field_id:int|None
    notes:str
    prediction:dict
    created_at:datetime
class FollowupOut(ORM):
    id:int
    scan_id:int
    due_at:datetime
    done:bool
