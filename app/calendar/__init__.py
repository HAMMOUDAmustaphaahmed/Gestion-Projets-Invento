from flask import Blueprint, jsonify
from app import db

bp = Blueprint('calendar', __name__, url_prefix='/calendar')

from app.calendar import routes

DEFAULT_CALENDAR_PERMISSIONS = {
    'calendar': {
        'read': True,
        'create': False,
        'update': False,
        'delete': False,
        'export': False
    }
}

@bp.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Ressource non trouvée'}), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'success': False, 'message': 'Erreur interne du serveur'}), 500

@bp.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'message': 'Requête invalide'}), 400