import cv2


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

    # Count pixels above threshold 240
    _, red = cv2.threshold(red, 240, 255, cv2.THRESH_BINARY)
    num_pass = int(cv2.countNonZero(red))
    return num_pass
