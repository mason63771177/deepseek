import os
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()  # 加载环境变量

app = Flask(__name__)

# 从环境变量获取配置
BOT_TOKEN = os.getenv('BOT_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
AUTHORIZED_USERS = os.getenv('AUTHORIZED_USERS', '').split(',')  # 允许使用的用户ID

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    try:
        data = request.json
        message = data.get('message', {})
        user_id = str(message['from']['id'])
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        # 权限验证
        if user_id not in AUTHORIZED_USERS:
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
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        ai_reply = response.json()['choices'][0]['message']['content']
        
        # 回复给 Telegram
        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(send_url, json={"chat_id": chat_id, "text": ai_reply})
        
    except Exception as e:
        print(f"⚠️ 错误: {str(e)}")
        # 发送错误通知
        if 'chat_id' in locals():
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": f"⚠️ 服务错误: {str(e)}"}
            )
    
    return "OK", 200

# 在 app.py 的末尾添加
if __name__ == '__main__':
    print("✅ 环境变量加载状态:")
    print(f"BOT_TOKEN: {'已设置' if BOT_TOKEN else '未设置'}")
    print(f"DEEPSEEK_API_KEY: {'已设置' if DEEPSEEK_API_KEY else '未设置'}")
    print(f"AUTHORIZED_USERS: {AUTHORIZED_USERS}")
    app.run(host='0.0.0.0', port=os.getenv('PORT', 10000))
