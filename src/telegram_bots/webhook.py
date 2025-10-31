import queue
import threading
from typing import Dict

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from waitress import serve

load_dotenv()

from telegram_bots.bot import Bot
from telegram_bots.expiry.expiry_bot import ExpiryBot
from telegram_bots.tools.tools_bot import ToolsBot

app = Flask(__name__)
bots: Dict[str, Bot] = {}
task_q = queue.Queue()


def worker():
    while True:
        bot, data = task_q.get()
        try:
            bot.handle_message(data)
        except Exception as e:
            print(f"{type(e)}: {e}")
        finally:
            task_q.task_done()


threading.Thread(target=worker, daemon=True).start()


@app.route("/webhook", methods=["POST"])
def webhook():
    host = request.headers["host"].split(".")[0]
    bot = bots[host]

    if request.headers["X-Telegram-Bot-Api-Secret-Token"] != bot.secret_token:
        return jsonify({"status": "failure"}), 415

    task_q.put((bot, request.json))

    return jsonify({"status": "success"}), 200


def start():
    print("Initialising bots...")
    bots["expiry"] = ExpiryBot()
    bots["tools"] = ToolsBot()
    print("Starting webhook server...")
    serve(app, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    start()
