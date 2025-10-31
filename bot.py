import json

import requests


class Bot:
    api_key: str
    secret_token: str

    def __init__(self, api_key, secret_token):
        self.api_key = api_key
        self.secret_token = secret_token

    def handle_message(self, message):
        raise NotImplementedError()

    def send_message(self, text, chat_id, replay_markup=None):
        data = {"text": text, "chat_id": chat_id}
        if replay_markup is not None:
            data["reply_markup"] = replay_markup
        print(f"Sending message to {chat_id}: {text}")
        requests.post(
            f"http://localhost:8081/{self.api_key}/sendMessage",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data),
        )
