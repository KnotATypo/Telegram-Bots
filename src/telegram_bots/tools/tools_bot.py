import json
import os
from datetime import datetime
from typing import Tuple

import requests

from telegram_bots.bot import Bot
from telegram_bots.tools.util import get_power_draw

STATES = ["Power meter", "Check estimate"]
CUSTOM_KEYBOARD = {
    "keyboard": [[{"text": "Power meter"}, {"text": "Check estimate"}]],
    "resize_keyboard": True,
    "input_field_placeholder": "Choose an option",
    "is_persistent": True,
}


class ToolsBot(Bot):
    state: str
    time_estimate: dict[str, Tuple[datetime, int]] = {}

    def __init__(self):
        print("Initialising ToolsBot...")
        super().__init__(f"bot{os.getenv("TOOLS_BOT_TOKEN")}", os.getenv("TOOLS_BOT_SECRET"))
        self.state = "idle"
        print("ToolsBot initialised")

    def handle_message(self, data):
        message = data["message"]
        chat_id = message["chat"]["id"]

        if "text" in message and message["text"].lower() == "done":
            start_time, estimate = self.time_estimate[chat_id]
            actual = round((datetime.now() - start_time).seconds / 60, 2)
            percent = round(100 / estimate * ((estimate - actual) if actual < estimate else (actual - estimate)), 1)
            self.send_message(
                f"Estimate: {estimate}\nActual: {actual}\nDifference: {percent}%",
                chat_id,
                replay_markup=CUSTOM_KEYBOARD,
            )
        elif self.state == "idle":
            if message["text"] in STATES:
                self.state = message["text"]
                if self.state == "Power meter":
                    self.send_message("Please send video", chat_id, replay_markup={"remove_keyboard": True})
                elif self.state == "Check estimate":
                    self.send_message("Provide estimate in minutes", chat_id, replay_markup={"remove_keyboard": True})
            else:
                self.send_message("Please selection from options", chat_id, replay_markup=CUSTOM_KEYBOARD)
        elif self.state == "Power meter":
            self.read_power_meter(chat_id, message)
        elif self.state == "Check estimate":
            self.store_estimate(chat_id, message["text"])

    def read_power_meter(self, chat_id, message):
        if "video" in message:
            response = requests.get(
                f"{os.getenv("BOT_API_URL")}/{self.api_token}/getFile?file_id={message["video"]['file_id']}"
            )
            response = response.json()
            path = response["result"]["file_path"]
            try:
                power_draw = get_power_draw(path)
                requests.post(
                    f"{os.getenv("BOT_API_URL")}/{self.api_token}/sendChatAction",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps({"action": "typing", "chat_id": chat_id}),
                )
                self.send_message(power_draw, chat_id, replay_markup=CUSTOM_KEYBOARD)
                os.remove(path)
                self.state = "idle"
            except Exception as e:
                self.send_message(f"Error: {e}", chat_id)
        else:
            self.send_message("That wasn't a video, try again", chat_id)

    def store_estimate(self, chat_id: str, message: str):
        try:
            estimate_minutes = int(message)
            self.time_estimate[chat_id] = (datetime.now(), estimate_minutes)
            self.send_message(
                'Estimate stored. Send "done" to complete estimate', chat_id, replay_markup=CUSTOM_KEYBOARD
            )
            self.state = "idle"
        except ValueError:
            self.send_message("Please provide an estimate in minutes", chat_id)
