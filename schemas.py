from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional,Any

# test API schema
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    createdAt: str
    createdBy: str
    lastSavedAt: str
    lastSavedBy: str
    isLocked: bool

    class Config:
        orm_mode = True


# Drill API Schema
class Resp(BaseModel):
    code: str
    error: str
    data: Any

class DrillInfo(BaseModel):
    product_name: str
    lot_number: str
    drill_machine_id: int
    drill_spindle_id: int
    ppm_control_limit: int
    ppm: int
    judge_ppm: bool
    drill_time: Optional[datetime] = None
    cpk: Optional[float] = -1
    cp :Optional[float] = -1
    ca :Optional[float] = -1
    aoi_time: Optional[datetime] = None
    ratio_target : Optional[float] = -1
    report_ee: Optional[str] = None
    report_time: Optional[datetime] = None
    comment: Optional[str] = None

    class Config:
        orm_mode = True

class MailInfo(BaseModel):
    email: str
    send_type: str

class EEInfo(BaseModel):
    ee_id: str
    name: str


class Report(BaseModel):
    lot_number: str = Field(..., title="drill lot number")
    machine_id: str = Field(..., title="drill machine id")
    spindle_id: str = Field(..., title="drill spindle id")
    contact_person: Optional[str] = None
    contact_time: Optional[datetime] = None
    comment: Optional[str] = None

class SearchMeasure(BaseModel):
    id_b: int

class SearchProduct(BaseModel):
    product_id: int

class SearchDrill(BaseModel):
    lot_number: str
    drill_machine_id: Optional[int] = None
    drill_spindle_id: Optional[int] = None

class ReportUpdate(BaseModel):
    report_ee: Optional[str] = None
    report_time: Optional[datetime] = None
    comment: Optional[str] = None
