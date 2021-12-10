# suitable for Heroku and AWS Elastic Beanstalk
web: gunicorn --bind :8000 --threads 15 --workers 1 microblog:app
worker: rq worker microblog-tasks
