'''actual bot code'''
import os
import re
import json
from flask import current_app
from werkzeug.local import LocalProxy
from slackclient import SlackClient
from lunchbot import BOTNAME, db

ADMINS = os.getenv('ADMINS').split(',')

REQUEST_MATCHER = {
    'dad_joke': lambda x: re.match(r'^.*(i( a)??m).+hungry', x),
    'start_lunch': lambda x: re.match(r'^.*(get|grab|going|take|brb).+(lunch|food|eat)', x),
    'stop_lunch': lambda x: re.match(r'^.*(i( a)??m).+(done|back|finished|full)', x),
    'needs_snickers': lambda x: re.match(r'.*(fuck|bitch|hate|ass|stupid|dumb|shit|suck).*', x),
    'insult_lindsey': lambda x: re.match(r'.*insult lindsey.*', x),
    'love': lambda x: re.match(r'.*i love you.*', x),
    'help': lambda x: re.match(r'.*h(e|a)lp.*', x),
    'status_report': lambda x: re.match(r'.*status( report)?.*', x),
    'ping': lambda x: re.match(r'.*ping.*', x),
    'potluck': lambda x: re.match(r'.*potluck.*', x),
    'set_pronouns': lambda x: re.match(r'.*i( a)??m an??\s"(.+)"', x),
    'get_brain': lambda x: re.match(r'.*let me pick your brain.*', x)
}


def sanitize(text):
    return re.sub(r'[^a-zA-Z0-9\s"]', '', text).lower()


