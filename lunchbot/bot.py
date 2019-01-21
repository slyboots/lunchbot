'''actual bot code'''
import os
import re
from flask import current_app

from slackclient import SlackClient
from lunchbot import BOTNAME

logger = current_app.logger

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
        self.messages = {}

    def respond(self, event):
        user = event['event']['user']
        message = sanitize(event['event']['text'])
        channel = event['event']['channel']
        timestamp = event['event']['ts']
        logger.debug(f"[{timestamp}] message from {user} in {channel}: {message}")
        if self.could_make_dad_joke(message):
            self.with_dad_joke(channel, message, timestamp)


    def with_dad_joke(self, channel, message, timestamp):
        name = re.sub(r'^.*(im|i am)', '', message).strip()
        joke = f"Hi {name}, I'm {BOTNAME}"
        self._send_message(channel, joke)


    def could_make_dad_joke(self, text):
        return 'im hungry' in text


    def _send_message(self,channel,text,**kwargs):
        post_message = self.client.api_call("chat.postMessage",
                                            channel=channel,
                                            username=self.name,
                                            icon_emoji=self.emoji,
                                            as_user=True,
                                            text=text,
                                            **kwargs
                                            )
        logger.debug(f"sent message: {post_message}")
