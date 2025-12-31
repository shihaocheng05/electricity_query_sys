#邮件工具（欠费提醒、验证码）
from flask_mail import Mail,Message
from ..middleware import BusinessException
from flask import current_app

def send_mail(mail,subject:str,recipients:list,cc:list,bcc:list,html:str=None,body:str=None)->str:
    msg=Message(
        subject=subject,
        recipients=recipients,
        cc=cc,
        bcc=bcc,
        html=html,
        body=body
    )

    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"邮件发送失败：{str(e)}")
        raise BusinessException("邮件发送失败",500)