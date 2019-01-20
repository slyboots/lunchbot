from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, make_response
)
from werkzeug.exceptions import abort
from lunchbot.db import get_db
from lunchbot.slack import from_event_json

bp = Blueprint('api', __name__)

@bp.route('/event/', methods=['POST'])
def update():
    '''a special endpoint for the slack api cat and mouse verification game
        https://api.slack.com/events-api
        Slack sends us a challenge token, and we have to... "accept" it,
        and then send it back to them
    '''
    if not request.is_json:
       return make_response("Not JSON data", 500, {"X-Slack-No-Retry": 1})
    data = request.get_json()
    if data.get('type','') == 'url_verification':
        return jsonify({'challenge': data.get('challenge')})
    else:
        print(jsonify(data))
        return jsonify(data)


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
        abort(405)
