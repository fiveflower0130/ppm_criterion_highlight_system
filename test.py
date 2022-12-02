import crud
import pytest
from datetime import datetime
from database import DBConnection
from fastapi import Depends
from fastapi.testclient import TestClient
from fastapi_utils.session import FastAPISessionMaker
from sqlalchemy import engine
from sqlalchemy.schema import Column
from sqlalchemy.types import Boolean, DateTime, Float, Integer, String
from transfer import TQMDataMining, PPMIniReader
from main import app


#-------------init class object-------------------
test_mssql = DBConnection('mssql')
test_mysql = DBConnection('mysql')
test_trnasfer = TQMDataMining()
test_ini = PPMIniReader()
client = TestClient(app)

#-------------Create expect data--------------------
class TestDrillInfo(test_mysql.base):
    __test__ = False
    __tablename__ = "test_lot_drill_result"

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

class TestMailInfo(test_mysql.base):
    __test__ = False
    __tablename__ = "test_mail_list"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(50))
    send_type = Column(String(10))

class TestEEInfo(test_mysql.base):
    __test__ = False
    __tablename__ = "test_ee_list"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ee_id = Column(String(10))
    name = Column(String(10))

expect_drill_info = {
    'product_name': 'A298340',
    'lot_number': 'L231012216',
    'drill_machine_id': 30,
    'drill_spindle_id': 1,
    'ppm_control_limit': 20000,
    'ppm': 6650,
    'judge_ppm': False,
    'drill_time': '2022-11-30 10:00:50',
    'cpk': 1.68654,
    'cp' : 2.186,
    'ca' : 21.34,
    'aoi_time': '2022-11-30 12:04:50',
    'ratio_target': 99.65214
}
except_mail_info = {
    'email': 'Dante_Chen@aseglobal.com',
    'send_type': 'to'
}
except_ee_info = {
    "ee_id": "K07214",
    "name": "許家豪"
}

expect_board_info = {
    'ProductID': 0, 
    'ID_B': 0, 
    'DrillTime': '2022/11/04 22:05:00', 
    'DrillSpindleID': 0, 
    'Lot': 'L221018082', 
    'DrillMachineID': 19, 
    'AOITime': '2022/11/25 18:49:15'
}

expect_product_info={
    'ID_PD': 0,
    'Name_PD': 'P S-78FBGA-90A'
}

expect_measure_info={
    'ToolID': -1, 
    'ID_M': 55, 
    'RatioInTarget_Before': 99.99932861328125
}

expect_transfer_info = {
    'ppm_control_limit': 8000,
    'ppm': 6.7138671875, 
    'judge_ppm': True
}

#-------------Content Function Test------------------

def test_get_ini_info():
    assert test_ini.config.get('Database', 'ms_user') == "sa"
    assert test_ini.config.get('Database', 'my_user') == "5940"

def test_databse():
    # mssql
    assert test_mssql.database_url.split(":")[0] == "mssql+pyodbc"
    assert isinstance(test_mssql.engine, engine.base.Engine)
    assert isinstance(test_mssql.sessionmaker, FastAPISessionMaker)

    # mysql
    assert test_mysql.database_url.split(":")[0] == "mysql+pymysql"
    assert isinstance(test_mssql.engine, engine.base.Engine)
    assert isinstance(test_mssql.sessionmaker, FastAPISessionMaker)


def test_create_models():
    # should create model in mysql database
    test_mysql.base.metadata.create_all(bind=test_mysql.engine)
    assert test_mysql.engine.dialect.has_table(test_mysql.engine.connect(), "test_lot_drill_result") == True

