# Tools Bot

<img alt="profile.jpg" height="100" src="profile.png" width="100" style="border-radius: 50%"/>

The bot provides various simple utilities, a toolbox if you will. These are miscellaneous features that don't fit into
any category but are useful on their own (to me at least).

## Features

- **Power meter**: Consumes a video of a power meter with a blinking indicator for power consumption and returns the
  power
  consumption rate.
    - This works with power meters with a red LED that blinks at 1Wh per impulse.
- **Check estimate**: Takes an estimated time and checks it against the actual time taken to perform an operation.
    - Useful for checking time estimates for tasks such as software builds or cooking.
- **Occupancy**: Manually record and retrieve occupancy of a location.
    - Designed with a gym in mind, but can be used for any location where occupancy tracking is useful.

## Commands

The primary command for interacting with the bot is implemented through the custom keyboard buttons:

- Power meter: Start the process of analyzing a power meter video.
    - The bot will prompt for a video file of the power meter.
- Check estimate: Start the process of checking an estimated time.
    - The bot will prompt for an estimated time in minutes. The estimate can be later checked against the actual time
      taken by sending "done" when the operation is complete.
- Occupancy: Record or retrieve occupancy information.
    - The bot will prompt for the current occupancy number or a day to retrieve occupancy for.

## Descriptions and Motivation/Use Cases

The Tools Bot is designed to provide quick access to a variety of utility functions that aren't already solved by easily
accessible tools such as calculators, timers or unit converters. The motivation behind this bot is to have a single
point of access for these miscellaneous tools, making it convenient for users (me) to perform tasks without needing to
switch between different applications or services.

### Power Meter

Many power meters these days are "smart" in that they can report power consumption digitally which can be accessed via
an app or web interface. However, some older models still use only a blinking LED to indicate power draw, meaning it can
be difficult to monitor instantaneous power consumption across the whole household.

This can be calculated by hand with a stopwatch and a tally counter, but it's tedious. The bot automates this process by
analyzing a video of the power meter, counting the LED blinks, and calculating the power consumption rate based on the
elapsed time and the number of blinks similar to how a human would do it.

**NOTE**: *The accuracy of this method depends on the quality of the video and the visibility of the LED indicator. My
power meter is in a very dark location, so the LED is quite visible in the video. In brighter environments, you may have
to fiddle with the thresholds for detecting what constitutes a "blink".*

My personal use case for this feature is relatively limited as I primarily rely on individually monitored smart plugs
for my high-power devices. However, some devices such as my electric water heater, electric oven and air conditioner are
wired directly into the mains, so I can't monitor their power consumption easily. Turning these devices on and taking a
measurement from the power meter allows me to estimate their power consumption.
Additionally, it can be useful for understanding baseline household power consumption when all high-power devices are
off.

### Check Estimate

Whether is it cooking a meal or building software, it's often useful to have an estimate of how long a task will take.
However, I often find my estimates can be pretty inaccurate. This allows me to track how accurate my estimates are.
Honestly, the utility of this feature is pretty dubious as a timer app would do the same job, but having the percentage
error calculated for me is a nice touch.

### Occupancy

I am the type of person who likes to go to the gym during off-peak hours to avoid crowds. However, it's not always easy
to know how busy the gym will be at a given time. Google Maps provides some occupancy data, but I find it to be very
inaccurate at my local gym.

This feature allows me to manually track the occupancy of my gym at different times and days. By recording the number of
people present when I arrive, I can build up a dataset over time that helps me identify patterns in gym occupancy.
Currently, the data is only output in a raw count format, but I may add more advanced analytics in the future using some
basic statistical analysis or machine learning techniques to predict busy times based on historical data.

This concept is easily extended to other locations where occupancy tracking is useful, such as libraries or a workshop,
however the utility very quickly diminishes as the location becomes less frequented or the number of visitors becomes 
higher than can be easily counted.