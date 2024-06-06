from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from api.chatgpt import ChatGPT
import os

# 初始化 LineBotApi 和 WebhookHandler
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFAULT_TALKING", default="true").lower() == "true"

app = Flask(__name__)
chatgpt = ChatGPT()

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # 獲取 X-Line-Signature header 的值
    signature = request.headers['X-Line-Signature']
    # 獲取請求的 body
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # 處理 Webhook 請求
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    if event.message.type != "text":
        return

    if event.message.text == "說話":
        working_status = True
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我可以說話囉，歡迎來跟我互動 ^_^ "))
        return

    if event.message.text == "閉嘴":
        working_status = False
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「說話」 > <"))
        return

    if working_status:
        chatgpt.add_msg(f"HUMAN:{event.message.text}")
        try:
            reply_msg = chatgpt.get_response().replace("AI:", "", 1)
            chatgpt.add_msg(f"AI:{reply_msg}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_msg))
        except Exception as e:
            app.logger.error(f"Error getting response from OpenAI: {e}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="發生錯誤，請稍後再試。"))

if __name__ == "__main__":
    app.run(debug=True)
