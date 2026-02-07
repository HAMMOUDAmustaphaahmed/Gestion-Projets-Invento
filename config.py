import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key - MUST be set in production via environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-super-secret-key-change-this-12345-abcdef-ghijkl'
    
    # Database - Aiven MySQL with SSL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        "mysql+pymysql://avnadmin:AVNS_gk-MK5-1fa-HjpSNe28@"
        "mysql-tchs-ahmedmustaphahammouda.k.aivencloud.com:19932/defaultdb"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
        'pool_size': 5,
        'max_overflow': 10,
        'connect_args': {
            'connect_timeout': 60,
            'read_timeout': 60,
            'write_timeout': 60,
            'ssl': {
                'check_hostname': False,
                'verify_mode': False
            }
        }
    }
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx'}
    
    # Image optimization
    OPTIMIZE_IMAGES = True
    MAX_IMAGE_DIMENSION = 2000
    IMAGE_QUALITY = 85
    SEND_FILE_MAX_AGE_DEFAULT = 300
    
    # Session Configuration - CRITICAL FOR CSRF
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'invento_session'
    SESSION_COOKIE_DOMAIN = None
    SESSION_COOKIE_PATH = '/'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_REFRESH_EACH_REQUEST = True
    
    # CSRF Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = False
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Application settings
    ITEMS_PER_PAGE = 20
    DASHBOARD_CHARTS_LIMIT = 6
    APP_NAME = 'Invento'
    APP_VERSION = '1.0.0'
    
    # Email configuration
    MAIL_SERVER = None
    MAIL_PORT = 587
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    ADMINS = ['admin@gmao.com']
    
    @staticmethod
    def init_app(app):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
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
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        import logging
        from logging import StreamHandler
        
        stream_handler = StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ENGINE_OPTIONS = {}

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig
}
