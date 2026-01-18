import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://avnadmin:AVNS_gk-MK5-1fa-HjpSNe28@"
        "mysql-tchs-ahmedmustaphahammouda.k.aivencloud.com:19936/defaultdb"
    )


    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx'}
    # Optimisation des images
    OPTIMIZE_IMAGES = True
    MAX_IMAGE_DIMENSION = 2000  # pixels
    IMAGE_QUALITY = 85  # qualité JPEG (0-100)   
    SEND_FILE_MAX_AGE_DEFAULT = 300
    # Security - Configuration pour permettre l'accès depuis différentes IPs
    # En développement, on désactive SESSION_COOKIE_SECURE pour permettre HTTP
    SESSION_COOKIE_SECURE = False  # Changé de True à False pour le développement
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Configuration CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Pas de limite de temps pour le token CSRF
    WTF_CSRF_SSL_STRICT = False  # Important: désactiver la vérification SSL stricte en dev
    
    # Application
    ITEMS_PER_PAGE = 20
    DASHBOARD_CHARTS_LIMIT = 6
    
    # Email (for future implementation)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['admin@gmao.com']
    @staticmethod
    def init_app(app):
        # Créer le dossier d'uploads s'il n'existe pas
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Créer les sous-dossiers
        for subfolder in ['projects', 'stock', 'personnel']:
            os.makedirs(
                os.path.join(app.config['UPLOAD_FOLDER'], subfolder), 
                exist_ok=True
            )
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False
    # En développement, désactiver les protections strictes
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_SSL_STRICT = False

class ProductionConfig(Config):
    DEBUG = False
    # Use production database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # En production, réactiver les protections
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
