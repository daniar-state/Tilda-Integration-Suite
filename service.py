# file: /service.py
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from requests import post, RequestException
from datetime import datetime
from base64 import b64encode
from hashlib import sha256
from time import time
from hmac import new
from pytz import timezone
import json
import uuid
from utilits import handleNotificationStatus
from db import DatabaseManager, Order, JollyOrder

db = DatabaseManager()


class VIPaymentAPI:
    HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "curl/7.64.1"
    }
    
    @staticmethod
    def place_an_order(uri, api_key, sign, service, user_id, zone_id, email):
        apiPath = "/game-feature"
        payload = {
            "key": api_key,
            "sign": sign,
            "type": "order",
            "service": service,
            "data_no": user_id,
            "data_zone": zone_id
        }
        try:
            response = post(url=f"{uri}{apiPath}", data=payload, headers=VIPaymentAPI.HEADERS)
            data = response.json()
            
            if response.status_code == 200:
                if data['result'] == True:
                    trxid = data['data']['trxid']
                    db.add_order(api_name='VIPAYMENT', order_id=trxid, email_user=email, status='waiting', order_details=str(data))
                    return trxid
                else:
                    handleNotificationStatus('VIPAYMENT', data, 'CREATE_ORDER', email, 'Result Failed')
            else:
                handleNotificationStatus('VIPAYMENT', data.raise_for_status(), 'CREATE_ORDER', email, 'RAISE FOR STATUS')
                data.raise_for_status()
        except RequestException as err:
            handleNotificationStatus('VIPAYMENT', err, 'CREATE_ORDER', email, 'Request Exception')
        return None
    
    @staticmethod
    def check_order(uri, api_key, sign, trxid, email):
        apiPath = "/game-feature"
        payload = {
            "key": api_key,
            "sign": sign,
            "type": "status",
            "trxid": trxid
        }
        try:
            response = post(url=f"{uri}{apiPath}", data=payload, headers=VIPaymentAPI.HEADERS)
            data = response.json()
            
            if response.status_code == 200:
                if data['result'] == True:
                    return data
                else:
                    handleNotificationStatus('VIPAYMENT', data, f"CheckOrderStatus {trxid}" if trxid is not None else 'CheckOrderStatus', email, 'RESULT FALSE')
            else:
                handleNotificationStatus('VIPAYMENT', data.raise_for_status(), f"CheckOrderStatus {trxid}" if trxid is not None else 'CheckOrderStatus', email, 'RAISE FOR STATUS')
                data.raise_for_status()
        except RequestException as err:
            handleNotificationStatus('VIPAYMENT', err, f"CheckOrderStatus {trxid}", email, err)
        return None
    

