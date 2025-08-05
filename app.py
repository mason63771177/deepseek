# app.py
import os
import requests
from flask import Flask, request

app = Flask(__name__)

# 从环境变量获取配置
BOT_TOKEN = os.getenv('BOT_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
YOUR_TELEGRAM_ID = os.getenv('YOUR_TELEGRAM_ID', '')  # 添加您的专属ID
API_URL = "https://api.deepseek.com/v1/chat/completions"

def is_authorized(user_id):
    """检查用户是否在白名单内"""
    allowed_ids = [id.strip() for id in YOUR_TELEGRAM_ID.split(',') if id.strip()]
    return str(user_id) in allowed_ids

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    try:
        data = request.json
        message = data.get('message', {})
        user_id = message['from']['id']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        # 权限验证
        if not is_authorized(user_id):
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": "🚫 未授权访问"}
            )
            return "OK", 200
        
        if not text:
            return "OK", 200
        
        # DeepSeek API 调用
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": text}]
        }
        
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        ai_reply = response.json()['choices'][0]['message']['content']
        
        # 回复给 Telegram
        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(send_url, json={"chat_id": chat_id, "text": ai_reply})
        
    except Exception as e:
        print(f"⚠️ 错误: {str(e)}")
    
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)