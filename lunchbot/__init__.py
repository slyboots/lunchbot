import os
import json
import logging
from flask import Flask, render_template_string, request, make_response, jsonify
from flask.logging import default_handler
from werkzeug.exceptions import HTTPException


BOTNAME = __name__
BOTID = os.getenv('BOTID')


class RequestFormatter(logging.Formatter):
    def format(self, record):
        record.url = request.url
        record.remote_addr = request.remote_addr
        return super().format(record)


formatter = RequestFormatter(
    '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
    '%(levelname)s in %(module)s: %(message)s'
)


def no_retry_response(e, status_code=500):
    '''@type e: werkzeug.exceptions.HTTPException'''
    """responds with a slack no retry header"""
    return make_response(e.get_body(), e.code, {"X-Slack-No-Retry": 1})


def create_app(test_config=None):
    default_handler.setFormatter(formatter)
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, BOTNAME+'.sqlite')
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that returns the apps name
    @app.route('/')
    def index():
        return render_template_string("<h1>Hi! I'm {{name}}.</h1>", name=BOTNAME)
    # a ping endpoint for checking if the server is running
    @app.route('/ping')
    def ping():
        return jsonify({'response': 'Pong'})
    from lunchbot import db
    db.init_app(app)
    from lunchbot import api
    app.register_blueprint(api.bp)
    app.register_error_handler(HTTPException, no_retry_response)
    return app
