import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://oracle:urimandthumim@10.102.109.141:5432/connecting'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database connection settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 20,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'co.nnecti.ng'
        }
    }
    
    # MongoDB configuration for translation cache
    MONGODB_HOST = os.environ.get('MONGODB_HOST') or '10.102.109.249'
    MONGODB_PORT = int(os.environ.get('MONGODB_PORT') or 27017)
    MONGODB_USERNAME = os.environ.get('MONGODB_USERNAME') or 'oracle'
    MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD') or 'urimandthumim'
    MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE') or 'connecting'
    
    # Ollama/Gemma3 configuration
    OLLAMA_HOST = os.environ.get('OLLAMA_HOST') or '10.102.109.66'
    OLLAMA_PORT = int(os.environ.get('OLLAMA_PORT') or 11434)
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL') or 'gemma3:1b'
    
    # Application settings
    POSTS_PER_PAGE = 20
    MAX_POST_LENGTH = 250
    MAX_IMAGES_PER_POST = 3
    SUPPORTED_LANGUAGES = ['en', 'fr', 'pt', 'de', 'es']
    
    # File upload settings
    UPLOAD_FOLDER = 'app/assets/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # SocketIO settings
    SOCKETIO_ASYNC_MODE = 'threading'