class Bot(object):
    """ Instanciates a Bot object to handle Slack onboarding interactions."""
    def __init__(self):
        super(Bot, self).__init__()
        self.name = BOTNAME
        self.emoji = ":robot_face:"
        self.verification = os.environ.get("VERIFICATION_TOKEN")
        self.client = SlackClient(os.getenv("BOT_TOKEN"))
        self.brain = LocalProxy(db.get_db)
        self.potluck = False

    def respond(self, event):
        user = event['event']['user']
        message = sanitize(event['event']['text'])
        channel = event['event']['channel']
        timestamp = event['event']['ts']
        current_app.logger.debug(f"[{timestamp}] message from {user} in {channel}: {message}")
        if REQUEST_MATCHER['help'](message):
            self.help(channel)
        elif REQUEST_MATCHER['ping'](message):
            self.ping_pong(channel)
        elif REQUEST_MATCHER['start_lunch'](message):
            self.start_lunch(user, channel)
        elif REQUEST_MATCHER['stop_lunch'](message):
            self.stop_lunch(user, channel)
        elif REQUEST_MATCHER['status_report'](message):
            self.status_report(channel)
        elif REQUEST_MATCHER['needs_snickers'](message):
            self.recommend_snickers(channel)
        elif REQUEST_MATCHER['dad_joke'](message):
            self.make_dad_joke(channel, message)
        elif REQUEST_MATCHER['insult_lindsey'](message):
            self.insult_lindsey(channel, user)
        elif REQUEST_MATCHER['love'](message):
            self.no_love(user, channel)
        elif REQUEST_MATCHER['potluck'](message):
            self.toggle_potluck(channel)
        elif REQUEST_MATCHER['set_pronouns'](message):
            self.set_pronoun(channel, user, message)
        elif REQUEST_MATCHER['get_brain'](message):
            self._send_message(channel, self._get_brain())
        else:
            current_app.logger.debug(f"Using generic response. Unable to match: {message}.")
            self.general_response(channel)


    def set_pronoun(self, channel, user, message):
        pronoun = REQUEST_MATCHER['set_pronouns'](message).groups()[-1]
        current_app.logger.debug(f"PRONOUN: {pronoun}")
        self._update_pronoun(pronoun, user)
        self._send_message(channel, f"Okay, from now on I'll refer to you as a \"{pronoun}\"")


    def toggle_potluck(self, channel):
        self.potluck = not self.potluck
        self._send_message(channel, f"Potluck mode set to: {self.potluck}")


    def general_response(self, channel):
        self._send_message(channel, "_wat?_\nhttp://rg2.me/lunchwat")


    def ping_pong(self, channel):
        self._send_message(channel, "What do you want?")


    def status_report(self, channel):
        geeks = self.get_geeks_onlunch()
        total = len(geeks)
        if total == 0:
            message = "No humans are currently eating."
        else:
            message = f"{total} geek{'s' if total > 1 else ''} eating: " + ", ".join(f"<@{geek['id']}>" for geek in geeks)
        self._send_message(channel, message)


    def no_love(self, user, channel):
        text = f"I am a robot <@{user}>. If you are lonely please seek comfort elsewhere."
        self._send_message(channel, text)


    def insult_lindsey(self, channel, user):
        if user in ADMINS:
            self._send_message(os.getenv('LINDSEY_ID'), f"{user} would like you to know: You are the worst!")
            self._send_message(channel, "Just did!")
        else:
            self._send_message(channel, "No.")


    def recommend_snickers(self, channel):
        joke = f"You get so cranky when you're hungry. Have a snickers:\nhttp://rg2.me/getasnickerscrankypants"
        self._send_message(channel, joke, unfurl_media=True)


    def make_dad_joke(self, channel, message):
        name = re.sub(r'(i( a)?m|uf3l7l0dv)+', '', message).strip()
        joke = f"Hi {name}, I'm {BOTNAME}"
        self._send_message(channel, joke)


    def start_lunch(self, user, channel):
        if self.potluck is True:
            self._send_message(channel, f"We're having a potluck! Now shut up and go eat")
            return
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
            user_pronoun = self._get_pronoun(user)
            self._send_message(channel, f"Alright <@{user}>! Enjoy whatever it is you {user_pronoun}s eat!")
            self._update_lunch(user, 1)


    def stop_lunch(self, user, channel):
        user_pronoun = self._get_pronoun(user)
        self._send_message(channel, f"Good. Now get back to work {user_pronoun}!")
        self._update_lunch(user, 0)


    def help(self, channel):
        text = """*How to interact with LunchBot (_with examples_):*
- *Start lunch*: just tell me you're going to lunch and I'll remember.
>   @LunchBot I'm grabbing some food
- *Stop lunch*: let me know when you're done and I'll remember.
>   @LunchBot I'm done eating
- *Status Report*: Get a list of everyone who is at lunch.
>   @LunchBot status
- *Ping*: Make sure @LunchBot is alive
> @LunchBot ping!
- *Insult Lindsey*: Sends Lindsey an insulting DM
> @LunchBot insult lindsey
- *Help*: Show this text.
>   @LunchBot halp
_If you have any suggestions on how I could be improved just yell at DakDak._
        """
        self._send_message(channel, text)


    def get_geeks_onlunch(self):
        result = self.brain.execute('SELECT * from geeks where onlunch=1').fetchall()
        return result


    def _update_lunch(self, user, onlunch):
        query = ''' INSERT INTO geeks (id,onlunch)
                    VALUES (?,?)
                    ON CONFLICT(id) DO UPDATE SET onlunch=excluded.onlunch''',
        self.brain.execute(
            query,
            (user, onlunch)
        )
        self.brain.commit()


    def _get_pronoun(self, user):
        query = "SELECT pronoun from geeks WHERE id = ?"
        return self.brain.execute(query, [user]).fetchone()


    def _update_pronoun(self, pronoun, user):
        query = f''' UPDATE geeks
                    SET pronoun = ?
                    WHERE id = ?'''
        self.brain.execute(query, [pronoun, user])
        self.brain.commit()


    def _get_brain(self):
        return json.dumps(
            [dict(row) for row in self.brain.execute('SELECT * from geeks').fetchall()],
            indent=2
        )


    def _send_message(self, channel, text, **kwargs):
        post_message = self.client.api_call("chat.postMessage",
                                            channel=channel,
                                            username=self.name,
                                            icon_emoji=self.emoji,
                                            as_user=True,
                                            text=text,
                                            **kwargs
                                            )
        current_app.logger.debug(f"sent message: {post_message}")
