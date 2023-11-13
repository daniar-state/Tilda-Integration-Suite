# file: /utilities.py

from yagmail import SMTP
from traceback import print_exc
from config import MAIL_USERNAME, MAIL_PASSWORD, CONTENTS


def handleNotificationStatus(api_name, msg, method, email, exc=None):
    if not exc:
        statusContext = f"{api_name} - {method} - Success\n\n{msg}"
    else:
        statusContext = f"{api_name} - {method} - Error\n\n{msg}\n\n{exc}"
        
    emailSendMessage(mail_recipient=email, msg=statusContext)
    return statusContext


def emailSendMessage(mail_recipient, msg):
    try:
        mail = SMTP(user=MAIL_USERNAME, password=MAIL_PASSWORD, host='smtp.mail.ru', port=465)
        mail.send(to=mail_recipient, subject='Информация о заказе', contents=msg) # contents=CONTENTS
    except Exception as error:
        print("Failed to send email: ", error)
        print_exc()
    return None