# suitable for Heroku and AWS Elastic Beanstalk
web: flask db upgrade; flask translate compile; gunicorn --bind :8000 --workers 4 microblog:app
worker: rq worker microblog-tasks
