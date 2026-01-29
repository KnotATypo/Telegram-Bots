import enum
import json
import os
from datetime import datetime
from typing import Tuple

import requests

from telegram_bots import util
from telegram_bots.bot import DatabaseBot
from telegram_bots.tools.tool_util import get_power_draw
from telegram_bots.logger import logger


class States(enum.Enum):
    POWER_METER = "power meter"
    CHECK_ESTIMATE = "check estimate"
    OCCUPANCY = "occupancy"

    def __str__(self):
        return self.value


CUSTOM_KEYBOARD = {
    "keyboard": [[{"text": "Power meter"}, {"text": "Check estimate"}, {"text": "Occupancy"}]],
    "resize_keyboard": True,
    "input_field_placeholder": "Choose an option",
    "is_persistent": True,
}


class ToolsBot(DatabaseBot):
    state_manager: util.StateManager = util.StateManager(States)
    time_estimate: dict[str, Tuple[datetime, int]] = {}

    def __init__(self, bot_token, bot_secret):
        logger.debug("Initialising ToolsBot...")
        super().__init__(f"bot{bot_token}", bot_secret)

        with self.db_cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS occupancy (time TEXT, count int)")
        logger.info("ToolsBot initialised")

    def handle_message(self, data):
        """
        Handle incoming message

        :param data: Incoming message data
        :return: None
        """
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
        """
        Handle incoming message with text content

        :param chat_id: ID of the chat the message is from
        :param message: Message data
        :param state: State of the chat
        :return: None
        """
        text: str = message["text"]

        if self.handle_global_commands(chat_id, text):
            return

        if state is None:
            try:
                new_state = States[text.upper().replace(" ", "_")]
                self.state_manager.set_state(chat_id, new_state)
                if new_state == States.POWER_METER:
                    self.send_message("Please send video", chat_id, replay_markup={"remove_keyboard": True})
                elif new_state == States.CHECK_ESTIMATE:
                    self.send_message("Provide estimate in minutes", chat_id, replay_markup={"remove_keyboard": True})
                elif new_state == States.OCCUPANCY:
                    self.send_message(
                        "Provide a count or name of a day to retrieve data for",
                        chat_id,
                        replay_markup={"remove_keyboard": True},
                    )
            except KeyError:
                self.send_message("Please selection from keyboard options", chat_id, replay_markup=CUSTOM_KEYBOARD)

        elif state == States.CHECK_ESTIMATE:
            self.store_estimate(chat_id, message["text"])
        elif state == States.OCCUPANCY:
            self.store_or_retrieve_occupancy(chat_id, message["text"])

    def handle_global_commands(self, chat_id, text: str) -> bool:
        """
        Handle global commands that can be called from any state

        :param chat_id: ID of the chat the message is from
        :param text: Text content of the message
        :return: Boolean indicating if a global command was handled
        """
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
            debug_string = f"Current state: {self.state_manager.get_state(chat_id)}\n\n=====\nTime estimate\n"

            time_estimate = self.time_estimate.get(chat_id, None)
            if time_estimate is not None:
                time_estimate = (
                    f"Start - {time_estimate[0].strftime("%Y-%m-%d %H:%M:%S")}, Estimate - {time_estimate[1]}"
                )
            debug_string += f"Stored estimate: {time_estimate}\n====="

            self.send_message(debug_string, chat_id)

        else:
            return False

        return True

    def read_power_meter(self, chat_id, message):
        """
        Read power meter from video message and send result back to user

        :param chat_id: ID of the chat the message is from
        :param message: Message data
        :return:
        """
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

    def store_estimate(self, chat_id: str, text: str):
        """
        Store time estimate in minutes provided by user

        :param chat_id: ID of the chat the message is from
        :param text: Text content of the message
        :return:
        """
        try:
            estimate_minutes = int(text)
            self.time_estimate[chat_id] = (datetime.now(), estimate_minutes)
            self.send_message(
                'Estimate stored. Send "done" to complete estimate', chat_id, replay_markup=CUSTOM_KEYBOARD
            )
            self.state_manager.clear_state(chat_id)
        except ValueError:
            self.send_message("Please provide an estimate in minutes", chat_id)

    def store_or_retrieve_occupancy(self, chat_id: str, text: str):
        """
        Store occupancy provided by user if given text is a number, or retrieve occupancy otherwise

        :param chat_id: ID of the chat the message is from
        :param text: Text content of the message
        :return:
        """

        def sort_time(entry):
            day_multi = {
                "Monday": 0,
                "Tuesday": 1,
                "Wednesday": 2,
                "Thursday": 3,
                "Friday": 4,
                "Saturday": 5,
                "Sunday": 6,
            }
            time = entry[0]
            day = time.split(" ")[0]
            hour = time.split(" ")[1].split(":")[0]
            minute = time.split(" ")[1].split(":")[1]
            return day_multi[day] * 24 + int(hour) + float(f"0.{minute}")

        try:
            number = int(text)
            with self.db_cursor() as cursor:
                time = datetime.now().strftime("%A %H:%M")
                cursor.execute("INSERT INTO occupancy VALUES (?, ?)", (time, number))
            self.send_message(f"Count of {number} stored for {time}", chat_id, replay_markup=CUSTOM_KEYBOARD)
        except ValueError:  # Passed value is not a number
            with self.db_cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM occupancy WHERE time LIKE ?", (f"%{text}%",)
                )  # Using fuzzy matching to allow for short names to be passed
                counts = cursor.fetchall()
            counts = sorted(counts, key=sort_time)
            count_string = ""
            for count in counts:
                hour = int(count[0].split(":")[0].split(" ")[1])
                if hour > 12:
                    hour -= 12
                    period = "pm"
                else:
                    period = "am"
                time = f"{count[0].split(" ")[0]} {hour}:{count[0].split(":")[1]}{period}"
                count_string += f"{time:18} {count[1]}\n"
            if count_string == "":
                self.send_message("No occupancy was found", chat_id)
            else:
                self.send_message(count_string, chat_id, replay_markup=CUSTOM_KEYBOARD)

        self.state_manager.clear_state(chat_id)
