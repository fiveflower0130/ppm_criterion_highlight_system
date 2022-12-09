from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas

# ----------------MySQL CRUD----------------------
async def get_drill_info_count(db: Session):
    data = db.query(models.DrillInfo).count()
    return data

async def get_drill_info(db: Session, search_items: schemas.SearchDrill):
    if search_items["drill_machine_id"] and search_items["drill_spindle_id"]:
        data = db.query(models.DrillInfo).\
            filter(
                models.DrillInfo.lot_number == search_items["lot_number"], 
                models.DrillInfo.drill_machine_id == search_items["drill_machine_id"], 
                models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"]
            ).all()
    elif search_items["drill_machine_id"]:
        data = db.query(models.DrillInfo).\
            filter(
                models.DrillInfo.lot_number == search_items["lot_number"], 
                models.DrillInfo.drill_machine_id == search_items["drill_machine_id"]
            ).all()
    elif search_items["drill_spindle_id"]:
        data = db.query(models.DrillInfo).\
            filter(
                models.DrillInfo.lot_number == search_items["lot_number"], 
                models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"]
            ).all()
    else:
        data = db.query(models.DrillInfo).\
            filter(
                models.DrillInfo.lot_number == search_items["lot_number"], 
            ).all()

    return data

async def get_ee_info(db: Session):
    data = db.query(models.EEInfo).all()
    return data

async def get_mail_info(db: Session):
    data = db.query(models.MailInfo).all()
    return data

async def get_judge_info(db: Session, start_time:datetime, end_time:datetime):
    data = db.query(models.DrillInfo).filter(models.DrillInfo.aoi_time.between(start_time, end_time)).all()
    return data

async def create_drill_info(db: Session, drill_info: schemas.DrillInfo):
    db_drill_info = models.DrillInfo(**drill_info)
    db.add(db_drill_info)
    db.commit()
    db.refresh(db_drill_info)
    return db_drill_info

async def create_mail_info(db: Session, mail_info: schemas.MailInfo):
    db_mail_info = models.MailInfo(**mail_info)
    db.add(db_mail_info)
    db.commit()
    db.refresh(db_mail_info)
    return db_mail_info

async def create_ee_info(db: Session, ee_info: schemas.EEInfo):
    db_ee_info = models.EEInfo(**ee_info)
    db.add(db_ee_info)
    db.commit()
    db.refresh(db_ee_info)
    return db_ee_info

async def update_drill_report_info(db: Session, search_items: schemas.SearchDrill, update_items: schemas.ReportUpdate):
    result = False
    data = db.query(models.DrillInfo).\
        filter(
            models.DrillInfo.lot_number == search_items["lot_number"], 
            models.DrillInfo.drill_machine_id == search_items["drill_machine_id"], 
            models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"]
        ).first()

    if data:
        update_dict = update_items
        for key, value in update_dict.items():
            setattr(data, key, value)
        db.commit()
        db.flush()
        db.refresh(data)
        result = True
    return result

# --------------------------MSSQL CRUD--------------------------------------

async def get_board_info_count(db: Session):
    data = db.query(models.BoardInfo).filter(models.BoardInfo.AOITime !="").count()
    return data

async def get_board_info(db: Session, boardInfo_id: int):
    data = db.query(models.BoardInfo).filter(models.BoardInfo.ID_B == boardInfo_id).first()
    return data

async def get_boards_info(db: Session, skip: int, limit: int):
    # data = db.query(models.BoardInfo).all()
    data = db.query(models.BoardInfo).filter(models.BoardInfo.AOITime !="").limit(limit).all()
    print("temp_limit: ",skip, " limit: ",limit)
    # print("board info: ",data[0].__dict__)
    data = data[skip:limit]
    return data

async def get_measure_info(db: Session, board_id: int):
    data = db.query(models.MeasureInfo).\
        filter(
            models.MeasureInfo.BoardID == board_id,
            models.MeasureInfo.ToolID == -1,
        ).first()
    return data

async def get_product_name(db: Session, product_id: int):
    data = db.query(models.ProductInfo).filter(models.ProductInfo.ID_PD == product_id).first()
    return data

