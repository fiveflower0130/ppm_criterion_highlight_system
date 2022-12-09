import uvicorn
import crud, schemas
import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi_utils.tasks import repeat_every
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database import DBConnection
from email_client import EmailClient
from logger import Logger
from transfer import TQMDataMining, PPMIniReader

# init FastApi
app = FastAPI()

# init logger
logger = Logger().get_logger()

# init MsSQL MySQL object
mssql = DBConnection("mssql")
mysql = DBConnection("mysql")

#init TQM data mining and ppmconfig
tqm = TQMDataMining()
ppm_config = PPMIniReader().config

# init email object
email_host=ppm_config.get("Email", "email_host")
email = EmailClient()


@app.on_event("startup")
@repeat_every(seconds=60*5, logger=logger, raise_exceptions= True)
async def run_tqm_process():
    """自動排程更新drill資料庫內資料並寄信通知異常狀態\n

    repeat_every Args: \n
        seconds: 輪迴秒數,
        logger: 紀錄logger
        raise_exceptions: 例外處理顯示結果
    Response: \n
        1. Loop 如果TQM DB資料 > Drill DB資料
        2. 取得TQM Board資料
        3. 取得Measure和Product資料並轉換內容
        4. 判斷PPM是否有超標，若有則發送通知信件
    """
    temp_limit = 0
    with mssql.sessionmaker.context_session() as msdb, mysql.sessionmaker.context_session() as mydb:
        board_count = await crud.get_board_info_count(db = msdb)
        drill_count = await crud.get_drill_info_count(db = mydb)
        # board_count = 8564
        # drill_count = 8562
        temp_limit = temp_limit + drill_count
    print("board_count: ",board_count, " drill_count: ",drill_count)
    while  board_count > temp_limit:
        boards_info = await crud.get_boards_info(msdb, skip= temp_limit, limit= temp_limit+100)
        if boards_info:
            for i in range(len(boards_info)):
                try:
                    board_id = boards_info[i].ID_B
                    product_id = boards_info[i].ProductID
                    product_info = await crud.get_product_name(msdb, product_id)
                    measure_info = await crud.get_measure_info(msdb, board_id)
                    drill_info = tqm.get_drill_info_transfer(boards_info[i], measure_info, product_info)
                    data = await crud.create_drill_info(mydb, drill_info)
                    if ((data.ppm_control_limit > 0) and (data.ratio_target > 0)):
                        if (data.judge_ppm == False):
                            print(f"Fail_drill_info: {drill_info}")
                            highlight_info = {
                                "machine_id":data.drill_machine_id,
                                "spindle_id":data.drill_spindle_id,
                                "lot_number":data.lot_number,
                                "ppm":data.ppm,
                                "ppm_control_limit":data.ppm_control_limit
                            }
                            mail_list = await crud.get_mail_info(mydb)
                            send_data = tqm.get_mail_data(highlight_info, mail_list)
                            email.addClient(host=email_host)
                            email.sendEmail(host= email_host, data= send_data)
                except Exception as e:
                    logger.error("error: ", e)
        else:
            logger.error("Can't fetch boards_info!")
            # break
        temp_limit = temp_limit+100
    print(f"Mission Completed at {datetime.now()}")


# API文件中定義的回傳格式
def resp(errMsg, data=None):
    resp = {"code": "0", "error": ""}

    if errMsg is not None:
        resp["code"] = "1"
        resp["error"] = errMsg
    else:
        resp["data"] = data

    return resp

'''
PPM Drill Info API
'''
@app.get("/")
async def read_root():
    return {"data": "Hello Drill API"}


@app.get("/api/drill/eelist", response_model=schemas.Resp)
async def get_ee_list(db: Session = Depends(mysql.get_db))->dict:
    """讀取EE通報名單\n

    Args: \n
        無
    Response: \n
        Object:{code: 執行結果(0是success, 1是fail), error: 錯誤訊息, data: [{內容}]}
    """
    try:
        data = await crud.get_ee_info(db)
    except Exception as err:
        return resp(str(err))
    finally:
        return resp(None, data)


@app.get("/api/drill/search", response_model=schemas.Resp)
async def get_drill_info(
    lot: str,
    machine_id: int = None,
    spindle_id: int = None,
    db: Session = Depends(mysql.get_db)) -> dict:
    """取得鑽孔批號柱號的資訊\n

    Args: \n
        lot: 批號,
        machine_id: 鑽孔機ID
        spindle_id: 柱號ID
    Response: \n
        Object:{code: 執行結果(0是success, 1是fail), error: 錯誤訊息, data: [{內容}]}
    """
    items = {
        "lot_number": lot,
        "drill_machine_id": machine_id,
        "drill_spindle_id": spindle_id
    }
    db_drill_info = await crud.get_drill_info(db, search_items=items)
    if db_drill_info is None:
        raise HTTPException(status_code=404, detail="User not found")
    return resp(None, db_drill_info)


