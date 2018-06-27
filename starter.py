import os
import time
import re
from slackclient import SlackClient
import random
from sutime import SUTime
import json
import argparse
import calendar_integration

jar_files = os.path.join(os.path.dirname(__file__), 'jars')
sutime = SUTime(jars=jar_files, mark_time_ranges=True)

SOCKET_DELAY = 1
SLACK_NAME = os.environ.get('SLACK_AUTH_NAME')
SLACK_TOKEN = os.environ.get('SLACK_AUTH_TOKEN')
SLACK_ID = None
slack_client = SlackClient(SLACK_TOKEN)

is_ok = slack_client.api_call('channels.list')
if(is_ok):
    for user in slack_client.api_call("users.list").get('members'):
        if user.get('name') == SLACK_NAME:
            SLACK_ID = user.get('id')

def is_private(event):
    return event.get('channel').startswith('D')

def get_mention(user):
    return '<@{user}>'.format(user=user)


def is_for_me(event):
    type = event.get('type')
    if type and type == 'message' and not(event.get('user')==SLACK_ID):
        if is_private(event):
                return True
            # in case it is not a private message check mention
        text = event.get('text')
        if get_mention(SLACK_ID) in text.strip().split():
            return True

def is_hi(message):
    tokens = [t.lower() for t in message.strip().split()]
    return any(g in tokens for g in ["meet", "meeting", "catch up", "1 on 1"])

def is_summary(message):
    tokens = [t.lower() for t in message.strip().split()]
    return any(g in tokens for g in ["summary"])

def handle_message(message, user, channel):
    if is_summary(message):
        summary = get_total_meeting_time_today()
        post_message("You have spent a total of " + str(summary) + "hours today in meetings", channel = channel)
    if is_hi(message):
        parse_message(message)
        post_message('Done, I have created a calendar event', channel)
    
        

def create_calendar_event(cal, emails, body):
    service = calendar_integration.init_calendar()
    begin = cal['date'] + cal['begin'] + ":00"
    end = cal['date'] + cal['end'] + ":00"
    calendar_integration.create_calendar_event(service, begin, end, persons = emails, event_body = body)

def get_total_meeting_time_today():
    service = calendar_integration.init_calendar()
    total_duration = calendar_integration.get_calendar_events(service)
    return total_duration


def post_message(message, channel):
    slack_client.api_call('chat.postMessage', text=message, channel = channel, as_user = True)

def get_emails(attendee):
    user_json = slack_client.api_call('users.info', user=attendee)
    return user_json['user']['profile']['email']

def run():
    if slack_client.rtm_connect(with_team_state=False):
        while True:
            event_list = slack_client.rtm_read()
            if len(event_list) > 0:
                for event in event_list:
                    if is_for_me(event):
                        text = (event.get('text'))
                        handle_message(message = text, user = event.get('user'), 
                                        channel = event.get('channel'))
                        time.sleep(SOCKET_DELAY)
    else:
        print("Socket connection failed")

def get_names(attendee):
    user_json = slack_client.api_call('users.info', user=attendee)
    return user_json['user']['profile']['real_name']

def parse_calendar_time(message):
    result = json.loads(json.dumps(sutime.parse(message), sort_keys=True, indent=4))
    print(result)
    cal = {}
    for r in result:
        if r['type'] == 'DATE':
            cal['date'] = r['value']
        if r['type'] == 'DURATION':
            if 'begin' in r['value']:
                cal['begin'] = r['value']['begin']
                cal['end'] = r['value']['end']
    return cal

def parse_message(message):
    attendees = [t[2:-1] for t in message.strip().split() if t.startswith('<@') and SLACK_ID not in t]
    print("Attendees {}".format(attendees))
    for a in attendees:
            post_message(message = 'You have a meeting request', channel = a)
    emails = [get_emails(a) for a in attendees]
    names = [get_names(a) for a in attendees]
    #For testing
    #emails = ['pradeep@callindra.com']
    #names = ['Pradeep Ban']
    cal = parse_calendar_time(message)
    cal_descr = 'Meeting with ' + ''.join(names)
    create_calendar_event(cal, emails, cal_descr)


if __name__ == "__main__":
    print("start")
    run()
    #parse_message("Setup a meeting with Pradeep tomorrow from 10AM to 11AM")
    
