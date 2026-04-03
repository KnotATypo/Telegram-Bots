import enum
from datetime import datetime
from typing import Dict


class StateManager:
    possible_states: enum.Enum
    user_states: Dict[int, enum.Enum]

    def __init__(self, states):
        self.user_states = {}
        self.possible_states = states

    def set_state(self, chat_id, state):
        if state not in self.possible_states:
            raise ValueError(f"Invalid state: {state}\nPossible states: {self.possible_states}")
        self.user_states[chat_id] = state

    def __setitem__(self, chat_id, state):
        self.set_state(chat_id, state)

    def get_state(self, chat_id):
        return self.user_states.get(chat_id, None)

    def __getitem__(self, chat_id):
        return self.get_state(chat_id)

    def clear_state(self, chat_id):
        if chat_id in self.user_states:
            del self.user_states[chat_id]

    def __delitem__(self, chat_id):
        self.clear_state(chat_id)


def get_future_year(day: int, month: int) -> int:
    year = datetime.now().year
    if month < datetime.now().month or (month == datetime.now().month and day < datetime.now().day):
        year += 1
    return year
