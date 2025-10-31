import json
import os

import requests


class Bot:
    api_token: str
    secret_token: str

    def __init__(self, api_token, secret_token):
        self.api_token = api_token
        self.secret_token = secret_token

    def handle_message(self, message):
        raise NotImplementedError()

    def send_message(self, text, chat_id, replay_markup=None):
        data = {"text": text, "chat_id": chat_id}
        if replay_markup is not None:
            data["reply_markup"] = replay_markup
        print(f"Sending message to {chat_id}: {text}")
        requests.post(
            f"{os.getenv("BOT_API_URL")}/{self.api_token}/sendMessage",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data),
        )
