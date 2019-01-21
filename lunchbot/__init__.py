import os
from flask import Flask, render_template_string

BOTNAME = __name__
BOTID = os.getenv('BOTID')

def no_retry_response(e, status_code=500):
    """responds with a slack no retry header"""
    return make_response(message, status_code, {"X-Slack-No-Retry": 1})

def create_app(test_config=None):
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

    from . import db
    db.init_app(app)
    from . import api
    app.register_blueprint(api.bp)
    app.register_error_handler(500, no_retry_response)
    return app
