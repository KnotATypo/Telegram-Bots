import json
import os

import cv2
import requests

from telegram_bots.bot import Bot

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
        print("Initialising ToolsBot...")
        super().__init__(f"bot{os.getenv("TOOLS_BOT_TOKEN")}", os.getenv("TOOLS_BOT_SECRET"))
        self.state = "idle"
        print("ToolsBot initialised")

    def handle_message(self, data):
        message = data["message"]
        chat_id = message["chat"]["id"]

        if self.state == "idle":
            if message["text"] in STATES:
                self.state = message["text"]
                if self.state == "Power meter":
                    self.send_message("Please send video", chat_id, replay_markup={"remove_keyboard": True})
            else:
                self.send_message("What?", chat_id, replay_markup=CUSTOM_KEYBOARD)
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


def get_power_draw(path: str) -> str:
    vidcap = cv2.VideoCapture(path)

    fps = round(vidcap.get(cv2.CAP_PROP_FPS), 1)
    count = 0
    frames = []
    success, image = vidcap.read()
    while success:
        red_frame = get_red_count(image) > 200  # We consider a blink captured if more than 200 red pixels are detected
        frames.append((red_frame, round(count / fps, 2)))
        success, image = vidcap.read()
        count += 1

    while not frames[0][0]:  # Remove leading non-red frames
        frames.pop(0)

    compressed_frames = [frames[0]]
    for i, f in enumerate(frames[1:], start=1):  # Compress consecutive identical frames
        if frames[i - 1][0] != f[0]:
            compressed_frames.append(f)

    if not compressed_frames[-1][0]:  # compressed_frames needs to end with a red frame
        compressed_frames.pop()

    gap_count = sum([not x[0] for x in compressed_frames])
    elapsed_seconds = compressed_frames[-1][1] - compressed_frames[0][1]

    wh = (3600 * gap_count) / elapsed_seconds
    if wh > 1000:
        return f"{round(wh / 1000, 2)} kW"
    else:
        return f"{round(wh)} W"


def get_red_count(image) -> int:
    """
    Returns the number of red pixels in the image after scaling to 720x1280.

    :param image:
    :return:
    """
    # Extract red channel
    red = image[:, :, 2]

    # Scale image to 720x1280 max
    h, w = red.shape[:2]
    new_w = max(1, int(w * 1 / (w / 720)))
    new_h = max(1, int(h * 1 / (h / 1280)))
    red = cv2.resize(red, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Count pixels above 240 threshold
    _, red = cv2.threshold(red, 240, 255, cv2.THRESH_BINARY)
    num_pass = int(cv2.countNonZero(red))
    return num_pass
