from flask import flash, redirect, render_template, request, url_for
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user
from flask_babel import _
from flask_cognito_auth import callback_handler, login_handler, logout_handler
from app.cognito import bp
from app.models import User

# Inspiration for this module was drawn from code
#   originally written by Ankit Shrivastava:
#   https://pypi.org/project/flask-cognito-auth/


@bp.route('/login', methods=['GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('cognito/login.html', title=_('Sign In'))


@bp.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('cognito.awslogout'))


# Use @login_handler decorator on cognito login route
@bp.route('/awslogin', methods=['GET'])
@login_handler
def awslogin():
    pass


# Use @callback_handler decorator on your cognito callback route
@bp.route('/callback', methods=['GET'])
@callback_handler
def callback():
    user = User.query.filter_by(username='mario').first()#form.username.data).first()
    if user is None:
        flash(_('User not known in Microblog'))
        return redirect(url_for('cognito.login'))
    login_user(user, remember=False)
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('main.index')
    return redirect(next_page)


# Use @logout_handler decorator on your cognito logout route
@bp.route('/awslogout', methods=['GET'])
@logout_handler
def awslogout():
    pass


@bp.route('/error', methods=['GET'])
def page500():
    flash(_('An error occurred during authentication to AWS Cognito'))
    return redirect(url_for('main.index'))
