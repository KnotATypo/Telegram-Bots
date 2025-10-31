import json
import os

import cv2
import numpy as np
import requests

from src.bot import Bot

STATES = ["Power meter"]
CUSTOM_KEYBOARD = {
    "keyboard": [[{"text": "Power meter"}]],
    "resize_keyboard": True,
    "input_field_placeholder": "Choose an option",
    "is_persistent": True,
}


class ToolsBot(Bot):
    state: str

    def __init__(self):
        super().__init__(f"bot{os.getenv("TOOLS_BOT_TOKEN")}", os.getenv("TOOLS_BOT_SECRET"))
        self.state = "idle"

    def handle_message(self, data):
        message = data["message"]
        chat_id = message["chat"]["id"]

        if self.state == "idle":
            if message["text"] in STATES:
                self.state = message["text"]
                if self.state == "Power meter":
                    self.send_message("Please send video", chat_id, replay_markup={"remove_keyboard": True})
                return
            else:
                self.send_message("What?", chat_id, replay_markup=CUSTOM_KEYBOARD)
                return
        elif self.state == "Power meter":
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
                return


def get_power_draw(path):
    vidcap = cv2.VideoCapture(path)

    down_sample = 2
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    success, image = vidcap.read()
    count = 0
    red_counts = []
    while success:
        if count % down_sample == 0:
            vidcap.grab()
        else:
            red = image[:, :, 2]
            scale = 0.05
            h, w = red.shape[:2]
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            red = cv2.resize(red, (new_w, new_h), interpolation=cv2.INTER_AREA)
            _, red = cv2.threshold(red, 240, 255, cv2.THRESH_BINARY)
            reds = int(cv2.countNonZero(red))
            red_counts.append(reds)
            success, image = vidcap.read()
        count += 1

    while red_counts[0] == 0:
        red_counts.pop(0)

    start = 0
    gap = True
    gap_sizes = []
    for i, rc in enumerate(red_counts):
        if rc > 0:
            if gap:
                gap_sizes.append(i - start)
                start = i
                gap = False
            continue
        elif rc == 0:
            gap = True
    gap_sizes.pop(0)

    blinks_per_second = 1 / (np.array(gap_sizes) / (fps / down_sample)).mean()
    watts = blinks_per_second * 3600
    if watts > 1000:
        return f"{round(watts / 1000, 2)} kW"
    else:
        return f"{round(watts)} W"
