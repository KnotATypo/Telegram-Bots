import atexit
import enum
from datetime import datetime
from typing import Dict, Tuple

from apscheduler.schedulers.background import BackgroundScheduler

from telegram_bots import util
from telegram_bots.bot import DatabaseBot
from telegram_bots.logger import logger


class States(enum.Enum):
    ADD_TASK = "add_task"
    SET_DATE = "set_date"
    SET_REPEAT = "set_repeat"
    REMOVE_TASK = "remove_task"


CUSTOM_KEYBOARD = {
    "keyboard": [[{"text": "Add"}, {"text": "List"}, {"text": "Remove"}]],
    "resize_keyboard": True,
    "input_field_placeholder": "Choose an option",
    "is_persistent": True,
}


def _parse_date(date_text: str) -> datetime | None:
    timestamp = date_text.split(" ")
    try:
        month = int(timestamp[0].split("-")[0])
        assert 1 <= month <= 12
        day = int(timestamp[0].split("-")[1])
        assert 1 <= day <= 31
        hour = int(timestamp[1].split(":")[0])
        assert 0 <= hour <= 23
        minute = int(timestamp[1].split(":")[1])
        assert 0 <= minute <= 59
    except (ValueError, AssertionError):
        return None
    year = util.get_future_year(day, month)
    return datetime(year, month, day, hour, minute)


class HassleBot(DatabaseBot):
    state_manager: util.StateManager = util.StateManager(States)
    sched: BackgroundScheduler
    task_buffer: Dict[str, Tuple[str, datetime]]

    def __init__(self, bot_token: str, bot_secret: str):
        logger.debug("Initialising HassleBot...")
        super().__init__(f"bot{bot_token}", bot_secret)

        self.task_buffer = {}

        self.sched = BackgroundScheduler(daemon=True)
        self.sched.start()
        atexit.register(lambda: self.sched.shutdown())

        with self.db_cursor() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS tasks_hassle (name TEXT, alert_time TEXT, repeat TEXT, chat_id TEXT)"
            )
            cursor.execute("CREATE TABLE IF NOT EXISTS users_hassle (chat_id TEXT UNIQUE)")

        logger.info("HassleBot initialised")

    def handle_message(self, data):
        text: str = data["message"]["text"]
        chat_id = str(data["message"]["chat"]["id"])

        with self.db_cursor() as cursor:
            cursor.execute("SELECT chat_id FROM users_hassle")
            users = cursor.fetchall()
            if (chat_id,) not in users:
                cursor.execute("INSERT INTO users_hassle (chat_id) VALUES (?)", (chat_id,))
                self.send_message(
                    "Welcome to HassleBot! Use the keyboard below to manage your task.\n\n"
                    "HassleBot will hassle you (when you tell it to) about tasks you create until you clear them.",
                    chat_id,
                    CUSTOM_KEYBOARD,
                )
                return

        chat_state = self.state_manager[chat_id]
        if text.lower() == "stop":
            self.send_message("Stopped", chat_id, CUSTOM_KEYBOARD)
            del self.state_manager[chat_id]
        elif chat_state is None:  # User has no ongoing operation
            if text == "Add":
                self.send_message("Provide the name of the task.", chat_id, {"remove_keyboard": True})
                self.state_manager[chat_id] = States.ADD_TASK
            elif text == "Remove":
                if self._send_remove_options(chat_id):
                    self.state_manager[chat_id] = States.REMOVE_TASK
            elif text == "List":
                self._send_list(chat_id)
        elif chat_state == States.ADD_TASK:
            self.state_manager[chat_id] = States.SET_DATE
            self.task_buffer[chat_id] = (text,)
            self.send_message("Please provide a time for the alert in the format MM-DD HH:MM.", chat_id)
        elif chat_state == States.SET_DATE:
            if (date := _parse_date(text)) is None:
                self.send_message("Invalid date. Please provide in MM-DD HH:MM format.", chat_id)
                return
            self.task_buffer[chat_id] = (self.task_buffer[chat_id][0], date)
            self.send_message(
                "How often should this task repeat?",
                chat_id,
                {
                    "keyboard": [[{"text": "Never"}, {"text": "Daily"}, {"text": "Weekly"}]],
                    "resize_keyboard": True,
                    "input_field_placeholder": "Choose an option",
                    "is_persistent": True,
                },
            )
            self.state_manager[chat_id] = States.SET_REPEAT
        elif chat_state == States.SET_REPEAT:
            if text not in ["Never", "Daily", "Weekly"]:
                self.send_message("Selection invalid. Try again.", chat_id)
                return
            name, date = self.task_buffer[chat_id]
            with self.db_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO tasks_hassle (name, alert_time, repeat, chat_id) VALUES (?, ?, ?, ?)",
                    (name, date, text, chat_id),
                )
            self.send_message(
                f'Created task "{name}". This task will alert at {date} and repeat {text.lower()}', chat_id
            )
            del self.state_manager[chat_id]
        elif chat_state == States.REMOVE_TASK:
            with self.db_cursor() as cursor:
                cursor.execute("SELECT * FROM tasks_hassle WHERE chat_id = ? AND name = ?", (chat_id, text))
                if len(cursor.fetchall()) == 0:
                    self.send_message("Item not found.", chat_id, CUSTOM_KEYBOARD)
                else:
                    cursor.execute("DELETE * FROM tasks_hassle WHERE chat_id = ? AND name = ?", (chat_id, text))
                    self.send_message(f'Task "{text}" deleted', chat_id, CUSTOM_KEYBOARD)
            del self.state_manager[chat_id]

    def _send_remove_options(self, chat_id) -> bool:
        with self.db_cursor() as cursor:
            cursor.execute("SELECT name FROM tasks_hassle WHERE chat_id = ?", (chat_id,))
            rows = cursor.fetchall()

        if not rows:
            self.send_message("No items to remove.", chat_id, CUSTOM_KEYBOARD)
            return False
        else:
            options = [[{"text": row[0]}] for row in rows]
            self.send_message(
                "Please choose a task to remove:",
                chat_id,
                {"keyboard": [*options], "resize_keyboard": True, "input_field_placeholder": "Choose an option"},
            )
            return True

    def _send_list(self, chat_id):
        with self.db_cursor() as cursor:
            cursor.execute("SELECT name, alert_time, repeat FROM tasks_hassle WHERE chat_id = ?", (chat_id,))
            rows = cursor.fetchall()
        if not rows:
            self.send_message("No tasks found.", chat_id, CUSTOM_KEYBOARD)
        else:
            rows.sort(key=lambda x: datetime.strptime(x[1], "%Y-%m-%d %H:%M"))
            message = "Tasks:\n"
            for row in rows:
                message += f'- "{row[0]}" will alert at {row[1]} and repeat {row[2]}\n'
            self.send_message(message, chat_id, CUSTOM_KEYBOARD)
