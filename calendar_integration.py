import spacy
import parsedatetime
from datetime import datetime
import os
import re
from sutime import SUTime
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import datetime
import json
from datetime import datetime, date, time
import iso8601
import logging

logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)

# Setup the Calendar API
def init_calendar():
    SCOPES = 'https://www.googleapis.com/auth/calendar'
    store = file.Storage('/Users/pbanavara/Downloads/credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))
    return service

# Call the Calendar API
def get_calendar_events(service):
    #now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    now = datetime.combine(date.today(), time()).isoformat() + 'Z'
    end = datetime.now().replace(hour=23,minute=0,second=0,microsecond=0).isoformat() + 'Z'
    print(now)
    print('Getting the upcoming events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        timeMax=end, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    total_duration = 0
    if not events:
        return('No upcoming events found.')
    for event in events:
        summary = event['summary']
        target = re.compile('meet', re.IGNORECASE)
        if target.search(summary):
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            diff = iso8601.parse_date(end) - iso8601.parse_date(start)
            total_duration += diff.seconds
    return int(total_duration/3600)

def create_calendar_event(service, start_time, end_time, persons = [], timezone = 'Asia/Kolkata', event_body = "Dummy"):
    event = {
        'summary': event_body,
        'description': event_body,
        'start': {
            'dateTime': start_time,
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_time,
            'timeZone': timezone,
        },
        'attendees': [
            {'email': 'pradeepbs@gmail.com'}
        ]
    }
    service.events().insert(calendarId = 'primary', body=event).execute()

def get_tokens(text):
    nlp = spacy.load('en_core_web_sm')
    cal = parsedatetime.Calendar()
    doc = nlp(text)
    for e in doc.ents:
        print(e.text, e.label_)
        if e.label_ == 'DATE':
            time_struct, _ = p_t = cal.parse(e.text)
            print(datetime.datetime(*time_struct[:6]))
            
def get_tokens_sutime(text):
    jar_files = os.path.join(os.path.dirname(__file__), 'jars')
    sutime = SUTime(jars=jar_files, mark_time_ranges=True)

    print(json.dumps(sutime.parse(text), sort_keys=True, indent=4))

if __name__ == "__main__":
    """
    service = init_calendar()
    create_calendar_event(service, '2018-06-21T17:00:00', '2018-06-21T17:30:00', ['pradeepbs@gmail.com'], 
                            'Asia/Kolkata', 'Meeting with Pradeep')
    get_calendar_events(service)
    """
    get_tokens_sutime("Schedule a team meeting for 1 hour meeting with my team for tomorrow noon")


