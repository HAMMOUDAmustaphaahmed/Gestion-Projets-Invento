from flask import Blueprint

bp = Blueprint('personnel', __name__, url_prefix='/personnel')

from app.personnel import routes