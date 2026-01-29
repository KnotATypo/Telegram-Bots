import json
import os
import sqlite3
from contextlib import contextmanager

import requests
from dotenv import load_dotenv

from telegram_bots.webhook import app

load_dotenv()


class Bot:
    api_token: str
    secret_token: str
    message_url: str

    def __init__(self, api_token, secret_token):
        self.api_token = api_token
        self.secret_token = secret_token
        self.message_url = f"{os.getenv("BOT_API_URL")}/{self.api_token}/sendMessage"

    def handle_message(self, message):
        raise NotImplementedError()

    def send_message(self, text, chat_id, replay_markup=None):
        data = {"text": text, "chat_id": chat_id}
        if replay_markup is not None:
            data["reply_markup"] = replay_markup
        app.logger.info(f"Sending message to {chat_id}: {text}")
        requests.post(
            self.message_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data),
        )


class DatabaseBot(Bot):
    db_path: str

    def __init__(self, api_token, secret_token):
        super().__init__(api_token, secret_token)
        self.db_path = os.getenv("DATABASE_PATH")

    @contextmanager
    def db_cursor(self):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        yield cursor
        connection.commit()
        connection.close()
