import spacy
import parsedatetime
from datetime import datetime
import os
from sutime import SUTime
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import datetime
import json

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
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

def create_calendar_event(service, start_time, end_time, persons, timezone, event_body):
    event = {
        'summary': event_body,
        'description': event_body,
        'start': {
            'dateTime': start_time,
            'timeZone': 'America/Los_Angeles',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'America/Los_Angeles',
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


