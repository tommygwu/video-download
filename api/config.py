"""Configuration for yt-dlp API"""

import os
from pathlib import Path

class Config:
    """Base configuration"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # API settings
    API_KEY = os.environ.get('YT_DLP_API_KEY', 'change-me-in-production')
    
    # Download settings
    DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', '/tmp/downloads')
    MAX_FILE_AGE_MINUTES = int(os.environ.get('MAX_FILE_AGE_MINUTES', '30'))
    MAX_DOWNLOAD_SIZE_MB = int(os.environ.get('MAX_DOWNLOAD_SIZE_MB', '500'))
    MAX_DURATION_SECONDS = int(os.environ.get('MAX_DURATION_SECONDS', '7200'))  # 2 hours
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', '10'))
    
    # yt-dlp default options
    DEFAULT_FORMAT = 'best[ext=mp4]/best'
    
    # Cookie configuration
    YOUTUBE_COOKIES_BASE64 = os.environ.get('YOUTUBE_COOKIES_BASE64', '')
    USE_COOKIES_FALLBACK = os.environ.get('USE_COOKIES_FALLBACK', 'true').lower() == 'true'
    
    # Player client configuration
    DEFAULT_PLAYER_CLIENT = os.environ.get('DEFAULT_PLAYER_CLIENT', 'ios')
    FALLBACK_ORDER = os.environ.get('FALLBACK_ORDER', 'ios,cookies,android').split(',')
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with config"""
        # Ensure download directory exists
        Path(cls.DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stdout in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('yt-dlp API startup')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    API_KEY = 'test-api-key'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}