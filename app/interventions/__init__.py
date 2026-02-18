from flask import Blueprint

bp = Blueprint('interventions', __name__, url_prefix='/interventions')

from app.interventions import routes