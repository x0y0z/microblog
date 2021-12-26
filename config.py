import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    if os.environ.get('RDS_PREFIX') is not None:
        SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
            os.environ.get('RDS_PREFIX'),
            os.environ.get('RDS_USERNAME'), os.environ.get('RDS_PASSWORD'),
            os.environ.get('RDS_HOSTNAME'), os.environ.get('RDS_PORT'),
            os.environ.get('RDS_DB_NAME'))
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SUBJECT_PREFIX = os.environ.get('MAIL_SUBJECT_PREFIX')
    ADMINS = [os.environ.get('ADMIN_EMAIL')]
    EXPORT_POST_SLEEP_SECONDS = int(os.environ.get('EXPORT_POST_SLEEP_SECONDS') or 5)
    LANGUAGES = ['en', 'es']
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    MS_TRANSLATOR_REGION = os.environ.get('MS_TRANSLATOR_REGION')
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    ELASTICSEARCH_USER = os.environ.get('ELASTICSEARCH_USER')
    ELASTICSEARCH_PSW = os.environ.get('ELASTICSEARCH_PSW')
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    REDIS_PSW = os.environ.get('REDIS_PSW')
    POSTS_PER_PAGE = 25
    AUTH_USE_AWS_COGNITO = os.environ.get('AUTH_USE_AWS_COGNITO')

    # Setup the flask-cognito-auth extention
    COGNITO_REGION = os.environ.get('COGNITO_REGION')
    COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
    COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
    COGNITO_CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET')
    COGNITO_DOMAIN = os.environ.get('COGNITO_DOMAIN')
    ERROR_REDIRECT_URI = os.environ.get('ERROR_REDIRECT_URI')
    COGNITO_STATE = os.environ.get('COGNITO_STATE')
    COGNITO_REDIRECT_URI = os.environ.get('COGNITO_REDIRECT_URI')
    COGNITO_SIGNOUT_URI = os.environ.get('COGNITO_SIGNOUT_URI')
