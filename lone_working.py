#!/usr/bin/python3

"""
Lone working system using Telegram messaging system
Copyright 2024 riban ltd <info@riban.co.uk>

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.


Depends on patch to telepot 12.7:
    Edit /usr/local/lib/python3.9/dist-packages/telepot/__init__.py
    Add 'my_chat_member' to list within relay_to_collector()
"""

NOTIFY_INTERVAL = 30 # Interval in minutes between user notifications
REPEAT_INTERVAL = 3 # Interval in minutes between notification repeats
ALERT_COUNT = 3 # Quantity of missed user notifications before alert sent to supervisor
SAVE_FILENAME = '/tmp/riban_loan_working.json'

import telepot # sudo pip3 install telepot
import logging
from time import sleep, monotonic
import json
import signal
import sys
import argparse
import configparser

logging.basicConfig (
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

users = {}
sessions = {}
supervisors = []

def save():
    config = {'users': users, 'sessions': sessions, 'supervisors': supervisors}
    logging.info(config)
    with open(SAVE_FILENAME, 'w') as file:
        json.dump(config, file)


def load():
    global users, sessions, supervisors
    users = {}
    try:
        with open(SAVE_FILENAME, 'r') as file:
            json_obj = json.load(file)
        for id,name in json_obj['users'].items():
            users[int(id)] = name
        sessions = json_obj['sessions']
        # Convert string keys to intergers
        for session in list(sessions):
            sessions[int(session)] = sessions.pop(session)
        supervisors = json_obj['supervisors']
    except:
        pass
    for user in sessions:
        try:
            logging.info(f"Restoring session for user {users[int(user)]}")
        except:
            logging.info(f"Removing session for invalid user {user}")
            try:
                del sessions[int(user)]
            except Exception as e:
                logging.warning(e)
    logging.info(f"Loaded users:{users} supervisors:{supervisors} sessions:{sessions}")


def signal_handler(sig, frame):
    save()
    logging.info("Stopping lone working service")
    sys.exit(0)


def on_telegram(msg):
    global sessions, users, supervisors
    logging.debug(msg)
    if 'chat' in msg:
        end_session = False
        try:
            id = msg['chat']['id']
            if 'new_chat_member' in msg:
                if msg['new_chat_member']['status'] == 'kicked':
                    end_session = True
                    logging.info(f"User {users[id]} removed / blocked bot")
                    #TODO: Notify stakeholders
                else:
                    return
            if end_session or msg['text'] == '/end':
                name = users[id]
                for sup_id in sessions[id]['supervisors']:
                    bot.sendMessage(sup_id, f"{name} has ended monitoring session")
                del sessions[id]
                if not end_session:
                    bot.sendMessage(id, f"🩶 Your session has ended. You are no longer monitored.")
                logging.info(f"Ending monitoring session for user {name}")
            elif msg['text'] == '/start':
                user = bot.getChatMember(id, id)['user']
                # {'user': {'id': 5111001928, 'is_bot': False, 'first_name': 'Catherine', 'language_code': 'en'}, 'status': 'member'}            
                id = user['id']
                first_name = ''
                last_name = ''
                if 'first_name' in user:
                    first_name = user['first_name']
                if 'last_name' in user:
                    last_name = user['last_name']
                name = ' '.join([first_name,last_name])
                users[id] = name
                logging.info(f"Adding new user {id}: {name}")
            elif msg['text'] == '/begin':
                name = users[id]
                sessions[id] = {'last_msg': monotonic(), 'missed':0, 'supervisors':[]}
                sups = ""
                for sup_id in supervisors:
                    sups += f"\n{users[sup_id]}:/{sup_id}"
                bot.sendMessage(id, f"Choose supervisors:{sups}")
                logging.info(f"Starting monitoring session for user {name}")
            elif msg['text'] == '/okay':
                if sessions[id]['missed'] > ALERT_COUNT:
                    logging.info(f"Alert for {users[id]} cleared")
                    for sup_id in sessions[id]['supervisors']:
                        bot.sendMessage(sup_id, f"💚 {users[id]} has responded")
                sessions[id]['missed'] = 0
                sessions[id]['last_msg'] = monotonic()
            elif msg['text'] == '/supervise':
                name = users[id]
                if id not in supervisors:
                    supervisors.append(id)
                    for session_id, session in sessions.items():
                        if id in session['supervisors']:
                            sups = []
                            for sup_id in session['supervisors']:
                                if sup_id in supervisors:
                                    sups.append(users[sup_id])
                            bot.sendMessage(session_id, f"{name} has started supervising. Supervisors: {', '.join(sups)}")
                    bot.sendMessage(id, "You are now registered as a supervisor.")
                else:
                    bot.sendMessage(id, "You are already registered as a supervisor.")
                logging.info(f"Adding supervisor {name}")
            elif msg['text'] == '/unsupervise':
                name = users[id]
                supervisors.remove(id)
                supervising_sessions = []
                for session_id, session in sessions.items():
                    if id in session['supervisors']:
                        sups = []
                        for sup_id in session['supervisors']:
                            if sup_id in supervisors:
                                sups.append(users[sup_id])
                        if sups:
                            bot.sendMessage(session_id, f"{name} has stopped supervising. Remaining supervisors: {', '.join(sups)}")
                        else:
                            bot.sendMessage(session_id, f"⚠️ {name} has stopped supervising. No one supervising!")
                            supervising_sessions.append(users[session_id])
                if supervising_sessions:
                    bot.sendMessage(id, f"⚠️ You have unregistered as a supervisor. {', '.join(supervising_sessions)} unsupervised!")
                else:
                    bot.sendMessage(id, "You have unregistered as a supervisor")
                logging.info(f"Removing supervisor {name}")
            else:
                for sup_id in supervisors:
                    if msg['text'] == f"/{sup_id}" and id not in sessions[id]['supervisors']:
                        sessions[id]['supervisors'].append(sup_id)
                        sups = []
                        for sup in sessions[id]['supervisors']:
                            sups.append(users[sup])
                        bot.sendMessage(id, f"💚 Monitoring session with supervisors: {', '.join(sups)}")
                        bot.sendMessage(sup_id, f"You are now supervising {users[id]}")
        except Exception as e:
            logging.warning(e)
    logging.debug(f"Telegram message: {msg}")


def clear_updates():
    try:
        update = bot.getUpdates()[0]
        id = update['update_id'] + 1
        bot.getUpdates(id)
        logging.info(f"Getting update {id}")
    except:
        pass


logging.info("Starting lone working service")
signal.signal(signal.SIGINT, signal_handler)

parser = argparse.ArgumentParser(
    prog="riban lone working service",
    description="Provides backend for Telegram messaging bot lone working system",
    )
parser.add_argument('-t', '--api_token')
parser.add_argument('-c', '--config')
parser.add_argument('-n', '--notify_interval')
parser.add_argument('-r', '--repeat_interval')
parser.add_argument('-a', '--alert_count')
parser.add_argument('-s', '--save_filename')
args = parser.parse_args()

if args.config is not None:
    config_fn = args['config']
else:
    config_fn = '/etc/riban_lone_working.conf'


config = configparser.ConfigParser()
try:
    config.read(config_fn)
    if 'Default' in config:
        if 'API_TOKEN' in config['Default']:
            API_TOKEN = config['Default']['API_TOKEN']
        if 'NOTIFY_INTERVAL' in config['Default']:
            NOTIFY_INTERVAL = config['Default']['NOTIFY_INTERVAL']
        if 'REPEAT_INTERVAL' in config['Default']:
            REPEAT_INTERVAL = config['Default']['REPEAT_INTERVAL']
        if 'ALERT_COUNT' in config['Default']:
            ALERT_COUNT = config['Default']['ALERT_COUNT']
        if 'SAVE_FILENAME' in config['Default']:
            SAVE_FILENAME = config['Default']['SAVE_FILENAME']
except:
    logging.warning(f"Cannot read config from {config_fn}")

if args.api_token is not None:
    API_TOKEN = args.api_token
if args.notify_interval is not None:
    NOTIFY_INTERVAL = int(args.notify_interval)
if args.repeat_interval is not None:
    REPEAT_INTERVAL = int(args.repeat_interval)
if args.alert_count is not None:
    ALERT_COUNT = int(args.alert_count)
if args.save_filename is not None:
    SAVE_FILENAME = args.save_filename

try:
    bot = telepot.Bot(API_TOKEN)
    bot.getUpdates(offset=-1)
    bot.message_loop(on_telegram)
except:
    logging.info("Failed to configured telegram client")

logging.info(f"Interval between user notification: {NOTIFY_INTERVAL} minutes")
logging.info(f"Interval between repeat notification: {REPEAT_INTERVAL} minutes")
logging.info(f"Quantity of notifications before alert: {ALERT_COUNT}")
logging.info(f"Filename of persistent data: {SAVE_FILENAME}")
# Load last session and attempt to restart sessions
load()
"""
for user in users:
    try:
        bot.sendMessage(user, "/start")
    except Exception as e:
        logging.warning(e)
for supervisor in supervisors:
    try:
        bot.sendMessage(supervisor, "/supervise")
    except Exception as e:
        logging.warning(e)
for session in sessions:
    try:
        bot.sendMessage(session, "/begin")
    except Exception as e:
        logging.warning(e)
"""

while True:
    sleep(60)
    for id, config in sessions.items():
        time_delta = int((monotonic() - config['last_msg']) / 60) - NOTIFY_INTERVAL
        logging.info(time_delta)
        if time_delta >= 0 and time_delta % REPEAT_INTERVAL == 0:
            try:
                # Send user notifications every NOTIFY_INTERVAL minutes then every REPEAT_INTERVAL until acknowledged
                if config['missed'] == 0:
                    bot.sendMessage(id, "💚 Are you /okay?")
                elif config['missed'] < ALERT_COUNT:
                    bot.sendMessage(id, "🧡 Are you /okay?")
                elif sessions[id]['supervisors']:
                    bot.sendMessage(id, "❤️ Alert sent to supervisors! Are you /okay?")
                    # Send supervisor notification every 5 minutes after user has failed to acknowlege 5 consecutive 1-minute notifications
                    for sup_id in config['supervisors']:
                        sleep(1)
                        bot.sendMessage(sup_id, f"⚠️ ALERT: {users[id]} has not responded!")
                        logging.info(f"ALERT for user {users[id]} sent to {users[sup_id]}")
                else:
                    bot.sendMessage(id, "❤️ Are you /okay?")
                config['missed'] += 1
            except Exception as e:
                logging.warning(e)
                bot.getUpdates(offset=-1)

save()
