import os.path
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
# Dict of subdomain to Bot instance
bots: Dict[str, Bot] = {}
task_q = queue.Queue()


def worker():
    while True:
        bot, data = task_q.get()
        try:
            bot.handle_message(data)
        except Exception as e:
            error = f"{type(e)}: {e}"
            print(error)
            print(data)
            bot.send_message(error, data["message"]["chat"]["id"])
        finally:
            task_q.task_done()


threading.Thread(target=worker, daemon=True).start()


@app.route("/health_check", methods=["GET"])
def health_check():
    # Webhooks are already specific to each bot
    host = request.headers["host"].split(".")[0]
    if host in bots:
        return jsonify({"status": "ok"}), 200
    else:
        return jsonify({"status": "not found"}), 404


@app.route("/webhook", methods=["POST"])
def webhook():
    host = request.headers["host"].split(".")[0]
    bot = bots[host]

    if (
        "X-Telegram-Bot-Api-Secret-Token" not in request.headers
        or request.headers["X-Telegram-Bot-Api-Secret-Token"] != bot.secret_token
    ):
        return jsonify({"status": "unauthorized"}), 401

    print("Webhook received for:", host)
    if "message" in request.json:
        task_q.put((bot, request.json))
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "success"}), 204


def start():
    print("Initialising bots...")

    expiry_bot_token = os.getenv("EXPIRY_BOT_TOKEN")
    expiry_bot_secret = os.getenv("EXPIRY_BOT_SECRET")
    if expiry_bot_token and expiry_bot_secret:
        bots["expiry-webhook"] = ExpiryBot(expiry_bot_token, expiry_bot_secret)
    else:
        print("Expiry bot token or secret not provided, not launching bot.")

    tools_bot_token = os.getenv("TOOLS_BOT_TOKEN")
    tools_bot_secret = os.getenv("TOOLS_BOT_SECRET")
    if tools_bot_token and tools_bot_secret:
        bots["tools-webhook"] = ToolsBot(tools_bot_token, tools_bot_secret)
    else:
        print("Tools bot token or secret not provided, not launching bot.")

    print("Starting webhook server...")
    serve(app, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    start()
