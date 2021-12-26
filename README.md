# Welcome to Microblog!

This is a fork of the [Microblog](https://github.com/miguelgrinberg/microblog) application written by Miguel Grinberg as part of his [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world).

This fork extends the original application as follows:
* Support for integration with [AWS Elastic Beanstalk](https://aws.amazon.com/elasticbeanstalk/). See the official [AWS Elastic Beanstalk - Developer Guide](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/) for further details.
* ...further extensions are planned

## Environment Variables
Microblog supports the following environment variables (see `config.py`):
* `FLASK_APP`: Name of the application to be loaded by Flask. This variable is also defined in `.flaskenv`.
* `FLASK_ENV`: Name of the environment Flask is run in. [`development` / `production`]
* `LOG_TO_STDOUT`: If set, logs are written to stdout, suitable for most environments where Flask is launched via `supervisor`. If not set, logs are written to `logs` directory, ideal during development.
* `SECRET_KEY`: The secret key used for computing and verifying session tokens. Should be randomly generated using e.g. `python -c "import uuid; print(uuid.uuid4().hex)"`.
* `RDS_PREFIX`: Database connection details. If `RDS_PREFIX` is not set, SQLite will be used.
  * `RDS_USERNAME`: Name of the database user.
  * `RDS_PASSWORD`: Password of the database user.
  * `RDS_HOSTNAME`: Hostname or IP address of database to connect to.
  * `RDS_PORT`: TCP port of database to connect to.
  * `RDS_DB_NAME`: Name of the database to connect to.
* `MAIL_SERVER`: SMTP connection details. If `MAIL_SERVER` is not set, then email notifications are disabled entirely.
  * `MAIL_PORT`: TCP port to use for SMTP connection.
  * `MAIL_USE_TLS`: Whether or not to use TLS for the STMP connection. To disable, make sure this variable is unset.
  * `MAIL_USERNAME`: User name for SMTP authentication.
  * `MAIL_PASSWORD`: Password for SMTP authentication.
* `ADMIN_EMAIL`: This email address is used that as sender for all emails and as recipient for exception failure emails.
* `MAIL_SUBJECT_PREFIX`: Prefix to append to each email subject. Useful to identify the environment (DEV / TEST / PROD) an email originated from.
* `REDIS_URL`: URL for redis service, used for handling of asynchronous background tasks.
* `REDIS_PSW`: Password for authentication to redis service
* `MS_TRANSLATOR_KEY`: Authentication key for the Microsoft translator service.
* `MS_TRANSLATOR_REGION`: MS Azure cloud computing region where the translator service runs
* `ELASTICSEARCH_URL`: URL for Elasticsearch service, used for full-text search of blog posts.
* `ELASTICSEARCH_USER`: User name for authentication to Elasticsearch service
* `ELASTICSEARCH_PSW`: Password for authentication to Elasticsearch service


## Deployment

### Linux
See the [Deployment on Linux](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvii-deployment-on-linux) tutorial for further details.
Since this is a direct deployment on top of Linux, it is also suitable for the Infrastructure as a Service (IaaS) cloud service model.

It is recommended to create a `.env` file in order to set the required environment variables.

### Docker
See the [Deployment on Docker Containers](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xix-deployment-on-docker-containers) tutorial for further details.

### Heroku
Heroku is a cloud service delivered through a Platform as a Service (PaaS) model.

See the [Deployment on Heroku](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xviii-deployment-on-heroku) tutorial for further details.

### AWS Elastic Beanstalk
[AWS Elastic Beanstalk](https://aws.amazon.com/elasticbeanstalk/) is a Platform as a Service (PaaS) offering by AWS.

It is recommended to set any required environment variables via the  a AWS Elastic Beanstalk console or via the EB CLI using `eb setenv VAR1=VAL1 VAR2=VAL2 ...`.