class MooGoldAPI:
    @staticmethod
    def create_auth_token(secret_key, partner_id):
        auth_token = b64encode(f"{partner_id}:{secret_key}".encode()).decode()
        return auth_token
    
    @staticmethod
    def create_auth_signature(secret_key, payload, path):
        timestamp = str(int(time()))
        string_to_sign = payload + timestamp + path
        auth_signature = new(bytes(secret_key, 'utf-8'), msg=string_to_sign.encode('utf-8'), digestmod=sha256).hexdigest()
        return auth_signature, timestamp
    
    @staticmethod
    def place_an_order(uri, secret_key, partner_id, service, user_id, zone_id, email):
        apiPath = "/order/create_order"
        payload = {
            "path": apiPath,
            "data": {
                "category": 1,
                "product-id": service,
                "quantity": 1,
                "User ID": user_id,
                "Server": zone_id,
                "Server ID": zone_id
            }
        }
        payload_json = json.dumps(payload)
        auth_basic = MooGoldAPI.create_auth_token(secret_key=secret_key, partner_id=partner_id)
        auth, timestamp = MooGoldAPI.create_auth_signature(secret_key=secret_key, payload=payload_json, path=apiPath)
        
        HEADERS = {
            "Content-Type": "application/json",
            "Authorization": "Basic " + auth_basic,
            "auth": auth,
            "timestamp": timestamp
        }
        try:
            response = post(url=f"{uri}{apiPath}", data=payload_json, headers=HEADERS)
            data = response.json()
            
            if response.status_code == 200:
                if data['status'] == True:
                    trxid = data['order_id']
                    db.add_order(api_name='MOOGOLD', order_id=trxid, email_user=email, status='waiting', order_details=str(data))
                    return trxid
                else:
                    handleNotificationStatus('MOOGOLD', data, 'CREATE_ORDER', email, 'Result Failed')
            else:
                handleNotificationStatus('MOOGOLD', data.raise_for_status(), 'CREATE_ORDER', email, 'RAISE FOR STATUS')
                data.raise_for_status()
        except RequestException as err:
            handleNotificationStatus('MOOGOLD', err, 'CREATE_ORDER', email, 'Request Exception')
        return None
    
    @staticmethod
    def check_order(uri, secret_key, partner_id, trxid, email):
        apiPath = "/order/order_detail"
        payload = {
            "path": apiPath,
            "order_id": trxid
        }
        payload_json = json.dumps(payload)
        auth_basic = MooGoldAPI.create_auth_token(secret_key=secret_key, partner_id=partner_id)
        auth, timestamp = MooGoldAPI.create_auth_signature(secret_key=secret_key, payload=payload_json, path=apiPath)
        
        HEADERS = {
            "Content-Type": "application/json",
            "Authorization": "Basic " + auth_basic,
            "auth": auth,
            "timestamp": timestamp
        }
        try:
            response = post(url=f"{uri}{apiPath}", data=payload_json, headers=HEADERS)
            data = response.json()
            
            if response.status_code == 200:
                if data['order_status'] == 'completed':
                    return data
                else:
                    handleNotificationStatus('MOOGOLD', data, f"CheckOrderStatus {trxid}" if trxid is not None else 'CheckOrderStatus', email, 'RESULT FALSE')
            else:
                handleNotificationStatus('MOOGOLD', data.raise_for_status(), f"CheckOrderStatus {trxid}" if trxid is not None else 'CheckOrderStatus', email, 'RAISE FOR STATUS')
                data.raise_for_status()
        except RequestException as err:
            handleNotificationStatus('MOOGOLD', err, f"CheckOrderStatus {trxid}", email, err)
        return None
    
    
