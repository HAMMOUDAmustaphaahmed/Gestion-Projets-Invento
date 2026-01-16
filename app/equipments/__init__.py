from flask import Blueprint

bp = Blueprint('equipments', __name__, url_prefix='/equipments')

from app.equipments import routes