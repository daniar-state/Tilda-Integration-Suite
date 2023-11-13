# file: /config.py

#? Constants
VIPayment_SUCCESS_STATUSES = ['success', 'error']
MooGold_SUCCESS_STATUSES = ['completed', 'failed']
JollyMax_SUCCESS_STATUSES = ['SUCC', 'FAIL']


#? Server parameters
PORT = 5000
LOCAL_HOST = 'http://localhost'
SERVER_HOST = ''

#? Data for mail connection
MAIL_USERNAME = '' # Mail login
MAIL_PASSWORD = '' # Mail password

#? Data for vipayment service connection
VIPAY_URI = 'https://vip-reseller.co.id/api'
VIPAY_API_ID = ''
VIPAY_API_KEY = ''
VIPAY_SIGN = ''

#? Data for moogold service connection
MGOLD_URI = 'https://moogold.com/wp-json/v1/api'
MGOLD_SECRET_KEY = ''
MGOLD_PARTNER_ID = ''

#? Data for jollymax service connection
JMAX_URI = 'https://api.jollymax.com/aggregate-pay/api/gateway'
JMAX_MERCHANT_ID = ''
JMAX_MERCHANT_APP_ID = ''
JM_CODE = [
    'ff15',
    'cdkey-fail',
    'cdkey-succ',
    'ff5d',
    'xld10'
]

PRODUCT_STATUS = ['VP', 'MG', 'JM']

#? Data for mail message
CONTENTS = """
Hello, dear user!
            
This email was sent to you from _. Please do not reply to it.
            
Order information:
            
- Order Number: 1111111111
- Service: 11111111
- Amount: 1111
- Status: Successful!
            
Thank you for the purchase!
            
Regards, _.
"""