from typing import Dict

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from waitress import serve

load_dotenv()

from telegram_bots.bot import Bot
from telegram_bots.expiry.expiry_bot import ExpiryBot
from telegram_bots.tools.tools_bot import ToolsBot

bots: Dict[str, Bot] = {"expiry": ExpiryBot(),
                        "tools": ToolsBot()}

app = Flask(__name__)


# piKPsA0BN5Ji
@app.route("/webhook", methods=["POST"])
def webhook():
    host = request.headers["host"].split(".")[0]
    bot = bots[host]

    print(request.json)

    if request.headers["X-Telegram-Bot-Api-Secret-Token"] != bot.secret_token:
        return jsonify({"status": "failure"}), 415

    data = request.json
    try:
        bot.handle_message(data)
    except Exception as e:
        print(f"{type(e)}: {e}")

    return jsonify({"status": "success"}), 200


def start():
    serve(app, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    start()
