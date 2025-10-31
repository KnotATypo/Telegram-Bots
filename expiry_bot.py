import atexit
import os
import sqlite3
from collections import defaultdict
from datetime import datetime
from typing import Dict

from apscheduler.schedulers.background import BackgroundScheduler

from bot import Bot

CUSTOM_KEYBOARD = {
    "keyboard": [[{"text": "Add"}, {"text": "List"}, {"text": "Remove"}]],
    "resize_keyboard": True,
    "input_field_placeholder": "Choose an option",
    "is_persistent": True,
}


class ExpiryBot(Bot):
    user_state: Dict[str, Dict[str, str]]
    sched: BackgroundScheduler

    def __init__(self):
        super().__init__(f"bot{os.getenv("EXPIRY_BOT_TOKEN")}", os.getenv("EXPIRY_BOT_SECRET"))
        self.user_state = defaultdict(lambda: {"state": "idle", "item": None})
        self.sched = BackgroundScheduler(daemon=True)

        connection = sqlite3.connect("data.db")
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS items (name TEXT, date TEXT)")
        connection.commit()
        connection.close()

        self.sched.add_job(self.send_notifications, "cron", hour=10, minute=0)
        self.sched.start()
        atexit.register(lambda: self.sched.shutdown())

    def send_notifications(self):
        connection = sqlite3.connect("data.db")
        cursor = connection.cursor()
        cursor.execute("SELECT name, date FROM items")
        rows = cursor.fetchall()
        today = datetime.now().date()
        for row in rows:
            item_name = row[0]
            expiration_date = datetime.strptime(row[1], "%Y-%m-%d").date()
            if expiration_date == today:
                for chat_id in ["5937133733", "6167840973"]:
                    self.send_message(f"{item_name} will expire today", chat_id)
            elif expiration_date == today.replace(day=today.day + 1):
                for chat_id in ["5937133733", "6167840973"]:
                    self.send_message(f"{item_name} will expire tomorrow", chat_id)
        connection.close()

    def handle_message(self, data):
        text = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]
        state = self.user_state[chat_id]["state"]

        if text == "Add" and state == "idle":
            self.user_state[chat_id]["state"] = "adding_item"
            self.send_message("Please provide the item to add:", chat_id, {"remove_keyboard": True})
        elif state == "adding_item":
            self.user_state[chat_id]["state"] = "adding_date"
            self.user_state[chat_id]["item"] = text
            self.send_message("Please provide the expiration date (DD/MM):", chat_id)
        elif state == "adding_date":
            if "/" not in text:
                self.send_message("Invalid date format. Please provide the expiration date in DD/MM format:", chat_id)
                return
            day = text.split("/")[0]
            month = text.split("/")[1]
            try:
                day = int(day)
                month = int(month)
                assert 1 <= day <= 31
                assert 1 <= month <= 12
            except:
                self.send_message("Invalid date format. Please provide the expiration date in DD/MM format:", chat_id)
                return
            year = datetime.now().year
            if (
                month < datetime.now().month
                or (month == datetime.now().month and day < datetime.now().day)
                or (month == datetime.now().month and day == datetime.now().day)
            ):
                year += 1
            date = f"{year}-{month:02d}-{day:02d}"
            connection = sqlite3.connect("data.db")
            cursor = connection.cursor()
            cursor.execute("INSERT INTO items (name, date) VALUES (?, ?)", (self.user_state[chat_id]["item"], date))
            connection.commit()
            connection.close()
            self.send_message(f"{self.user_state[chat_id]['item']} will expire on {date}", chat_id, CUSTOM_KEYBOARD)
            self.user_state[chat_id]["state"] = "idle"
            self.user_state[chat_id]["item"] = None
        elif text == "List" and state == "idle":
            connection = sqlite3.connect("data.db")
            cursor = connection.cursor()
            cursor.execute("SELECT name, date FROM items")
            rows = cursor.fetchall()
            if not rows:
                self.send_message("No items found.", chat_id, CUSTOM_KEYBOARD)
            else:
                rows.sort(key=lambda x: datetime.strptime(x[1], "%Y-%m-%d"))
                message = "Items:\n"
                for row in rows:
                    message += f"- {row[0]} (expires on {row[1]})\n"
                self.send_message(message, chat_id, CUSTOM_KEYBOARD)
            connection.close()
        elif text == "Remove" and state == "idle":
            self.user_state[chat_id]["state"] = "removing_item"
            connection = sqlite3.connect("data.db")
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM items")
            rows = cursor.fetchall()
            if not rows:
                self.send_message("No items to remove.", chat_id, CUSTOM_KEYBOARD)
                self.user_state[chat_id]["state"] = "idle"
            else:
                options = [[{"text": row[0]}] for row in rows]
                self.send_message(
                    "Please choose an item to remove:",
                    chat_id,
                    {"keyboard": [*options], "resize_keyboard": True, "input_field_placeholder": "Choose an option"},
                )
            connection.close()
        elif state == "removing_item":
            item_to_remove = text
            connection = sqlite3.connect("data.db")
            cursor = connection.cursor()
            cursor.execute("DELETE FROM items WHERE name = ?", (item_to_remove,))
            connection.commit()
            connection.close()
            self.send_message(f"{item_to_remove} has been removed.", chat_id, CUSTOM_KEYBOARD)
            self.user_state[chat_id]["state"] = "idle"
