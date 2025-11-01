import atexit
import os
import sqlite3
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from typing import Dict

from apscheduler.schedulers.background import BackgroundScheduler

from telegram_bots.bot import Bot

CUSTOM_KEYBOARD = {
    "keyboard": [[{"text": "Add"}, {"text": "List"}, {"text": "Remove"}]],
    "resize_keyboard": True,
    "input_field_placeholder": "Choose an option",
    "is_persistent": True,
}


class ExpiryBot(Bot):
    user_state: Dict[str, Dict[str, str]]
    sched: BackgroundScheduler
    db_path: str

    def __init__(self):
        print("Initialising ExpiryBot...")
        super().__init__(f"bot{os.getenv("EXPIRY_BOT_TOKEN")}", os.getenv("EXPIRY_BOT_SECRET"))
        self.user_state = defaultdict(lambda: {"state": "idle", "item": None})
        self.sched = BackgroundScheduler(daemon=True)
        self.db_path = os.path.join(os.path.dirname(__file__), "data.db")

        with self.db_cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS items (name TEXT, date TEXT)")
            cursor.execute("CREATE TABLE IF NOT EXISTS users (chat_id TEXT UNIQUE)")

        self.sched.add_job(self._send_notifications, "cron", hour=10, minute=0)
        self.sched.start()
        atexit.register(lambda: self.sched.shutdown())

        print("ExpiryBot initialised")

    def _send_notifications(self):
        with self.db_cursor() as cursor:
            cursor.execute("SELECT name, date FROM items")
            rows = cursor.fetchall()
            cursor.execute("SELECT chat_id FROM users")
            users = cursor.fetchall()
        today = datetime.now().date()
        for row in rows:
            item_name = row[0]
            expiration_date = datetime.strptime(row[1], "%Y-%m-%d").date()
            for chat_id in users:
                if expiration_date == today:
                    self.send_message(f"{item_name} will expire today", chat_id)
                elif expiration_date == today.replace(day=today.day + 1):
                    self.send_message(f"{item_name} will expire tomorrow", chat_id)

    def handle_message(self, data):
        text = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]
        with self.db_cursor() as cursor:
            cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
        state = self.user_state[chat_id]["state"]

        if text == "stop":  # Catch-all to reset state
            self.user_state[chat_id]["state"] = "idle"
            self.user_state[chat_id]["item"] = None
            self.send_message("Operation cancelled.", chat_id, CUSTOM_KEYBOARD)
        elif text == "Add" and state == "idle":  # Start adding an item
            self.user_state[chat_id]["state"] = "adding_item"
            self.send_message("Please provide the item to add:", chat_id, {"remove_keyboard": True})
        elif state == "adding_item":  # Got item name, now ask for date
            self.user_state[chat_id]["state"] = "adding_date"
            self.user_state[chat_id]["item"] = text
            self.send_message("Please provide the expiration date (DD/MM):", chat_id)
        elif state == "adding_date":  # Got date, validate and store
            self._save_item(text, chat_id)
        elif text == "List" and state == "idle":  # List items
            self._send_list(chat_id)
        elif text == "Remove" and state == "idle":  # Start removing an item by showing options
            self._send_remove_options(chat_id)
        elif state == "removing_item":  # Remove selected item
            item_to_remove = text
            with self.db_cursor() as cursor:
                cursor.execute("DELETE FROM items WHERE name = ?", (item_to_remove,))
            self.send_message(f"{item_to_remove} has been removed.", chat_id, CUSTOM_KEYBOARD)
            self.user_state[chat_id]["state"] = "idle"

    def _send_list(self, chat_id):
        with self.db_cursor() as cursor:
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

    def _send_remove_options(self, chat_id):
        self.user_state[chat_id]["state"] = "removing_item"
        with self.db_cursor() as cursor:
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

    def _save_item(self, date, chat_id):
        if "/" not in date:
            self.send_message("Invalid date format. Please provide the expiration date in DD/MM format:", chat_id)
            return
        day = date.split("/")[0]
        month = date.split("/")[1]
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
        with self.db_cursor() as cursor:
            cursor.execute("INSERT INTO items (name, date) VALUES (?, ?)", (self.user_state[chat_id]["item"], date))
        self.send_message(f"{self.user_state[chat_id]['item']} will expire on {date}", chat_id, CUSTOM_KEYBOARD)
        self.user_state[chat_id]["state"] = "idle"
        self.user_state[chat_id]["item"] = None

    @contextmanager
    def db_cursor(self):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        yield cursor
        connection.commit()
        connection.close()