@app.get("/api/drill/judge", response_model=schemas.Resp)
async def get_drill_judge_result(
    start_time: Optional[datetime] = None, 
    end_time: Optional[datetime] = None, 
    db: Session = Depends(mysql.get_db)):
    """讀取資料庫內穴位機量測結果&系統判斷結果\n

    Args: \n
        start_time: 開始時間,
        end_time: 結束時間
    Response: \n
        Object:{code: 執行結果(0是success, 1是fail), error: 錯誤訊息, data: [{內容}]}
    """
    if start_time and not end_time:
        raise HTTPException(status_code=422, detail="end_time could not be empty")
    if end_time and not start_time:
        raise HTTPException(status_code=422, detail="start_time could not be empty")
    try:
        data = await crud.get_judge_info(db, start_time, end_time)
    except Exception as err:
        return resp(str(err))
    finally:
        return resp(None, data)

@app.post("/api/drill/mail", response_model=schemas.Resp)
async def add_email_info(body: schemas.MailInfo, db: Session = Depends(mysql.get_db)):
    """新增資料庫通報信箱清單\n

    Args: \n
        body: {
            email: 信箱,
            send_type: 寄信類別(ex: to, cc, bcc)
        }
    Response: \n
        Object:{code: 執行結果(0是success, 1是fail), error: 錯誤訊息, data: [{內容}]}
    """
    if not body.email:
        return resp("email could not be empty!")
    if not body.send_type:
        return resp("send type could not be empty!")
    try:
        mail_info = {}
        mail_info["email"] = body.email
        mail_info["send_type"] = body.send_type
        data = await crud.create_mail_info(db, mail_info)

    except Exception as err:
        return resp(str(err))
    finally:
        return resp(None, data)

@app.post("/api/drill/eelist", response_model=schemas.Resp)
async def add_ee_info(body: schemas.EEInfo, db: Session = Depends(mysql.get_db)):
    """新增資料庫EE名單\n

    Args: \n
        body: {
            ee_id: EE的工號
            name: EE的姓名
        }
    Response: \n
        Object:{code: 執行結果(0是success, 1是fail), error: 錯誤訊息, data: [{內容}]}
    """
    if not body.ee_id:
        return resp("EE ID could not be empty!")
    if not body.name:
        return resp("EE name could not be empty!")
    try:
        ee_info = {}
        ee_info["ee_id"] = body.ee_id
        ee_info["name"] = body.name
        data = await crud.create_ee_info(db, ee_info)

    except Exception as err:
        return resp(str(err))
    finally:
        return resp(None, data)

@app.put("/api/drill/report", response_model=schemas.Resp)
async def update_drill_report_info(body: schemas.Report, db: Session = Depends(mysql.get_db)):
    """更新資料庫內OP通報EE狀態、備註、時間\n

    Args: \n
        body: {
            lot_number: 批號,
            machine_id: 鑽孔機ID,
            spindle_id: 軸別ID,
            contact_person: OP通報EE,
            contact_time: OP通報時間
            comment: OP備註
        }
    Response: \n
        Object:{code: 執行結果(0是success, 1是fail), error: 錯誤訊息, data: [{內容}]}
    """
    if not body.lot_number:
        return resp("lot number could not be empty!")
    if not body.machine_id:
        return resp("machine id could not be empty!")
    if not body.spindle_id:
        return resp("spindle id could not be empty!")
    search_items = {}
    update_items = {}
    try:
        search_items["lot_number"] = body.lot_number
        search_items["drill_machine_id"] = int(body.machine_id)
        search_items["drill_spindle_id"] = int(body.spindle_id)
        update_items["report_ee"] = body.contact_person if body.contact_person else None
        update_items["report_time"] = body.contact_time if body.contact_time else None
        update_items["comment"] = body.comment if body.comment else None
        data = await crud.update_drill_report_info(db, search_items, update_items)

    except Exception as err:
        return resp(str(err))
    finally:
        return resp(None, data)


if __name__ == "__main__":
    # if you don't want to run test before, close it
    pytest.main(['--html=report/report.html', 'test.py'])
    # pytest.main()
    uvicorn.run(app="main:app", host="0.0.0.0", port=8003, reload=True)