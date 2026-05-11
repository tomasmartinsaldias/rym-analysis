import os
from dotenv import load_dotenv

# Cargamos el archivo .env
load_dotenv()

class Config:
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Flask y SQLAlchemy
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-de-emergencia-no-segura'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Last.fm Config
    LASTFM_API_KEY = os.environ.get('LASTFM_API_KEY')
    LASTFM_API_SECRET = os.environ.get('LASTFM_API_SECRET')