# file: /main.py

import json
import asyncio
from time import sleep
from threading import Thread
from flask import Flask, request, jsonify, abort
from flask_cors import CORS

from db import DatabaseManager, Order, JollyOrder
from utilits import emailSendMessage
from service import VIPaymentAPI, MooGoldAPI, JollyMaxAPI

from config import (
    LOCAL_HOST, SERVER_HOST, PORT, PRODUCT_STATUS,
    VIPayment_SUCCESS_STATUSES, MooGold_SUCCESS_STATUSES, JollyMax_SUCCESS_STATUSES,
    VIPAY_URI, VIPAY_API_ID, VIPAY_API_KEY, VIPAY_SIGN,
    MGOLD_URI, MGOLD_SECRET_KEY, MGOLD_PARTNER_ID,
    JMAX_URI, JMAX_MERCHANT_ID, JMAX_MERCHANT_APP_ID, JM_CODE
)


db = DatabaseManager()
app = Flask(__name__)
CORS(app)


def check_status(interval=60):
    while True:
        orders = db.get_orders_by_status('waiting')
        for order in orders:
            if isinstance(order, (list, tuple)): 
                api_name, order_id, email_user, _, _ = order
            else:
                api_name = order.api_name
                order_id = order.order_id
                email_user = order.email_user
                
            if api_name == 'VIPAYMENT':
                orderData = VIPaymentAPI.check_order(uri=VIPAY_URI, api_key=VIPAY_API_KEY, sign=VIPAY_SIGN, trxid=order_id, email=email_user)
                if not orderData or not isinstance(orderData, dict) or 'data' not in orderData:
                    continue
                if isinstance(orderData['data'], list) and len(orderData['data']) > 0:
                    status = orderData['data'][0].get('status')
                    service = orderData['data'][0].get('service')
                    price = orderData['data'][0].get('price')
                else:
                    status = None
                    
                success_statuses = VIPayment_SUCCESS_STATUSES
                statusContext = f"{api_name} - ORDER PAYMENT - Success\n\n{orderData}"
                emailSendMessage(mail_recipient=email_user, msg=statusContext)
                db.update_order(order_id=order_id, status=status, new_order_details=json.dumps(orderData))
            elif api_name == 'MOOGOLD':
                orderData = MooGoldAPI.check_order(uri=MGOLD_URI, secret_key=MGOLD_SECRET_KEY, partner_id=MGOLD_PARTNER_ID, trxid=order_id, email=email_user)
                if not orderData or not isinstance(orderData, dict) or 'data' not in orderData:
                    continue
                if isinstance(orderData['data'], list) and len(orderData['data']) > 0:
                    status = orderData.get('order_status')
                    price = orderData.get('total')
                else:
                    status = None
                    
                success_statuses = MooGold_SUCCESS_STATUSES
                statusContext = f"{api_name} - ORDER PAYMENT - Success\n\n{orderData}"
                
                emailSendMessage(mail_recipient=email_user, msg=statusContext)
                db.update_order(order_id=order_id, new_status=status, new_order_details=json.dumps(orderData))
            else:
                continue
            
            if not status or status not in success_statuses:
                continue
        
        jm_orders = db.get_orders_jm_by_status('waiting')
        for order in jm_orders:
            if isinstance(order, (list, tuple)): 
                _, api_name, order_id, message_id, email_user, _, _ = order
            else:
                api_name = order.api_name
                order_id = order.order_id
                message_id = order.message_id
                email_user = order.email_user
                
            orderData = JollyMaxAPI.check_order(uri=JMAX_URI, app_id=JMAX_MERCHANT_APP_ID, no_id=JMAX_MERCHANT_ID, outOrderId=order_id, messageId=message_id, email=email_user)
            if not orderData or not isinstance(orderData, dict) or 'data' not in orderData:
                    continue
            if isinstance(orderData['data'], list) and len(orderData['data']) > 0:
                status = orderData['data'][0].get('status')
                price = orderData['data'][0].get('tradeAmount')
            else:
                status = None
            
            success_statuses = JollyMax_SUCCESS_STATUSES
            
            if not status or status not in success_statuses:
                continue
            
            statusContext = f"{api_name} - ORDER PAYMENT - Success\n\n{orderData}"
            emailSendMessage(mail_recipient=email_user, msg=statusContext)
            db.update_jm_order(order_id=order_id, message_id=message_id, new_status=status, new_order_details=json.dumps(orderData))
        sleep(interval)


@app.route('/', methods=['GET'])
def index():
    return "Стартовый маршрут. SERVICE API V3"

@app.route('/v3/skyshop', methods=['POST'])
def skyshop_get_webhook():
    
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
        
    if 'test' in data:
        return jsonify({ "status": "success", "message": "Test request received", "data": data['test'] })
    
    user_id = data.get('Input')
    zone_id = data.get('Zone_ID')
    email = data.get('Email')
    select_box = data.get('Selectbox')
    
    if not all([user_id, zone_id, email]):
        return jsonify({ "error": "Missing parameters!" }), 400
    
    payment_data_str = data.get('payment')
    if not payment_data_str:
        return jsonify({ "error": "Missing payment data" }), 400
    
    try:
        payment_data = json.loads(payment_data_str)
    except json.JSONDecodeError:
        return jsonify({ "error": "Invalid payment data" }), 400
    
    products = payment_data.get('products', [])
    if not products:
        return jsonify({ "error": "No products found" }), 400
    
    product_info = products[0].split('+')
    if len(product_info) < 3:
        return jsonify({ "error": "Invalid product format" }), 400
    
    service_code, product_code, product_name = product_info[0], product_info[1], product_info[2]
    
    if service_code == 'VP':
        response = VIPaymentAPI.place_an_order(uri=VIPAY_URI, api_key=VIPAY_API_KEY, sign=VIPAY_SIGN, service=product_code, user_id=user_id, zone_id=zone_id, email=email)
    elif service_code == 'MG':
        response = MooGoldAPI.place_an_order(uri=MGOLD_URI, secret_key=MGOLD_SECRET_KEY, partner_id=MGOLD_PARTNER_ID, service=product_code, user_id=user_id, zone_id=zone_id, email=email)
    elif service_code == 'JM':
        response = JollyMaxAPI.place_an_order(uri=JMAX_URI, app_id=JMAX_MERCHANT_APP_ID, no_id=JMAX_MERCHANT_ID, code=product_code, user_id=user_id, zone_id=zone_id, email=email)
    else:
        return jsonify({ "error": "Invalid service prefix" }), 400
    
    return jsonify({ "status": "success", "message": "Successful data", "data": response})



if __name__ == '__main__':
    background_task = Thread(target=check_status)
    background_task.start()
    app.run(port=PORT, host=LOCAL_HOST, debug=False)
