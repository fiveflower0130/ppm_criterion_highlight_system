import os
import configparser
import math
import pandas as pd
import sys
from datetime import datetime 
from logger import Logger


class Singleton():
    __instance = None

    # Singleton的另一個寫法
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

class PPMIniReader(Singleton):

    def __init__(self):
        self.__file_name = 'ppm_config.ini'
        self.config = self.__get_config_info()
    
    def __get_ini_path(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)

        config_path = os.path.join(application_path, self.__file_name)
        return config_path

    def __get_config_info(self):
        ini_file_path = self.__get_ini_path()
        config = configparser.ConfigParser()
        config.read(ini_file_path, encoding='utf-8')
        return config

class TQMDataMining(Singleton):
    __logger = Logger().get_logger()
    __ppm_config = PPMIniReader().config
    
    def __init__(self):
        self.__execution_path = os.getcwd()
        self.__retry = 0
    
    def __get_ppm_control_limit(self, product_name:str)-> int:
        ppm_control_limit = 0
        file_name= self.__ppm_config.get("Excel", "ppm_file_name")
        file_path = os.path.join(self.__execution_path, file_name)
        # file_path = os.path.join(self.__execution_path, self.__config.get('Excel', 'ppm_file_name'))
        try:
            # sheet_name: 0->sheet1 , usecols: 0->圖號 12->散孔管制界限
            df = pd.read_excel(file_path, sheet_name='風險圖號', usecols=[0, 12])
            for i in range(len(df)):
                ppm_criteria_limit_name = df.at[i, df.columns[0]] 
                if (ppm_criteria_limit_name == product_name):
                    ppm_control_limit = int(df.at[i, df.columns[1]])
        except Exception as err:
            self.__logger.error(f"{str(err)}. ReTry {self.__retry+1}")
            if self.__retry < 3:
                self.__retry = self.__retry + 1
                self.__get_ppm_control_limit(product_name)
            else:     
                ppm_control_limit = -1
        finally:
            self.__retry = 0
            return ppm_control_limit


    def __get_report_receivers(self, mail_list:list)->dict:
        data = {
            "to": [],
            "cc": [],
            "bcc": [],
        }
        if len(mail_list)>0:
            for mail in mail_list:
                if mail.send_type == "to":
                    data["to"].append(mail.email)
                if mail.send_type == "cc":
                    data["cc"].append(mail.email)
                if mail.send_type == "bcc":
                    data["bcc"].append(mail.email)
        return data

    def get_drill_info_transfer(self, board: object, measure: object, product: object)->dict:
        drill_info = {}
        drill_info["lot_number"] = str(board.Lot)
        drill_info["product_name"] = str(product.Name_PD) if product.Name_PD else None

        if board.DrillTime:
            if len(board.DrillTime.split( )) > 1:
                drill_info["drill_time"] = datetime.strptime(board.DrillTime, "%Y/%m/%d %H:%M:%S")
            elif len(board.DrillTime.split( )) == 1 :
                drill_info["drill_time"] = datetime.strptime(board.DrillTime, "%Y/%m/%d")
            else:
                drill_info["drill_time"] = None
        if board.AOITime:
            if len(board.AOITime.split( )) > 1:
                drill_info["aoi_time"] = datetime.strptime(board.AOITime, "%Y/%m/%d %H:%M:%S")   
            elif len(board.AOITime.split( )) == 1 :
                drill_info["aoi_time"] = datetime.strptime(board.AOITime, "%Y/%m/%d")
            else:
                drill_info["aoi_time"] = None

        drill_info["drill_machine_id"] = int(board.DrillMachineID)
        drill_info["drill_spindle_id"] = int(board.DrillSpindleID)
        drill_info["ppm_control_limit"] = self.__get_ppm_control_limit(product_name=drill_info["product_name"]) 
        if measure:
            drill_info["ratio_target"] = float(measure.RatioInTarget_Before) if measure.RatioInTarget_Before else 0
            drill_info["cpk"] = float(measure.Cpk_Z_Before) if measure.Cpk_Z_Before else -1
            drill_info["cp"] = float(measure.CP_Z_Before) if measure.CP_Z_Before else -1
            drill_info["ca"] = float(measure.CA_Z_Before) if measure.CA_Z_Before else -1
        else:
            drill_info["ratio_target"] = 0
            drill_info["cpk"] = -1
            drill_info["cp"] = -1
            drill_info["ca"] = -1

        drill_info["ppm"] = (100 - drill_info["ratio_target"])*10000
        drill_info["judge_ppm"] = False if ((math.ceil(drill_info["ppm"]) > drill_info["ppm_control_limit"])) else True
        return drill_info

    def get_mail_data(self, highlight_info:dict, mail_list:list)->dict:
        sender = {
            'name': 'PPM Hightlight System Manager',
            'email': 'TID5940@aseglobal.com'
        }
        receivers = self.__get_report_receivers(mail_list)

        content =f"""
            <p>
               Dear all,<br> 
               機鑽穴位圖PPM已超出管制上限. 請EE立即至該機台確認<br>
               <br>
               1. 機台編號: {highlight_info['machine_id']+1}<br>
               2. 軸: {highlight_info['spindle_id']+1}<br>
               3. 批號: {highlight_info['lot_number']}<br>
               4. PPM: {math.floor(highlight_info['ppm'])}. (上限: {highlight_info['ppm_control_limit']})<br>
               <br>
               連結網頁: <a href="http://10.10.10.10:5000/Result/OpViewPage?lot={highlight_info['lot_number']}">http://10.10.10.10:5000/Result/OpViewPage?lot={highlight_info['lot_number']}</a>
            </p>
        """
        subject = f"[Warning!!!!!][機鑽站] PPM out of control limit. 機台編號: {highlight_info['machine_id']+1}, 軸: {highlight_info['spindle_id']+1}, 批號: {highlight_info['lot_number']}"

        send_data = {
            'from': sender,
            'to': receivers["to"],
            'cc': receivers["cc"],
            'bcc': receivers["bcc"],
            'subject': subject,
            'body': content,
            'attachment': []
        }
        return send_data