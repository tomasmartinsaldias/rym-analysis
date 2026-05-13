from app import create_app, db
from app.models import Album
import sys

def list_low_listeners():
    app = create_app()
    with app.app_context():
        # Buscar álbumes con 0 o 1 oyente
        low = Album.query.filter(Album.lastfm_listeners <= 1).limit(100).all()
        print(f"Encontrados {len(low)} álbumes con <= 1 oyente (mostrando primeros 100):")
        for a in low:
            try:
                line = f" - [{a.lastfm_listeners}] {a.artist} | {a.title}"
                print(line.encode('utf-8', errors='replace').decode('utf-8'))
            except:
                pass

if __name__ == '__main__':
    list_low_listeners()
