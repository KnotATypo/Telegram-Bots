# Hassle Bot

<img alt="profile.jpg" height="100" src="profile.png" width="100" style="border-radius: 50%"/>

This bot is designed to hassle the user until its messages are acknowledged. This is intended to be used for
time-sensitive reminders such as medication which can't be easily fulfilled by the Android/Apple default reminders
functionality.

## Features

- Add new tasks to be reminded of
- List tasks
- Remove tasks
- Sending reminders at increasing frequency after set deadline

## Commands

The primary commands for interacting with the bot are implemented through the custom keyboard buttons:

- **Add**: Start the process of adding a new task.
    - The bot will prompt for the task name, then follow up with setting the date and the repeat frequency.
- **List**: View all tasks.
    - The bot will display a list of tasks sorted by their dates along with repeating frequency.
- **Remove**: Remove a task.
    - The bot will provide a list of tasks through the custom keyboard for deletion.

"stop" is also supported by the bot in all states in order to abort the current operation.

## "Hassling"

The bot will initially send a message with the name of the task at the elected time. If this goes unacknowledged, it
will repeat the message after 10 minutes, then at 5 minutes and every 5 minutes after that until acknowledged.

Once acknowledged, the reminders will stop and be rescheduled for the chosen "repeat" time.
