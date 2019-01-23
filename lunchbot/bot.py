'''actual bot code'''
import os
import re
from flask import current_app
from werkzeug.local import LocalProxy
from slackclient import SlackClient
from lunchbot import BOTNAME, db

REQUEST_MATCHER = {
    'dad_joke': lambda x: re.match(r'^.*(i( a)??m).+hungry', x),
    'start_lunch': lambda x: re.match(r'^.*(get|grab|going|take|brb).+(lunch|food)', x),
    'stop_lunch': lambda x: re.match(r'^.*(i( a)??m).+(done|back|finished|full)', x),
    'needs_snickers': lambda x: re.match(r'.*(fuck|bitch|hate|ass|stupid|dumb|shit).*', x),
    'insult_lindsey': lambda x: re.match(r'.*insult lindsey.*', x),
    'love': lambda x: re.match('.* i love you.*', x)
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
        if REQUEST_MATCHER['needs_snickers'](message):
            self.recommend_snickers(channel)
        elif REQUEST_MATCHER['dad_joke'](message):
            self.make_dad_joke(channel, message, timestamp)
        elif REQUEST_MATCHER['start_lunch'](message):
            self.start_lunch(user, channel)
        elif REQUEST_MATCHER['stop_lunch'](message):
            self.stop_lunch(user, channel)
        elif REQUEST_MATCHER['insult_lindsey'](message):
            self.insult_lindsey(channel)


    def no_love(self, user, channel):
        text = f"I am a robot <@{user}>. If you are lonely please seek comfort elsewhere."
        self._send_message(channel, text)


    def insult_lindsey(self, channel):
        self._send_message(os.getenv('LINDSEY_ID'),"You are the worst!")
        self._send_message(channel, "Just did!")


    def recommend_snickers(self, channel):
        joke = f"You get so cranky when you're hungry. Have a snickers:\nhttps://www.amazon.com/SNICKERS-Singles-Chocolate-1-86-Ounce-48-Count/dp/B001HXI0V0/ref=sr_1_5?keywords=snicker&qid=1548107459&sr=8-5"
        self._send_message(channel, joke, unfurl_media=True)


    def make_dad_joke(self, channel, message, timestamp):
        name = re.sub(r'(i( a)?m|uf3l7l0dv)+', '', message).strip()
        joke = f"Hi {name}, I'm {BOTNAME}"
        self._send_message(channel, joke)


    def start_lunch(self, user, channel):
        geeks_eating = self.get_geeks_onlunch()
        if len(geeks_eating) > int(os.getenv('LUNCH_WARNING_THRESHOLD')):
            geek_list = "\n".join(f"- <@{geek['id']}>" for geek in geeks_eating)
            self._send_message(
                channel,
                f"*Whoa! We're {len(geeks_eating)} geeks short right now!*\n"
                "_Maybe wait a bit or slack the gluttons to see when they'll be done?_\n"
                f"Here they are:\n{geek_list}"
            )
        else:
            self._send_message(channel, f"Alright <@{user}>! Enjoy whatever it is you humans eat!")
            self._update_db(user,None,1)


    def stop_lunch(self, user, channel):
        self._send_message(channel, f"Good. Now get back to work human meatsack!")
        self._update_db(user,None,0)


    def get_geeks_onlunch(self):
        result = self.brain.execute('SELECT * from geeks where onlunch=1').fetchall()
        return result


    def _update_db(self,*argv):
        self.brain.execute(
            'INSERT INTO geeks (id,username,onlunch)'
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
