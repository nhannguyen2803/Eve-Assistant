from flask import Flask, request, jsonify
import os
import requests
import openai

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    # 👉 Nếu Lark đang gửi challenge để xác minh webhook
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    event = data.get("event", {})
    if event.get("type") == "message":
        user_id = event["sender"]["sender_id"]["user_id"]
        text = event.get("text", "")

        # Gọi GPT
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý ảo Eve, chuyên giúp người dùng tóm tắt cuộc họp, viết báo cáo và hỗ trợ công việc."},
                {"role": "user", "content": text}
            ]
        )
        answer = response["choices"][0]["message"]["content"]

        # Lấy token từ Lark
        token_res = requests.post(
            "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
            json={
                "app_id": os.environ.get("LARK_APP_ID"),
                "app_secret": os.environ.get("LARK_APP_SECRET")
            }
        ).json()
        token = token_res["tenant_access_token"]

        # Gửi tin nhắn về Lark
        requests.post(
            "https://open.larksuite.com/open-apis/message/v4/send/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": user_id,
                "msg_type": "text",
                "content": {"text": answer}
            }
        )
    return "ok"
