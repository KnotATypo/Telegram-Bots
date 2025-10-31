import os
from typing import Dict

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from waitress import serve

from bot import Bot
from expiry_bot import ExpiryBot
from tools_bot import ToolsBot

load_dotenv()

bots: Dict[str, Bot] = {"expiry": ExpiryBot(f"bot{os.getenv("EXPIRY_BOT_KEY")}", os.getenv("EXPIRY_BOT_SECRET")),
                        "tools": ToolsBot(f"bot{os.getenv("TOOLS_BOT_KEY")}", os.getenv("TOOLS_BOT_SECRET"))}

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


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)
