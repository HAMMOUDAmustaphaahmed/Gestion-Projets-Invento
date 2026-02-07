import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # IMPORTANT: Change this to a random string for production
    SECRET_KEY = 'your-secret-key-change-this-in-production-12345'
    
    # Database - hardcoded for simplicity
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://avnadmin:AVNS_gk-MK5-1fa-HjpSNe28@"
        "mysql-tchs-ahmedmustaphahammouda.k.aivencloud.com:19932/defaultdb"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20,
        'connect_args': {
            'connect_timeout': 30,
            'read_timeout': 30,
            'write_timeout': 30,
            'ssl': {
                'ssl_mode': 'REQUIRED'  # CRITICAL: Must be REQUIRED for Aiven
            }
        }
    }
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx'}
    
    # Image optimization
    OPTIMIZE_IMAGES = True
    MAX_IMAGE_DIMENSION = 2000
    IMAGE_QUALITY = 85
    SEND_FILE_MAX_AGE_DEFAULT = 300
    
    # Security settings
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # CSRF Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = False
    
    # Application settings
    ITEMS_PER_PAGE = 20
    DASHBOARD_CHARTS_LIMIT = 6
    
    # Email configuration
    MAIL_SERVER = None
    MAIL_PORT = 587
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    ADMINS = ['admin@gmao.com']
    
    @staticmethod
    def init_app(app):
        # Create upload folder if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Create subfolders
        for subfolder in ['projects', 'stock', 'personnel', 'equipment', 'interventions']:
            os.makedirs(
                os.path.join(app.config['UPLOAD_FOLDER'], subfolder), 
                exist_ok=True
            )

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ENGINE_OPTIONS = {}

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
