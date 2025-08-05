import os
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
AUTHORIZED_USERS = os.getenv('AUTHORIZED_USERS', '').split(',')

# 简单的内存上下文存储
user_context = {}

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    try:
        data = request.json
        message = data.get('message', {})
        user_id = str(message['from']['id'])
        chat_id = message['chat']['id']
        text = message.get('text', '').strip()

        print(f"Received message from user: {user_id}")
        print(f"Authorized users: {AUTHORIZED_USERS}")
        print(f"Is authorized: {user_id in AUTHORIZED_USERS}")

        # 权限验证
        if user_id not in AUTHORIZED_USERS:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": "🚫 未授权访问"}
            )
            return "OK", 200

        if not text:
            return "OK", 200

        # 清除上下文命令
        if text.lower() in ['/clear', '清除', '清除上下文']:
            user_context.pop(user_id, None)
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": "✅ 上下文已清除。"}
            )
            return "OK", 200

        # 默认先回复一个“收到消息”提示
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": "🤖 思考中，请稍等..."}
        )

        # 上下文初始化
        if user_id not in user_context:
            user_context[user_id] = []

        # 添加用户消息到上下文
        user_context[user_id].append({"role": "user", "content": text})

        # 调用 DeepSeek
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
        payload = {
            "model": "deepseek-chat",
            "messages": user_context[user_id]
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )

        ai_reply = response.json()['choices'][0]['message']['content']

        # 添加 AI 回复到上下文
        user_context[user_id].append({"role": "assistant", "content": ai_reply})

        # 回复给用户
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": ai_reply}
        )

    except Exception as e:
        print(f"⚠️ 错误: {str(e)}")
        if 'chat_id' in locals():
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": f"⚠️ 服务错误: {str(e)}"}
            )

    return "OK", 200


if __name__ == '__main__':
    print("✅ 环境变量加载状态:")
    print(f"BOT_TOKEN: {'已设置' if BOT_TOKEN else '未设置'}")
    print(f"DEEPSEEK_API_KEY: {'已设置' if DEEPSEEK_API_KEY else '未设置'}")
    print(f"AUTHORIZED_USERS: {AUTHORIZED_USERS}")

    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
