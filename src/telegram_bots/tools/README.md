# Tools Bot

<img alt="profile.jpg" height="100" src="profile.png" width="100" style="border-radius: 50%"/>

The bot provides various simple utilities, a toolbox if you will. Currently, it only supports a single feature.

## Features

- Power meter: Consumes a video of a power meter with a blinking indicator for power consumption and returns the power
  consumption rate.
    - This works with power meters with a red LED that blinks at 1Wh per impulse.

## Commands

The primary command for interacting with the bot is implemented through the custom keyboard buttons:

- Power meter: Start the process of analyzing a power meter video.
    - The bot will prompt for a video file of the power meter.