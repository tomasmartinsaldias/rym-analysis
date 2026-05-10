import os
from dotenv import load_dotenv

# Cargamos el archivo .env
load_dotenv()

class Config:
    # Flask y SQLAlchemy
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-de-emergencia-no-segura'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Last.fm Config
    LASTFM_API_KEY = os.environ.get('LASTFM_API_KEY')
    LASTFM_API_SECRET = os.environ.get('LASTFM_API_SECRET')