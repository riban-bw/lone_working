# lone_working
Telegram messenger bot lone working service

# About

This Python script acts as the background service to implement a lone-working user check system. Users start a session and receive notifications (by default every 30 minutes) to which they should respond. If a user does not respond, they receive further notifications (by default 4) at a different interval (by default 3 minutes). If they still do not respond then the list of users supervising the session will start to receive alerts at the repeat interval (by default 3 minutes). If the user acknowledges the notification then alerts cease. The user can end the session to stop notifications.

# Build

The system consists of two parts:

- Telegram bot
- Python service script

The Telegram bot is a simple bot, configured as described in the [Telegram bot instructions](https://core.telegram.org/bots). The bot's API token is required by the Python script. The only configuration for the bot is to add commands:

/begin
/end
/supervise
/unsupervise
