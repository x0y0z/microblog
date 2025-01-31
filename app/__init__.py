import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cognito_auth import CognitoAuthManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from elasticsearch import Elasticsearch
from redis import Redis
import rq
from config import Config
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_message = _l('Please log in to access this page.')
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()


def get_redis_client(url, password=None):
    # redis.Redis.from_url() doesn't support passing the password separately
    # Author: Owen Taylor
    # Source: https://github.com/andymccurdy/redis-py/issues/1347
    from urllib.parse import quote, urlparse, urlunparse

    if password:
        parts = urlparse(url)
        netloc = f':{quote(password)}@{parts.hostname}'
        if parts.port is not None:
            netloc += f':{parts.port}'

        url = urlunparse((parts.scheme, netloc, parts.path, parts.params, parts.query, parts.fragment))

    return Redis.from_url(url, decode_components=True)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    # tell Flask it is running behind a reverse proxy, so it can set response headers accordingly
    app.wsgi_app = ProxyFix(app.wsgi_app)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    cognito = CognitoAuthManager(app)
    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']], \
                                      http_auth=(app.config['ELASTICSEARCH_USER'], app.config['ELASTICSEARCH_PSW'])) \
        if app.config['ELASTICSEARCH_URL'] else None
    app.redis = get_redis_client(app.config['REDIS_URL'], app.config['REDIS_PSW'])
    app.task_queue = rq.Queue('microblog-tasks', connection=app.redis)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    if app.config['AUTH_USE_AWS_COGNITO']:
        # use AWS cognito based authentication module
        from app.cognito import bp as cognito_bp
        app.register_blueprint(cognito_bp, url_prefix='/cognito')
        login.login_view = 'cognito.login'
    else:
        # use built-in authentication module
        from app.auth import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        login.login_view = 'auth.login'

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr=app.config['ADMINS'][0],
                toaddrs=app.config['ADMINS'], subject='{}Microblog Failure'.format(app.config['MAIL_SUBJECT_PREFIX']),
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/microblog.log',
                                               maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Microblog startup')

    return app


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


from app import models