@pytest.mark.anyio
async def test_create_data():
    with test_mysql.sessionmaker.context_session() as tmydb:
        db_drill_info = TestDrillInfo(**expect_drill_info)
        tmydb.add(db_drill_info)
        tmydb.commit()
        tmydb.refresh(db_drill_info)

        test_schema = {
            "lot_number": expect_drill_info["lot_number"],
            "drill_machine_id": expect_drill_info["drill_machine_id"],
            "drill_spindle_id": expect_drill_info["drill_spindle_id"]
        }

        test_drill_info = tmydb.query(TestDrillInfo).\
            filter(
                TestDrillInfo.lot_number == test_schema["lot_number"], 
                TestDrillInfo.drill_machine_id == test_schema["drill_machine_id"], 
                TestDrillInfo.drill_spindle_id == test_schema["drill_spindle_id"]
            ).first()
        
        assert test_drill_info.lot_number == db_drill_info.lot_number
        assert test_drill_info.drill_machine_id == db_drill_info.drill_machine_id
        assert test_drill_info.drill_spindle_id == db_drill_info.drill_spindle_id
    
    with test_mysql.sessionmaker.context_session() as tmydb:
        db_mail_info = TestMailInfo(**except_mail_info)
        tmydb.add(db_mail_info)
        tmydb.commit()
        tmydb.refresh(db_mail_info)

        test_mail_info = tmydb.query(TestMailInfo).first()
        print("test_mail_info: ",test_mail_info.__dict__)
        assert test_mail_info.email == db_mail_info.email
        assert test_mail_info.send_type == db_mail_info.send_type
    
    with test_mysql.sessionmaker.context_session() as tmydb:
        db_ee_info = TestEEInfo(**except_ee_info)
        tmydb.add(db_ee_info)
        tmydb.commit()
        tmydb.refresh(db_ee_info)

        test_ee_info = tmydb.query(TestEEInfo).first()
        assert test_ee_info.ee_id == db_ee_info.ee_id
        assert test_ee_info.name == db_ee_info.name

@pytest.mark.anyio
async def test_info_count():
    with test_mysql.sessionmaker.context_session() as tmydb, test_mssql.sessionmaker.context_session() as tmsdb:
        board_count = await crud.get_board_info_count(db = tmsdb)
        drill_count = await crud.get_drill_info_count(db = tmydb)
        assert board_count >= drill_count

@pytest.mark.anyio
async def test_get_drill_info():
    with test_mysql.sessionmaker.context_session() as tmydb:
        test_schemas = {
            "lot_number": "L221007216",
            "drill_machine_id": 49,
            "drill_spindle_id": 0
        }
        test_drill_info = await crud.get_drill_info(db= tmydb, search_items=test_schemas)
        assert test_drill_info.lot_number == test_schemas["lot_number"]
        assert test_drill_info.drill_machine_id == test_schemas["drill_machine_id"]
        assert test_drill_info.drill_spindle_id == test_schemas["drill_spindle_id"]

@pytest.mark.anyio
async def test_get_mail_info():
    expect_email = "Steve_Sun@aseglobal.com"
    with test_mysql.sessionmaker.context_session() as tmydb:
        test_mail_info = await crud.get_mail_info(db= tmydb)
        assert test_mail_info[0].email == expect_email

@pytest.mark.anyio
async def test_get_ee_info():
    expect_ee = {
        "name": "許家豪",
        "id": 1,
        "ee_id": "K07214"
    }
    with test_mysql.sessionmaker.context_session() as tmydb:
        test_ee_info = await crud.get_ee_info(db= tmydb)
        print(test_ee_info[0].__dict__)
        assert test_ee_info[0].name == expect_ee["name"] and test_ee_info[0].ee_id == expect_ee["ee_id"]

@pytest.mark.anyio
async def test_get_tqm_data():
    with test_mssql.sessionmaker.context_session() as tmsdb:
        test_boards_info = await crud.get_boards_info(tmsdb, skip= 0, limit= 1)
        
        assert test_boards_info[0].ProductID == expect_board_info["ProductID"]
        assert test_boards_info[0].DrillSpindleID == expect_board_info["DrillSpindleID"]
        assert test_boards_info[0].ID_B == expect_board_info["ID_B"]
        assert test_boards_info[0].DrillTime == expect_board_info["DrillTime"]
        assert test_boards_info[0].Lot == expect_board_info["Lot"]
        assert test_boards_info[0].DrillMachineID == expect_board_info["DrillMachineID"]
        assert test_boards_info[0].AOITime == expect_board_info["AOITime"]

        test_product_info = await crud.get_product_name(tmsdb, test_boards_info[0].ProductID)
        assert test_product_info.ID_PD == expect_product_info["ID_PD"]
        assert test_product_info.Name_PD == expect_product_info["Name_PD"]

        test_measure_info = await crud.get_measure_info(tmsdb, test_boards_info[0].ID_B)
        assert test_measure_info.ToolID == expect_measure_info["ToolID"]
        assert test_measure_info.ID_M == expect_measure_info["ID_M"]
        assert test_measure_info.RatioInTarget_Before == expect_measure_info["RatioInTarget_Before"]

        test_trans2drilinfo = test_trnasfer.get_drill_info_transfer(test_boards_info[0], test_measure_info, test_product_info)
        assert test_trans2drilinfo["ppm_control_limit"] == expect_transfer_info["ppm_control_limit"]
        assert test_trans2drilinfo["ppm"] == expect_transfer_info["ppm"]
        assert test_trans2drilinfo["judge_ppm"] == expect_transfer_info["judge_ppm"]


