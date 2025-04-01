from flask import Flask, request, jsonify
import os
import openai
import requests

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    # 1. Xử lý xác minh từ Lark
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # 2. Xử lý message từ user gửi đến
    event = data.get("event", {})
    message = event.get("message", {})
    sender = event.get("sender", {})

    if message.get("message_type") == "text":
        text = message.get("content", {}).get("text", "")
        user_id = sender.get("sender_id", {}).get("user_id")

        # Gọi OpenAI GPT để phản hồi
        openai.api_key = os.getenv("OPENAI_API_KEY")
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý Eve."},
                {"role": "user", "content": text}
            ]
        )
        reply_text = gpt_response["choices"][0]["message"]["content"]

        # Lấy access token từ Lark
        lark_resp = requests.post(
            "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
            json={
                "app_id": os.getenv("LARK_APP_ID"),
                "app_secret": os.getenv("LARK_APP_SECRET")
            }
        ).json()
        access_token = lark_resp.get("tenant_access_token")

        # Gửi tin nhắn lại cho user
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        msg_body = {
            "receive_id": user_id,
            "content": {"text": reply_text},
            "msg_type": "text"
        }
        requests.post(
            "https://open.larksuite.com/open-apis/im/v1/messages?receive_id_type=user_id",
            headers=headers,
            json=msg_body
        )

    return "OK"


@app.route("/", methods=["GET"])
def index():
    return "Eve-Assistant is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
