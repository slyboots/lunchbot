from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
from hungrybot.db import get_db

bp = Blueprint('api', __name__)

@bp.route('/geeks/', methods=['GET'])
def get_all():
    db = get_db()
    geeks = db.execute('SELECT * FROM geek').fetchall()
    geeks_json = jsonify([dict(i) for i in geeks])
    return geeks_json # render_template('blog/index.html', posts=posts)
