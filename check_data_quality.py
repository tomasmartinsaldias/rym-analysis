from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import re

db = SQLAlchemy()

def check():
    app = Flask(__name__)
    db_path = os.path.join(os.getcwd(), 'instance', 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        from app.models import Album
        
        all_artists = db.session.query(Album.artist).distinct().all()
        
        corrupted = []
        for (artist,) in all_artists:
            if not artist: continue
            
            # Heurística de repetición difusa
            # Buscar si el inicio del nombre se repite más adelante
            # "Pink FloydPink Floyd" -> True
            # "Bob Marley & The WailersBob MarleyThe Wailers" -> True (Bob Marley se repite)
            
            clean_artist = artist.replace(" ", "").lower()
            # Si el nombre sin espacios tiene una repetición interna clara
            half = len(clean_artist) // 2
            if clean_artist[:half] == clean_artist[half:]:
                corrupted.append(artist)
                continue
            
            # Buscar repetición de palabras clave
            words = artist.split()
            unique_words = set()
            for w in words:
                if len(w) > 3:
                    if w in unique_words:
                        corrupted.append(artist)
                        break
                    unique_words.add(w)

        print(f"Encontrados {len(corrupted)} posibles nombres corruptos:")
        for c in corrupted:
            print(f" - {c}")

if __name__ == '__main__':
    check()
