from fastapi_utils.session import FastAPISessionMaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Iterator
from transfer import PPMIniReader

# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:TID_5940@localhost:3306/tid_5940"
# # SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:5940@192.168.0.100:3306/automatic_highlight_system"

# # echo=True表示引擎將用repr()函式記錄所有語句及其引數列表到日誌
# engine = create_engine(SQLALCHEMY_DATABASE_URL)

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # 建立基本對映類
# Base = declarative_base()
ppm_config = PPMIniReader().config


class DBConnection(object):

    def __init__(self, db_type):
        self.database_url =self.__get_connection_url(db_type)
        self.engine = create_engine(self.database_url)
        self.sessionmaker = self.__get_fastapi_sessionmaker()
        self.session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.base = declarative_base()

    def __get_connection_url(self, db_type) -> str:
        url = ("")
        if db_type == 'mssql':
            """ get MSSQL info from ini config """
            user = ppm_config.get('Database', 'ms_user')
            password = ppm_config.get('Database', 'ms_password')
            host = ppm_config.get('Database', 'ms_host')
            port = ppm_config.get('Database', 'ms_port')
            db = ppm_config.get('Database', 'ms_db')
            driver = 'ODBC+Driver+17+for+SQL+Server'

            url = (f"mssql+pyodbc://{user}:{password}@{host}:{port}/{db}"f"?driver={driver}")
        elif db_type == 'mysql':
            """ get MYSQL info from ini config """
            user = ppm_config.get('Database', 'my_user')
            password = ppm_config.get('Database', 'my_password')
            host = ppm_config.get('Database', 'my_host')
            port = ppm_config.get('Database', 'my_port')
            db = ppm_config.get('Database', 'my_db')

            url = (f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}")
            
        return url

    def __get_fastapi_sessionmaker(self) -> FastAPISessionMaker:
        """ This function could be replaced with a global variable if preferred """
        database_uri = self.database_url
        return FastAPISessionMaker(database_uri)
    
    def get_db(self) -> Iterator[sessionmaker]:
        """ FastAPI dependency that provides a sqlalchemy session """
        yield from self.sessionmaker.get_db()

    def get_db_session(self):
        db = self.session()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


class MySQLConnect():

    def __init__(self):
        self.database_url = "mysql+pymysql://5940:5940@localhost:3306/tid_5940"
        # self.database_url = self.__get_connection_url()
        self.engine = create_engine(self.database_url)
        self.session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.sessionmaker = FastAPISessionMaker(self.database_url)
        self.base = declarative_base()

    def __get_connection_url(self) -> str:
        """ get MYSQL info from ini config """
        user = ppm_config.get('Database', 'my_user')
        password = ppm_config.get('Database', 'my_password')
        host = ppm_config.get('Database', 'my_host')
        port = ppm_config.get('Database', 'my_port')
        db = ppm_config.get('Database', 'my_db')

        url = (f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}")
        return url
    
    def get_db_session(self):
        db = self.session()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

class MsSQLConnect():

    def __init__(self):
        self.database_url = ("mssql+pyodbc://sa:mvtqmsystem@10.16.94.44:1433/mvTQMBox""?driver=ODBC+Driver+17+for+SQL+Server")
        self.database_url =self.__get_connection_url()
        self.engine = create_engine(self.database_url)
        self.session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.sessionmaker = FastAPISessionMaker(self.database_url)
        self.base = declarative_base()

    def __get_connection_url(self) -> str:
        """ get MSSQL info from ini config """
        user = ppm_config.get('Database', 'ms_user')
        password = ppm_config.get('Database', 'ms_password')
        host = ppm_config.get('Database', 'ms_host')
        port = ppm_config.get('Database', 'ms_port')
        db = ppm_config.get('Database', 'ms_db')

        url = (f"mssql+pyodbc://{user}:{password}@{host}:{port}/{db}""?driver=ODBC+Driver+17+for+SQL+Server")
        return url
    
    def get_db_session(self):
        db = self.session()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
