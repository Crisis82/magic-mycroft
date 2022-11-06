from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from datetime import datetime
from dateutil.parser import parse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os.path

URL = ['https://www.googleapis.com/auth/calendar']
PATH = '/opt/mycroft/skills/magic-mirror-voice-control-skill/credentials/'

################### LOGIN ########################

def getToken():
    if os.path.exists(PATH+'token.json'):
        loginCreds = Credentials.from_authorized_user_file(PATH+'token.json', URL)
    else:
        loginCreds = None

    if not loginCreds or not loginCreds.valid:
        if loginCreds and loginCreds.expired and loginCreds.refresh_token:
            loginCreds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(PATH+'credentials.json', URL)
            loginCreds = flow.run_local_server(port=0)

        with open(PATH+'token.json', 'w') as token:
            token.write(loginCreds.to_json())
        print("Login successful!\n")
    else:
        print("Credentials loaded correctly!\n")

    return loginCreds

################### UTILS ########################

def dateFormat(date, time='00:00', utc=False):
    # date format used by Google
    # the format is 'year-month-day T hours:minutes:seconds utc'
    # e.g. 2020-06-21T14:25:00+01:00
    if date == '':
        return date
    else:
        if time == '' or time is None:
            time='00:00'

        if utc:
            localUTC = '+01:00'
        else:
            localUTC = ''
            
        return date + 'T' + time + ':01' + localUTC

def changeFormat(date, format='%d %B, %H:%M'):
    # default is a human-readable format
    # e.g. 25 September, 13:15
    return datetime.strftime(parse(date), format)

def defaultFormat(date):
    return datetime.strftime(parse(date), '%Y-%m-%dT%H:%M:%S')

################### SHOW ########################

def getEvent(service, title, date):        
    event_result = service.events().list(calendarId='primary', q=title, maxResults=1, singleEvents=True, orderBy='startTime').execute()
    event = event_result.get('items', [])
    if len(event) == 0:
        return None
    else:
        return event

def getEvents(service, startDate, endDate):        
    now = datetime.utcnow().isoformat()
    if startDate == '':
        print('Upcoming events:')
        events_result = service.events().list(calendarId='primary', timeMin=(now+'Z'), maxResults=5, singleEvents=True, orderBy='startTime').execute()
    else:
        if endDate == '':
            endDate = changeFormat(str(datetime.strptime(startDate, '%Y-%m-%dT%H:%M:%S') + datetime.datetime.timedelta(days=1)), '%Y-%m-%dT%H:%M:%S')
        if changeFormat(startDate, '%Y-%m-%d') == changeFormat(now, '%Y-%m-%d'):
            print('Today events:')
        else:
            print('%s events:' %changeFormat(startDate, '%a %d %B')) # print day of the week
        events_result = service.events().list(calendarId='primary', timeMin=(startDate+'Z'), timeMax=(endDate+'Z'), singleEvents=True, orderBy='startTime').execute()
    
    events = events_result.get('items', [])
    return events

def show(loadedCreds, start='', end=''):
    try:
        service = build('calendar', 'v3', credentials=loadedCreds)
        
        events = getEvents(service, start, end)
        if not events:
            print('No upcoming events found.')
        else:
            for event in events:
                eventTime = event['start'].get('dateTime', event['start'].get('date'))
                eventTimeFormatted = changeFormat(eventTime)
                print(eventTimeFormatted, event['summary'], event['id'])
    except HttpError as error:
        print('An error occurred: %s' % error)

################### ADD ########################

def createEvent(title, startDate, endDate, description):        
    start = {
        'dateTime': startDate + 'Z'
    }
    if endDate == '':
        end = start
    else:
        end = {
            'dateTime': endDate + 'Z'
        }
        
    event = {
        'summary': title,
        'description': description,
        'start': start,
        'end': end
    }

    return event

def alreadyExists(service, title, date):
    event = getEvent(service, title, date)
    if event:
        return True
    else:
        return False

def addEvent(title, startDate, endDate='', description=''):
    loadedCreds = getToken()
    try:
        service = build('calendar', 'v3', credentials=loadedCreds)

        if alreadyExists(service, title, dateFormat(startDate)):
            return 'Event already exists!'
        else:
            event = createEvent(title, startDate, endDate, description)
            service.events().insert(calendarId='primary', body=event).execute()
            return ('%s - %s  correctly added!' %(title,changeFormat(startDate, '%a %d %B %Y, %H:%M')))
    except HttpError as error:
        return ('Event not added, because of error: %s' % error)

################### DELETE ########################

def deleteEvent(title, date):
    loadedCreds = getToken()
    try:
        service = build('calendar', 'v3', credentials=loadedCreds)
        event = getEvent(service, title, date)
        if not event:
            return ('Event not found!')
        else:
            eventTitle=event[0]['summary']
            eventDate=event[0]['start'].get('dateTime', event[0]['start'].get('date'))
            eventId=event[0]['id']
            service.events().delete(calendarId='primary', eventId=eventId).execute()
            return ('%s - %s  correctly removed!' %(eventTitle,changeFormat(eventDate, '%a %d %B')))
    except HttpError as error:
        return ('Event not removed, because of error: %s' % error)

################### MAIN ########################

def googleEvent(action, title, date):
    if action == 'add':
        return addEvent(title, date)
    elif action == 'del':
        return deleteEvent(title, date)
    else:
        return 'No valid action!'