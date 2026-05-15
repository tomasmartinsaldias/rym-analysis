from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    

    db.init_app(app)

    # Cargar datos pre-computados del recomendador (si existen)
    from app.services.recommender import load_recommender_data
    app.recommender_data = load_recommender_data()

    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    from app.routes.game import game_bp
    app.register_blueprint(game_bp)

    return app
