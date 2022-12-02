import smtplib
import mimetypes

from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email.header import Header

from transfer import TQMDataMining 
from logger import Logger


tqm = TQMDataMining()

class EmailClientSingleton():
    __instance = None

    # Singleton
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance


class EmailClient(EmailClientSingleton):
    __logger = Logger().get_logger()

    def __init__(self):
        self.__emailClient = {}
    
    def __getClient(self, host:str) -> object:
        return self.__emailClient[host]

    def __getReceivers(self, to:list) -> str:
        receiver_list = None
        if len(to) > 0:
            receiver_list = ",".join(to)
        return receiver_list
    
    def __getMessage(self, data:dict)->object:

        message = MIMEMultipart('alternative')
        message['From'] = Header(data['from']['name'], 'utf-8') # 發送者
        message['To'] =  Header(self.__getReceivers(data['to']), 'utf-8') # 接收者
        message['cc'] = Header(self.__getReceivers(data['cc']), 'utf-8') if len(data['cc']) > 0 else None # 副本
        message['bcc'] = Header(self.__getReceivers(data['bcc']), 'utf-8') if len(data['bcc']) > 0 else None # 密件本
        message['Subject'] = Header(data['subject'], 'utf-8') if len(data['subject']) > 0 else "無標題" # 標題
    
        body = MIMEText(data['body'], 'html', 'utf-8') if len(data['body']) > 0 else MIMEText('''<p>無內容</p>''', 'html', 'utf-8')
        message.attach(body)

        if len(data['attachment'])>0:
            for attach in data['attachment']:
                ctype, encoding = mimetypes.guess_type(attach)
                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"
                maintype, subtype = ctype.split("/", 1)

                if maintype == "text":
                    fp = open(attach, "rb")
                    attachment = MIMEText(fp.read(), _subtype=subtype, _charset='utf-8')
                    fp.close()
                elif maintype == "image":
                    fp = open(attach, "rb")
                    attachment = MIMEImage(fp.read(), _subtype=subtype)
                    fp.close()
                elif maintype == "audio":
                    fp = open(attach, "rb")
                    attachment = MIMEAudio(fp.read(), _subtype=subtype)
                    fp.close()
                else:
                    fp = open(attach, 'rb')
                    attachment = MIMEBase(maintype, subtype)
                    attachment.set_payload(fp.read())
                    fp.close()
                    encoders.encode_base64(attachment)
                
                #attachment["Content-Type"] = 'application/octet-stream'
                attachment["Content-Disposition"] = f'attachment; filename="{attach}"'
                message.attach(attachment)

        return message
    
    def addClient(self, host:str, port:str=''):
        # self.__logger.info(f"init email client {host}......")
        try:
            if(len(port) > 0):
                self.__emailClient[host] = smtplib.SMTP(f"{host}:{port}")
            else:
                self.__emailClient[host] = smtplib.SMTP(host)
        except smtplib.SMTPException as error:
             self.__logger.error(f"Initial fail: {error}")

    def sendEmail(self, host:str, data:dict):
        try:
            email_client = self.__getClient(host)
            sender = data['from']['email']
            receiver = data['to'] + data['cc'] + data['bcc']
            message = self.__getMessage(data)
            
            email_client.sendmail(sender, receiver, message.as_string())
            # self.__logger.info(f"已發送郵件.")
        except smtplib.SMTPException as e:
            self.__logger.error(f"Error: 無法發送郵件, {e}")