def test_drop_models():
    test_mysql.base.metadata.drop_all(bind=test_mysql.engine)
    assert test_mysql.engine.dialect.has_table(test_mysql.engine.connect(), "test_lot_drill_result") == False

# #-------------API Test------------------

def test_read_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"data": "Hello Drill API"}

def test_get_ee_list():
    expect_data= {
                "name": "許家豪",
                "id": 1,
                "ee_id": "K07214"
            }
            
    headers = {"x-token": "coneofsilence"}
    resp = client.get("/api/drill/eelist/", headers=headers)
    result = resp.json()
    assert resp.status_code == 200
    assert result["data"][0] == expect_data

def test_get_drill_info():
    lot = "L220718062"
    machine_id = 8
    spindle_id = 1
    headers = {"x-token": "coneofsilence"}

    # situation.1 all params
    resp = client.get(f"/api/drill/search?lot={lot}&machine_id={machine_id}&spindle_id={spindle_id}", headers=headers)
    result = resp.json()
    assert resp.status_code == 200
    assert (result["data"][0]["lot_number"] == lot) and (result["data"][0]["drill_machine_id"] == machine_id) and (result["data"][0]["drill_spindle_id"] == spindle_id)
    
    # situation.2 no machine_id
    resp = client.get(f"/api/drill/search?lot={lot}&spindle_id={spindle_id}", headers=headers)
    result = resp.json()
    assert resp.status_code == 200
    assert (result["data"][0]["lot_number"] == lot) and (result["data"][0]["drill_spindle_id"] == spindle_id)

    # situation.3 no spindle_id
    resp = client.get(f"/api/drill/search?lot={lot}&machine_id={machine_id}", headers=headers)
    result = resp.json()
    assert resp.status_code == 200
    assert (result["data"][0]["lot_number"] == lot) and (result["data"][0]["drill_machine_id"] == machine_id)

    # situation.3 no spindle_id, no machine_id
    resp = client.get(f"/api/drill/search?lot={lot}", headers=headers)
    result = resp.json()
    assert resp.status_code == 200
    assert len(result["data"]) > 1

def test_get_drill_judge_result():
    expect_product_name = "P S-78FBGA-90A"

    start_time = "2022-11-04 22:05:01"
    end_time = "2022-11-04 22:10:01"
    headers = {"x-token": "coneofsilence"}

    resp = client.get(f"/api/drill/judge?start_time={start_time}&end_time={end_time}", headers=headers)
    result = resp.json()
    assert resp.status_code == 200
    assert len(result["data"]) == 1 and result["data"][0]["product_name"] == expect_product_name

def test_update_drill_report_info():
    update_data = {
        "lot_number": "L221007216",
        "machine_id": 49,
        "spindle_id": 0,
        "contact_person": "K09857",
        "contact_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "comment": "PPM over limit"
    }
    headers = {"x-token": "coneofsilence"}
   

    resp = client.put("/api/drill/report", json=update_data, headers=headers)
    result = resp.json()
    assert resp.status_code == 200
    assert result["data"] == True
    
    resp = client.get(f"/api/drill/search?lot={update_data['lot_number']}&machine_id={update_data['machine_id']}&spindle_id={update_data['spindle_id']}", headers=headers)
    result = resp.json()
    result_time = datetime.strptime(result["data"][0]["report_time"], "%Y-%m-%dT%H:%M:%S")

    assert resp.status_code == 200
    assert result["data"][0]["report_ee"] == update_data["contact_person"] and result_time.strftime("%Y-%m-%d %H:%M:%S") == update_data["contact_time"]