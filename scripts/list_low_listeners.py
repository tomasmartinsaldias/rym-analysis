import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Album

def list_low_listeners():
    app = create_app()
    with app.app_context():
        # Álbumes con menos de 1000 oyentes
        low = Album.query.filter(Album.lastfm_listeners < 1000).all()
        print(f"Encontrados {len(low)} álbumes con menos de 1000 oyentes.")
        
        output_path = os.path.join('data', 'low_listeners.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            for a in low:
                f.write(f"[{a.lastfm_listeners}] {a.artist} - {a.title}\n")
        print(f"Lista guardada en {output_path}")

if __name__ == '__main__':
    list_low_listeners()
