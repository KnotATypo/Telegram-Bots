import enum
from typing import Dict


class StateManager:
    possible_states: enum.Enum
    user_states: Dict[int, enum.Enum]

    def __init__(self, states):
        self.user_states = {}
        self.possible_states = states

    def set_state(self, user_id, state):
        if state not in self.possible_states:
            raise ValueError(f"Invalid state: {state}\nPossible states: {self.possible_states}")
        self.user_states[user_id] = state

    def get_state(self, user_id):
        return self.user_states.get(user_id, None)

    def clear_state(self, user_id):
        if user_id in self.user_states:
            del self.user_states[user_id]
