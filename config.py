import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-super-secret-key-change-this-12345-abcdef-ghijkl'
    
    # Aiven MySQL connection
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        "mysql+pymysql://avnadmin:AVNS_gk-MK5-1fa-HjpSNe28@"
        "mysql-tchs-ahmedmustaphahammouda.k.aivencloud.com:19932/defaultdb"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Optimized for Aiven free tier with better resilience
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,          # Recycle connections before MySQL times out
        'pool_pre_ping': True,        # Test connections before using them
        'pool_size': 2,               # Small pool for free tier
        'max_overflow': 3,            # Limited overflow
        'pool_timeout': 30,           # Wait up to 30s for a connection
        'connect_args': {
            'connect_timeout': 20,    # 20 second connection timeout
            'read_timeout': 20,       # 20 second read timeout
            'write_timeout': 20,      # 20 second write timeout
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': True        # Auto-commit for better reliability
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
    
    # Session Configuration
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