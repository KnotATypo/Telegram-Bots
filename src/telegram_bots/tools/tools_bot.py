import enum
import json
import os
from datetime import datetime
from typing import Tuple

import requests

from telegram_bots import util
from telegram_bots.bot import Bot
from telegram_bots.tools.tool_util import get_power_draw


class States(enum.Enum):
    POWER_METER = "power meter"
    CHECK_ESTIMATE = "check estimate"

    def __str__(self):
        return self.value


CUSTOM_KEYBOARD = {
    "keyboard": [[{"text": "Power meter"}, {"text": "Check estimate"}]],
    "resize_keyboard": True,
    "input_field_placeholder": "Choose an option",
    "is_persistent": True,
}


class ToolsBot(Bot):
    state_manager: util.StateManager = util.StateManager(States)
    time_estimate: dict[str, Tuple[datetime, int]] = {}

    def __init__(self):
        print("Initialising ToolsBot...")
        super().__init__(f"bot{os.getenv("TOOLS_BOT_TOKEN")}", os.getenv("TOOLS_BOT_SECRET"))
        print("ToolsBot initialised")

    def handle_message(self, data):
        message = data["message"]
        chat_id = message["chat"]["id"]
        state = self.state_manager.get_state(chat_id)

        if "text" in message:
            self.handle_text(chat_id, message, state)

        elif "video" in message:
            if state == States.POWER_METER:
                self.read_power_meter(chat_id, message)
            else:
                self.send_message(
                    "It looks like you sent a video, but I wasn't expecting one. Please select an option from the keyboard.",
                    chat_id,
                    replay_markup=CUSTOM_KEYBOARD,
                )

    def handle_text(self, chat_id, message, state: enum.Enum | None):
        text: str = message["text"]

        self.global_commands(chat_id, text)

        if state is None:
            try:
                new_state = States[text.upper().replace(" ", "_")]
                self.state_manager.set_state(chat_id, new_state)
                if new_state == States.POWER_METER:
                    self.send_message("Please send video", chat_id, replay_markup={"remove_keyboard": True})
                elif new_state == States.CHECK_ESTIMATE:
                    self.send_message("Provide estimate in minutes", chat_id, replay_markup={"remove_keyboard": True})
            except KeyError:
                self.send_message("Please selection from keyboard options", chat_id, replay_markup=CUSTOM_KEYBOARD)

        elif state == States.CHECK_ESTIMATE:
            self.store_estimate(chat_id, message["text"])

    def global_commands(self, chat_id, text: str):
        text = text.lower()

        if text == "/start":
            self.send_message(
                "Welcome to ToolsBot! Please select an option from the keyboard below.",
                chat_id,
                replay_markup=CUSTOM_KEYBOARD,
            )
            self.state_manager.clear_state(chat_id)

        elif chat_id in self.time_estimate and text == "done":
            start_time, estimate = self.time_estimate[chat_id]
            actual = round((datetime.now() - start_time).seconds / 60, 2)
            percent = round(100 / estimate * ((estimate - actual) if actual < estimate else (actual - estimate)), 1)
            self.send_message(
                f"Estimate: {estimate}\nActual: {actual}\nDifference: {percent}%",
                chat_id,
                replay_markup=CUSTOM_KEYBOARD,
            )
            del self.time_estimate[chat_id]

        elif text in ["stop", "cancel", "clear"]:
            self.state_manager.clear_state(chat_id)
            self.send_message(
                "State cleared. Please select an option from the keyboard.", chat_id, replay_markup=CUSTOM_KEYBOARD
            )

        elif text == "debug":
            self.send_message(f"Current state: {self.state_manager.get_state(chat_id)}", chat_id)
            self.send_message(f"Stored estimate: {self.time_estimate.get(chat_id, None)}", chat_id)

    def read_power_meter(self, chat_id, message):
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
        except Exception as e:
            self.send_message(f"Error: {e}", chat_id)

    def store_estimate(self, chat_id: str, message: str):
        try:
            estimate_minutes = int(message)
            self.time_estimate[chat_id] = (datetime.now(), estimate_minutes)
            self.send_message(
                'Estimate stored. Send "done" to complete estimate', chat_id, replay_markup=CUSTOM_KEYBOARD
            )
            self.state_manager.clear_state(chat_id)
        except ValueError:
            self.send_message("Please provide an estimate in minutes", chat_id)