class JollyMaxAPI:
    @staticmethod
    def timezone():
        tz = timezone('Europe/Moscow')
        cur_time = datetime.now(tz)
        req_time = cur_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + cur_time.strftime('%z')[:3] + ':' + cur_time.strftime('%z')[3:]
        return req_time
    
    @staticmethod
    def generate_unique_id(prefix=''):
        unique_id = str(uuid.uuid4()).replace('-', '')
        unique_time = datetime.now().strftime('%Y%m%d%H%M%S')
        return prefix + unique_time + unique_id
    
    @staticmethod
    def generate_signature(payload):
        with open('private.key.pem', 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signature = private_key.sign(
            payload_json,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        encoded_signature = b64encode(signature).decode('utf-8')
        return encoded_signature, payload_json
    
    @staticmethod
    def check_user(uri, app_id, no_id, code, user_id, zone_id, email):
        apiPath = "/distribute-check-user"
        requestTime = JollyMaxAPI.timezone()
        messageId = JollyMaxAPI.generate_unique_id()
        payload = {
            "requestTime": requestTime,
            "version": "1.0",
            "keyVersion": "1",
            "merchantAppId": app_id,
            "merchantNo": no_id,
            "data": {
                "code": code,
                "tradeInfo": {
                    "userId": user_id,
                    "serverId": zone_id,
                },
                "messageId": messageId
            }
        }
        signature, payload_json = JollyMaxAPI.generate_signature(payload)
        HEADERS = {
            "Content-Type": "application/json",
            "sign": signature
        }
        try:
            response = post(url=f"{uri}{apiPath}", data=payload_json, headers=HEADERS)
            data = response.json()
            
            if response.status_code == 200:
                if data['code'] == 'APPLY_SUCCESS':
                    role_id = data['data']['extension']['roles']
                    return role_id
                else:
                    handleNotificationStatus('JOLLYMAX', data, 'CHECK_USER', email, 'Result Failed')
            else:
                handleNotificationStatus('JOLLYMAX', data.raise_for_status(), 'CHECK_USER', email, 'RAISE FOR STATUS')
                data.raise_for_status()
        except RequestException as err:
            handleNotificationStatus('JOLLYMAX', err, 'CHECK_USER', email, 'Request Exception')
        return None
    
    @staticmethod
    def place_an_order(uri, app_id, no_id, code, user_id, zone_id, email):
        apiPath = "/distribute-order-create"
        requestTime = JollyMaxAPI.timezone()
        outOrderId = JollyMaxAPI.generate_unique_id(prefix='TM003400')
        messageId = JollyMaxAPI.generate_unique_id()
        payload = {
            "requestTime": requestTime,
            "version": "1.0",
            "keyVersion": "1",
            "merchantAppId": app_id,
            "merchantNo": no_id,
            "data": {
                "outOrderId": outOrderId,
                "code": code,
                "quantity": 1,
                "tradeInfo": {
                    "userId": user_id,
                    "serverId": zone_id,
                    "role_id": "",
                },
                "messageId": messageId,
            }
        }
        signature, payload_json = JollyMaxAPI.generate_signature(payload)
        HEADERS = {
            "Content-Type": "application/json",
            "sign": signature
        }
        try:
            response = post(url=f"{uri}{apiPath}", data=payload_json, headers=HEADERS)
            data = response.json()
            
            if response.status_code == 200:
                if data['code'] == 'APPLY_SUCCESS':
                    trxid = data['data']['orderId']
                    db.add_jm_order(api_name='JOLLYMAX', order_id=trxid, message_id=messageId, email_user=email, status='waiting', order_details=str(data))
                    return trxid, messageId
                else:
                    handleNotificationStatus('JOLLYMAX', data, 'CREATE_ORDER', email, 'Result Failed')
            else:
                handleNotificationStatus('JOLLYMAX', data.raise_for_status(), 'CREATE_ORDER', email, 'RAISE FOR STATUS')
                data.raise_for_status()
        except RequestException as err:
            handleNotificationStatus('JOLLYMAX', err, 'CREATE_ORDER', email, 'Request Exception')
        return None
    
    @staticmethod
    def check_order(uri, app_id, no_id, outOrderId, messageId, email):
        apiPath = "/distribute-order-query"
        requestTime = JollyMaxAPI.timezone()
        payload = {
            "requestTime": requestTime,
            "version": "1.0",
            "keyVersion": "1",
            "merchantAppId": app_id,
            "merchantNo": no_id,
            "data": {
                "outOrderId": outOrderId,
                "messageId": messageId
            }
        }
        signature, payload_json = JollyMaxAPI.generate_signature(payload)
        HEADERS = {
            "Content-Type": "application/json",
            "sign": signature
        }
        try:
            response = post(url=f"{uri}{apiPath}", data=payload_json, headers=HEADERS)
            data = response.json()
            
            if response.status_code == 200:
                if data['code'] == 'APPLY_SUCCESS':
                    return data
                else:
                    handleNotificationStatus('JOLLYMAX', data, f"CheckOrderStatus {outOrderId} {messageId}" if outOrderId is not None and messageId is not None else 'CheckOrderStatus', email, 'RESULT FALSE')
            else:
                handleNotificationStatus('JOLLYMAX', data.raise_for_status(), f"CheckOrderStatus {outOrderId} {messageId}" if outOrderId is not None and messageId is not None else 'CheckOrderStatus', email, 'RAISE FOR STATUS')
                data.raise_for_status()
        except RequestException as err:
            handleNotificationStatus('JOLLYMAX', err, f"CheckOrderStatus {outOrderId} {messageId}", email, err)
        return None

