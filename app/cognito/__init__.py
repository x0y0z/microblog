from flask import Blueprint

bp = Blueprint('cognito', __name__)

from app.cognito import routes
