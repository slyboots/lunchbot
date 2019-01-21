'''actual bot code'''
import os
import re
from flask import current_app
from werkzeug.local import LocalProxy
from slackclient import SlackClient
from lunchbot import BOTNAME, db

REQUEST_MATCHER = {
    'dad_joke': lambda x: re.match(r'^.*(i( a)??m).+hungry', x),
    'start_lunch': lambda x: re.match(r'^.*(get|grab|going|take).+lunch', x),
    'stop_lunch': lambda x: re.match(r'^.*(i( a)??m).+(done|back|finished|full)', x)
}


def sanitize(text):
    return re.sub(r'[^a-zA-Z0-9\s]','',text).lower()


class Bot(object):
    """ Instanciates a Bot object to handle Slack onboarding interactions."""
    def __init__(self):
        super(Bot, self).__init__()
        self.name = BOTNAME
        self.emoji = ":robot_face:"
        self.verification = os.environ.get("VERIFICATION_TOKEN")
        self.client = SlackClient(os.getenv("BOT_TOKEN"))
        self.brain = LocalProxy(db.get_db)

    def respond(self, event):
        user = event['event']['user']
        message = sanitize(event['event']['text'])
        channel = event['event']['channel']
        timestamp = event['event']['ts']
        current_app.logger.debug(f"[{timestamp}] message from {user} in {channel}: {message}")
        if REQUEST_MATCHER['dad_joke'](message):
            self.make_dad_joke(channel, message, timestamp)
        elif REQUEST_MATCHER['start_lunch'](message):
            self.start_lunch(user, channel)
        elif REQUEST_MATCHER['stop_lunch'](message):
            self.stop_lunch(user, channel)


    def make_dad_joke(self, channel, message, timestamp):
        name = re.sub(r'^.*(i( a)?m)', '', message).strip()
        joke = f"Hi {name}, I'm {BOTNAME}"
        self._send_message(channel, joke)


    def start_lunch(self, user, channel):
        self._send_message(channel, f"Alright <@{user}>! Enjoy whatever it is you humans eat!")
        self._update_db(user,None,1)


    def stop_lunch(self, user, channel):
        self._send_message(channel, f"Good. Now get back to work human meatsack!")
        self._update_db(user,None,0)

    def _update_db(self,*argv):
        self.brain.execute(
            'INSERT INTO geek (id,username,onlunch)'
            ' VALUES (?,?,?)'
            ' ON CONFLICT(id) DO UPDATE SET onlunch=excluded.onlunch',
            argv
        )
        self.brain.commit()

    def _send_message(self,channel,text,**kwargs):
        post_message = self.client.api_call("chat.postMessage",
                                            channel=channel,
                                            username=self.name,
                                            icon_emoji=self.emoji,
                                            as_user=True,
                                            text=text,
                                            **kwargs
                                            )
        current_app.logger.debug(f"sent message: {post_message}")
