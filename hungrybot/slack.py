import json
from json import JSONEncoder

EXAMPLE_EVENT_DICT = {
    "token": "one-long-verification-token",
    "team_id": "T061EG9R6",
    "api_app_id": "A0PNCHHK2",
    "event": {
        "type": "message",
        "channel": "C024BE91L",
        "user": "U2147483697",
        "text": "Live long and prospect.",
        "ts": "1355517523.000005",
        "event_ts": "1355517523.000005",
        "channel_type": "channel"
    },
    "type": "event_callback",
    "authed_teams": [
        "T061EG9R6"
    ],
    "event_id": "Ev0PV52K21",
    "event_time": 1355517523
}
EXAMPLE_EVENT_STRING = '''{
    "token": "one-long-verification-token",
    "team_id": "T061EG9R6",
    "api_app_id": "A0PNCHHK2",
    "event": {
        "type": "message",
        "channel": "C024BE91L",
        "user": "U2147483697",
        "text": "Live long and prospect.",
        "ts": "1355517523.000005",
        "event_ts": "1355517523.000005",
        "channel_type": "channel"
    },
    "type": "event_callback",
    "authed_teams": [
        "T061EG9R6"
    ],
    "event_id": "Ev0PV52K21",
    "event_time": 1355517523
}'''
PHRASE_IDENTIFIER = "hungrybot"
LUNCH_START_PHRASES = [
    'grab something to eat',
    'get something to eat',
    'grab lunch',
    'get lunch',
    'go to lunch',
    'going to lunch',
    'take lunch',
    'get my grub on'
]
LUNCH_END_PHRASES = [
    'im back',
    'im done eating',
    'im stuffed',
    'im full'
]

class SlackEventEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

def from_event_json(j):
    args = None
    if j.get('event',{}).get('type','') == 'message':
        args = {
            'token': j['token'],
            'id': j['event_id'],
            'timestamp': j['event_time'],
            'sender': j['event']['user'],
            'content': j['event']['text']
        }
    if args:
        return Message(**args)

class Message:
    def __init__(self, token, id, timestamp, sender, content):
        self.token = token
        self.id = id
        self.timestamp = timestamp
        self.sender = sender
        self.content = content
        self.lunch_alert_type = self.parseLunchAlert(content)
    def parseLunchAlert(self, msg):
        if PHRASE_IDENTIFIER in msg:
            if any(p in msg for p in LUNCH_START_PHRASES):
                return 1
            if any(p in msg for p in LUNCH_END_PHRASES):
                return 0
        return None
