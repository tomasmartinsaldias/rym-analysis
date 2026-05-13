from app import create_app, db
from app.models import Album
import re
import os
import pylast
import time

def run_fix():
    app = create_app()
    with app.app_context():
        lastfm_api_key = os.environ.get("LASTFM_API_KEY")
        lastfm_api_secret = os.environ.get("LASTFM_API_SECRET")
        if not lastfm_api_key: return
            
        network = pylast.LastFMNetwork(api_key=lastfm_api_key, api_secret=lastfm_api_secret)
        
        problematic = Album.query.filter(Album.lastfm_listeners < 10).all()
        print(f"Última pasada para {len(problematic)} álbumes...")
        
        fixed_count = 0
        for album in problematic:
            original_artist = album.artist
            
            # Estrategia de candidatos
            candidates = set()
            candidates.add(original_artist)
            candidates.add(original_artist.replace("$", "s"))
            candidates.add("The " + original_artist)
            
            # Limpieza de duplicados
            match = re.search(r'([a-z])([A-Z])', original_artist)
            if match:
                candidates.add(original_artist[:match.start()+1])
            
            # Especiales
            if "Prodigy" in original_artist: candidates.add("The Prodigy")
            if "Kesha" in original_artist or "Ke$ha" in original_artist: candidates.add("Kesha")

            success = False
            for candidate in sorted(candidates, key=len): # Probar los más cortos primero
                if not candidate: continue
                try:
                    lf_album = network.get_album(candidate, album.title)
                    listeners = lf_album.get_listener_count()
                    if listeners and listeners > 10:
                        print(f"  OK: '{original_artist}' -> '{candidate}' ({listeners} oyentes)")
                        album.artist = candidate
                        album.lastfm_listeners = listeners
                        album.lastfm_playcount = lf_album.get_playcount()
                        success = True
                        fixed_count += 1
                        break
                except:
                    pass
            
            time.sleep(0.1)
            if fixed_count % 5 == 0: db.session.commit()
        
        db.session.commit()
        print(f"Finalizado. Corregidos {fixed_count} más.")

if __name__ == '__main__':
    run_fix()
