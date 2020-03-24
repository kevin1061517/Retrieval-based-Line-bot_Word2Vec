import re
from flask import Flask, request, abort
from simi_extract import CandReplyer
from chatter import Chatter
import os
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)
cand_replyer = CandReplyer()
chatter = Chatter()
mode = "promote"
mode_pattern = re.compile(r'.+\smode$')

is_prod = os.environ.get('IS_HEROKU', None)
if is_prod:
    line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN',''))
    handler = WebhookHandler(os.environ.get('CHANNEL_SECRET',''))


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if mode_pattern.match(event.message.text):
        keyword = event.message.text.split(" ")[0]
        if keyword == "promote":
            mode = "promote"
            reply = "Change to promote mode!"
        elif keyword == "chat":
            mode = "chat"
            reply = "Change to chat mode!"
        else:
            reply = "Sorry, We only have promote and chat mode now :("
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply))
    elif mode == "promote":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=cand_replyer.reply(event.message.text)))
    elif mode == "chat":
        reply = chatter.response(event.message.text)
        if reply == "stick":
            line_bot_api.reply_message(
                event.reply_token,
                StickerSendMessage(
                    package_id='1',
                    sticker_id='1'
                ))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply))


if __name__ == "__main__":
    app.run()