import json
from flask import (
    Blueprint, flash, redirect, render_template,
    request, url_for, jsonify, make_response
)
from werkzeug.exceptions import abort
from lunchbot.db import get_db
from lunchbot.slack import from_event_json
from lunchbot import bot, BOTNAME, BOTID

bp = Blueprint('api', __name__)
lunchbot = bot.Bot()

def _event_handler(event_type, slack_event):
    """
    A helper function that routes events from Slack to our Bot
    by event type and subtype.
    Parameters
    ----------
    event_type : str
        type of event recieved from Slack
    slack_event : dict
        JSON response from a Slack reaction event
    Returns
    ----------
    obj
        Response object with 200 - ok or 500 - No Event Handler error
    """
    # ================ App Mention Events =============== #
    # When you say @lunchbot
    if event_type == "app_mention":
        # send to bot for response
        lunchbot.respond(slack_event)
        return make_response("mention received", 200,)

    # ================ Message Events =============== #
    # In the event you forgot to put the "@" before lunchbot
    if event_type == "message" and slack_event['event'].get('user') != BOTID:
        # ignore messages unless they have BOTNAME in the text
        response = make_response("message ignored", 200)
        message = slack_event['event']['text']
        if any(i in message for i in [BOTNAME, BOTID]):
            response = make_response("message accepted", 200)
            lunchbot.respond(slack_event)
        return response

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = f"No handler defined for the {event_type}"
    return make_response(message, 200, {"X-Slack-No-Retry": 1})

@bp.route('/events/', methods=['GET', 'POST'])
def receive():
    '''listen for stuff then do other stuff in response to those things'''
    # for some reason we got weird stuff
    if not request.is_json:
       return make_response("Not JSON data", 500, {"X-Slack-No-Retry": 1})
    slack_event = json.loads(request.data)
    # Slack URL Verification
    if "challenge" in slack_event:
        return jsonify({'challenge': slack_event['challenge']})
    # Token Verification
    if lunchbot.verification != slack_event.get("token"):
        message = f"Invalid Slack verification token: {slack_event['token']} \
                   \npyBot has: {lunchbot.verification}\n\n"
        return make_response(message, 403, {"X-Slack-No-Retry": 1})
    # Handle events
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        # Then handle the event by event_type and have your bot respond
        return _event_handler(event_type, slack_event)
    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@bp.route('/geeks/', methods=['GET', 'POST'])
def list():
    '''
    The list() endpoint provides access to the list of geeks in the database
    you can view the list of geeks and thier individual statuses with a GET.
    you can send a POST to create a new user and add them to the list.
    POST body should be a user object formatted as json.
    '''
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        if any(x is None for x in [data['name'], data['lunchstatus']]) is None:
            flash("heck")
        else:
            db = get_db()
            db.execute(
                'INSERT INTO geek (name, lunchstatus)'
                ' VALUES (?, ?)',
                (data['name'], data['lunchstatus'])
            )
            db.commit()
            return redirect(url_for('api.list'))
    if request.method == 'GET':
        db = get_db()
        geeks = db.execute('SELECT * FROM geek').fetchall()
        geeks_json = jsonify([dict(i) for i in geeks])
        return geeks_json
    else:
        make_response("", 405, {"X-Slack-No-Retry": 1})

@bp.route("/install", methods=["GET"])
def pre_install():
    """This route renders the installation page with 'Add to Slack' button."""
    # Since we've set the client ID and scope on our Bot object, we can change
    # them more easily while we're developing our app.
    client_id = lunchbot.oauth["client_id"]
    scope = lunchbot.oauth["scope"]
    # Our template is using the Jinja templating language to dynamically pass
    # our client id and scope
    return render_template("install.html", client_id=client_id, scope=scope)

@bp.route("/thanks", methods=["GET", "POST"])
def thanks():
    """
    This route is called by Slack after the user installs our app. It will
    exchange the temporary authorization code Slack sends for an OAuth token
    which we'll save on the bot object to use later.
    To let the user know what's happened it will also render a thank you page.
    """
    # Let's grab that temporary authorization code Slack's sent us from
    # the request's parameters.
    code_arg = request.args.get('code')
    # The bot's auth method to handles exchanging the code for an OAuth token
    lunchbot.auth(code_arg)
    return render_template("thanks.html")
