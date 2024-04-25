# riban lone working
Telegram messenger bot lone working service

# About

There are risks involved when someone must work alone or as part of a team in dangerous locations. This system provides a mechanism to monitor such situations and reduce the risk of lone-working. Users start a session and receive notifications (by default every 30 minutes) to which they should respond. If a user does not respond, they receive further notifications (by default 3) at a different interval (by default 4 minutes). If they still do not respond then the list of users supervising the session will start to receive alerts at the repeat interval (by default 4 minutes). If the user acknowledges the notification then alerts cease. The user can end the session to stop notifications.

# User Guide

There are two types of user:

- Monitored user - A person working alone that needs to check in regularly to ensure they remain healthy and safe
- Supervisor - A person who will be notified if a monitored user has failed to check in

There may be any quantity of monitored users and supervisors and each monitored user can select any quantity of available supervisors for their monitored session.

## Monitored User Workflow

### First time configuration
- Install Telegram App on mobile device (Android phone, iPhone, etc.)
- Create Telegram account and log in on mobile device
- Start chat with bot (system admin should provide bot name)
- Press `START` button to start the bot connection
- Change the notification sound for the chat to be destinctive:
  - Press _hamburger_ menu
  - Select "Mute"
  - Select "Customize"
  - Select "Sound"
  - Choose distinctive sound - it is recommended this is loud and long to avoid missing notifications
### Each lone working session
Within the lone working chat in Telegram:
- Press `Start monitored session (/begin)` option in menu - you should receive a notification listing available supervisors
- Press the numeric link next to each supervisor you wish to add to the session - you should receive a notification after each supervisor is added, listing the supervisors monitoring the session
- Periodically a `💚 Are you /okay?` notification will be sent to the chat - press the `/okay` link in the message or the `/okay` menu option to acknowledge the notification
- The `🧡 Are you /okay?` notification will repeat periodically (every 4 minutes by default) until acknowledged. Note the repeated messages have an orange heart.
- After a number of repeated notifications (3 times by default) you will start to receive `❤️ Alert sent to supervisors! Are you /okay?` notifications which will continue at the same repeat rate until you acknowledge
- If there are no supervisors available the red heart messages will just say, `❤️ Are you /okay?`
- You will receive a message if a user that is supervising your session logs off - This will include an alert indication if there are no more users supervising your session
- Press `Start monitored session (/begin)` to see list of available supervisors and list those supervising your session - this does not effect the current session
- Press `End monitored session (/end)` to end the monitored session - all users supervising the session receive a notification that the session has ended

## Supervisor Workflow
### First time configuration
- Install Telegram App on mobile device (Android phone, iPhone, etc.)
- Create Telegram account and log in on mobile device
- Start chat with bot (system admin should provide bot name)
- Press `START` button to start the bot connection
- Change the notification sound for the chat to be destinctive:
  - Press _hamburger_ menu
  - Select "Mute"
  - Select "Customize"
  - Select "Sound"
  - Choose distinctive sound - it is recommended this is loud and long to avoid missing notifications
### Each lone working session
Within the lone working chat in Telegram:
- Press `Start supervising (/supervise)` option in menu - you should receive a notification confirming you are now a supervisor (or that you were already logged in as a supervisor)
- Press `List sessions (/sessions)` menu option to list active sessions - you can select a session id from the list to start or stop supervising that session
- You will receive a notification when a user adds you to a monitored session
- You will receive an `⚠️ ALERT: <user's name> has not responded! /handle_xxxxxx` alert if a user has failed to acknowledge several notifications (default 46 minutes since last acknowledgement) - This will repeat until the user acknowledges their alert (default every 4 minutes)
- Press the `/handle` link to notify all supervising users that you are responding to the alert
- Press `Stop supervising (/unsupervise)` to log out and stop monitoring any sessions - any users that you are supervising will be notified that you have stopped supervising them

# Build

The system consists of two parts:

- Telegram bot
- Python service script

The Telegram bot is a simple bot, configured as described in the [Telegram bot instructions](https://core.telegram.org/bots). The bot's API token is required by the Python script. The only configuration for the bot is to add commands:

```
begin - Start a monitored user session
end - End a monitored user session
supervise - Start supervising
unsupervise - End supervising
sessions - List active sessions
```
The Python script (hosted in this git repository) needs to be run on an Internet connected host. It is tested on Debian 10 Bullseye on Raspberry Pi 4 but should work on most platforms supporting Python 3 and the dependencies.

## Dependencies

The script is written in Python 3 and requires some Python modules as listed below. These may be provided as OS distribution packages or may require to be installed via PIP.

- teleport
- configparser
- argparse
- json
- logging
- time
- signal
- sys

The teleport module version 12.7 does not handle some Telegram bot messages. The work around for this is to add `'my_chat_member'` to the list of keys handled by the function `relay_to_collector` in __init__.py, e.g.:
```
        def relay_to_collector(update):
            key = _find_first_key(update, ['message',
                                           'edited_message',
                                           'channel_post',
                                           'edited_channel_post',
                                           'callback_query',
                                           'inline_query',
                                           'chosen_inline_result',
                                           'shipping_query',
                                           'pre_checkout_query',
                                           'my_chat_member'])
            collect_queue.put(update[key])
            return update['update_id']
```
on the Debian test machine this file is found here: `/usr/local/lib/python3.9/dist-packages/telepot/__init__.py`. This is a bit of a bodge that is prone to be overwritten by updates but it solves the problem.

# Running the service

The Python script `lone_working.py` can be run without elevated rights. It must be given the Telegram bot API token either as a command line parameter or reading from a configuration file. By default it looks for a configuration file `/etc/riban_lone_working.conf` which is an ini style configuration file with one section `[Default]':

```
[Default]
API_TOKEN = "API_TOKEN_AS_A_STRIG" # The Telegram bot API token
NOTIFY_INTERVAL = 30 # Interval in minutes between user notifications
REPEAT_INTERVAL = 3 # Interval in minutes between notification repeats
ALERT_COUNT = 3 # Quantity of missed user notifications before alert sent to supervisor
SAVE_FILENAME = '/tmp/riban_loan_working.json'
```

Command line parameters in short or long form can be provided for the following options:

```
-t --api_token : Telegram API token
-c --config : Full path and filename of configuration file [Default: /etc/riban_lone_working.conf]
-n, --notify_interval : Interval (in minutes) between user notifications [Default: 30]
-r, --repeat_interval : Interval (in minutes) beteween notification repeat [Default: 4]
-a, --alert_count : Quantity of notifications before an alert is sent [Default: 3]
-s, --save_filename : Full path and filename of persistent state save file [Default: /tmp/riban_loan_working.json]
```

If the service is stopped, e.g. with ctrl+c, it saves its current list of users, supervisors and sessions. When it restarts it restores these.

# Defects and enhancements
Please use issue tracker to report bugs an feature requests. Feel free to submit pull requests to resolve any bugs or implement new features. Add comments to the issue tracker to advance the discussion of such issues.
All known issues have been entered into the issue tracker.
