from sqlalchemy.schema import Column
from sqlalchemy.types import Boolean, DateTime, Float, Integer, String
from database import DBConnection


mssql = DBConnection("mssql")
mysql = DBConnection("mysql")


# -----------MYSQL MODELS-----------
class User(mysql.base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(20), unique=True, index=True)
    password = Column(String(255))
    createdAt = Column(String(100))
    createdBy = Column(String(20))
    lastSavedAt = Column(String(100))
    lastSavedBy = Column(String(20))
    isLocked = Column(Boolean, default=False)
    #apiTokens = Column(String(255))

class DrillInfo(mysql.base):
    # create __tablename__ attribute，宣告 model 對應的 database table name
    __tablename__ = "lot_drill_result"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String(64))
    lot_number = Column(String(32))
    drill_machine_id = Column(Integer)
    drill_spindle_id = Column(Integer)
    ppm_control_limit = Column(Integer)
    ppm = Column(Integer)
    judge_ppm = Column(Boolean)
    drill_time = Column(DateTime)
    cpk = Column(Float)
    cp = Column(Float)
    ca = Column(Float)
    aoi_time = Column(DateTime)
    ratio_target = Column(Float)
    report_ee = Column(String(16))
    report_time = Column(DateTime)
    comment = Column(String(512))

class MailInfo(mysql.base):
    __tablename__ = "mail_list"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(50))
    send_type = Column(String(10))

class EEInfo(mysql.base):
    __tablename__ = "ee_list"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ee_id = Column(String(10))
    name = Column(String(10))


# ---------MSSQL MODELS-----------
class BoardInfo(mssql.base):
    __tablename__ = "tBoard"

    ID_B = Column(Integer, primary_key=True, index=True)
    ProductID = Column(Integer)
    DrillMachineID = Column(Integer)
    DrillSpindleID = Column(Integer)
    DrillTime = Column(String)
    AOITime = Column(String)
    Lot = Column(String, index=True)

class MeasureInfo(mssql.base):
    __tablename__ = "tMeasure"

    ID_M = Column(Integer, primary_key=True, index=True)
    BoardID = Column(Integer, index=True)
    ToolID = Column(Integer)
    CA_Z_Before = Column(Float)
    CP_Z_Before = Column(Float)
    Cpk_Z_Before = Column(Float)
    RatioInTarget_Before = Column(Float)

class ProductInfo(mssql.base):
    __tablename__ = "tProduct"

    ID_PD = Column(Integer, primary_key=True, index=True)
    Name_PD = Column(String)


mysql.base.metadata.create_all(bind=mysql.engine)
mssql.base.metadata.create_all(bind=mssql.engine)