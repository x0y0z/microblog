from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user
from flask_babel import _
from app import db
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
    # N.B.: we don't need to explicitly verify the CSRF token, as this is already done by flask_cognito_auth
    if request.values.get('error') is not None:
        # AWS Cognito reeturned an error.
        flash(request.values.get('error'))
    elif session is not None and session.get('expires') > 0:
        user = User.query.filter_by(aws_cognito_uid=session.get('id')).first()
        if user is not None:
            # User known in Microblog. Check whether their AWS Cognito and Microblog username matches
            if user.username != session.get('username'):
                # the built-in username doesn't match the one in AWS cognito. force logout.
                flash(_('Microblog and AWS Cognito user names do not match.'))
                return redirect(url_for('cognito.logout'))
            else:
                # user found, we can proceed and log them in
                flash(_('Login successful!'))
        else:
            # User not known in Microblog. Register in Microblog so that we can link our internal records.
            # check whether username is already in use
            user = User.query.filter_by(username=session.get('username')).first()
            if user is not None:
                flash(_('Please use a different username.'))
                return redirect(url_for('cognito.logout'))
            # check whether email address is already in use
            user = User.query.filter_by(email=session.get('email')).first()
            if user is not None:
                flash(_('Please use a different email address.'))
                return redirect(url_for('cognito.logout'))
            # validation succeeded. register the user.
            user = User(username=session.get('username'), email=session.get('email'),
                        aws_cognito_uid=session.get('id'))
            db.session.add(user)
            db.session.commit()
            flash(_('Congratulations, you are now a registered user!'))
        # we have made it until here, we can log in the user now
        login_user(user, remember=False)
    else:
        flash(_('Session not found in Microblog'))
        return redirect(url_for('cognito.logout'))
    # redirect to next_page URL parameter if set, otherwise redirect to the index page
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
