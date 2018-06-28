import os
import time
import re
from slackclient import SlackClient
import random
from sutime import SUTime
import json
import argparse
import calendar_integration
import isodate, dateutil.parser

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
    """
    Check if the incoming message is addressed to the bot
    @params: message - The raw slack message
    @return: boolean
    """
    type = event.get('type')
    if type and type == 'message' and not(event.get('user')==SLACK_ID):
        if is_private(event):
                return True
            # in case it is not a private message check mention
        text = event.get('text')
        if get_mention(SLACK_ID) in text.strip().split():
            return True

def is_meeting(message):
    """
    A crude hack to check for words related to meetings
    @params: message - Incoming slack messsage
    @returns: boolean - If the message contains any of the meeting related keywords
    """
    tokens = [t.lower() for t in message.strip().split()]
    return any(g in tokens for g in ["meet", "meeting", "catch up", "1 on 1"])

def is_summary(message):
    """
    A crude hack to check for word summary
    @params: message - Incoming slack messsage
    @returns: boolean
    """
    tokens = [t.lower() for t in message.strip().split()]
    return any(g in tokens for g in ["summary"])

def handle_message(message, channel):
    """
    To handle messages. This is a very simple 1 level handshake. Checks for the presence of summary and meetings
    and handles accordingly
    @params: message - incoming message
    @params: channel - Slack channel id
    @returns None
    """
    if is_summary(message):
        summary = get_total_meeting_time_today()
        post_message("You have a total of " + str(summary) + " hours today in meetings", channel = channel)
    if is_meeting(message):
        parse_message(message)
        post_message('Done, I have created a calendar event', channel)

def create_calendar_event(cal, emails, body):
    """
    Helper method to create calendar event
    @params: cal - Dictionary containing the calendar begin and end times
    @params: emails - list of email addresses of attendees
    @params: body - Calendar event description
    @returns None
    """
    try:
        service = calendar_integration.init_calendar()
        begin = cal['date'] + cal['begin'] + ":00"
        end = cal['date'] + cal['end'] + ":00"
        calendar_integration.create_calendar_event(service, begin, end, persons = emails, event_body = body)
    except Exception as e:
        print(e)

def get_total_meeting_time_today():
    """
    Helper method to get the total time spent in meetings per day
    @return: Total duration in hours
    """
    service = calendar_integration.init_calendar()
    total_duration = calendar_integration.get_calendar_events(service)
    return total_duration

def post_message(message, channel):
    slack_client.api_call('chat.postMessage', text=message, channel = channel, as_user = True)

def get_emails(attendee):
    user_json = slack_client.api_call('users.info', user=attendee)
    return user_json['user']['profile']['email']

def run():
    """
    Main method to run the slack bot. Runs in an infinite loop and listens for requests with a 1 second break
    Terribly inefficient and hogs CPU
    """
    if slack_client.rtm_connect(with_team_state=False):
        while True:
            event_list = slack_client.rtm_read()
            if len(event_list) > 0:
                for event in event_list:
                    if is_for_me(event):
                        text = (event.get('text'))
                        handle_message(message = text, channel = event.get('channel'))
                        time.sleep(SOCKET_DELAY)
    else:
        print("Socket connection failed")

def get_names(attendee):
    """
    Helper transform method to get the Full name of the attendee
    """
    user_json = slack_client.api_call('users.info', user=attendee)
    return user_json['user']['profile']['real_name']

def parse_calendar_time(message):
    """
    Main method to parse the message for time duration strings. Uses sutime.
    @params: message - incoming message
    @return: cal - A dictionary containing the start and end times
    """
    result = json.loads(json.dumps(sutime.parse(message), sort_keys=True, indent=4))
    print(result)
    cal = {}
    # Many checks to match SuTime's rendering of dates. Here's a sample
    #[{'end': 34, 'start': 19, 'text': 'tonight at 10PM', 'type': 'TIME', 'value': '2018-06-28T22:00'}, 
    # {'end': 45, 'start': 39, 'text': '1 hour', 'type': 'DURATION', 'value': 'PT1H'}]
    for r in result:
        if 'DATE' in r['type']:
            cal['date'] = r['value']
        if 'DURATION' in r['type']:
            if 'begin' in r['value']:
                cal['begin'] = r['value']['begin']
                cal['end'] = r['value']['end']
            else:
                #Begin is already present in 'TIME' variable. Have to get the duration value
                #and add to the begin variable. This is real messy.
                duration_ = isodate.parse_duration(r['value'])
                cal['end'] = 'T' + (dateutil.parser.parse(cal['begin']) + duration_).strftime('%H:%M')
        if 'TIME' in r['type']:
            d = r['value'].split('T')[0]
            t = r['value'].split('T')[1]
            cal['date'] = d
            cal['begin'] = 'T' + t

    return cal

def parse_message(message):
    try:
        attendees = [t[2:-1] for t in message.strip().split() if t.startswith('<@') and SLACK_ID not in t]
        cal = parse_calendar_time(message)
        for a in attendees:
                post_message(message = 'You have a meeting request', channel = a)
        emails = [get_emails(a) for a in attendees]
        names = [get_names(a) for a in attendees]
        cal_descr = 'Meeting with ' + ''.join(names)
        create_calendar_event(cal, emails, cal_descr)
    except ValueError as ve:
        print(ve)
    except KeyError as ke:
        print(ke)


if __name__ == "__main__":
    print("Starting the program")
    run()
    #parse_message("Setup a meeting with Pradeep tomorrow from 10AM to 11AM")
    
