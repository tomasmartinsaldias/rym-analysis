from app import create_app, db
from app.utils import process_csv_to_db
from app.models import Album
from sqlalchemy import func
import time
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

app = create_app()

def enriquecer_con_spotify(albums_list):
    """
    Recibe una lista de diccionarios [{'title': '...', 'artist': '...'}, ...]
    y usa la API de Spotify para poblar la base de datos de manera inicial.
    """
    client_id = os.environ.get("SPOTIPY_CLIENT_ID", "TU_CLIENT_ID")
    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET", "TU_CLIENT_SECRET")
    
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    procesados = 0
    
    for item in albums_list:
        title = item.get('title')
        artist = item.get('artist')
        
        if not title or not artist:
            continue
            
        print(f"Buscando en Spotify: {title} - {artist}")
        query = f"album:{title} artist:{artist}"
        results = sp.search(q=query, type='album', limit=1)
        
        if results['albums']['items']:
            sp_album = results['albums']['items'][0]
            spotify_id = sp_album['id']
            
            album_db = Album.query.filter_by(spotify_id=spotify_id).first()
            if not album_db:
                album_db = Album.query.filter(
                    func.lower(Album.title) == func.lower(title),
                    func.lower(Album.artist) == func.lower(artist)
                ).first()
                
            if not album_db:
                album_db = Album(
                    title=title,
                    artist=artist,
                    position=0,
                    avg_rating=0.0,
                    rating_count=0,
                    review_count=0
                )
                db.session.add(album_db)
                
            album_db.spotify_id = spotify_id
            album_db.total_tracks = sp_album['total_tracks']
            
            full_album = sp.album(spotify_id)
            album_db.spotify_popularity = full_album['popularity']
            album_db.label = full_album['label']
            
            artist_id = full_album['artists'][0]['id']
            full_artist = sp.artist(artist_id)
            album_db.artist_followers = full_artist['followers']['total']
            album_db.spotify_genres = ", ".join(full_artist['genres'])
            
            tracks = full_album['tracks']['items']
            track_ids = [t['id'] for t in tracks]
            
            features = sp.audio_features(tracks=track_ids[:100])
            valid_features = [f for f in features if f is not None]
            
            if valid_features:
                album_db.avg_energy = sum(f['energy'] for f in valid_features) / len(valid_features)
                album_db.avg_valence = sum(f['valence'] for f in valid_features) / len(valid_features)
                album_db.avg_acousticness = sum(f['acousticness'] for f in valid_features) / len(valid_features)
                album_db.avg_tempo = sum(f['tempo'] for f in valid_features) / len(valid_features)
                
            explicit_count = sum(1 for t in tracks if t['explicit'])
            album_db.pct_explicit = (explicit_count / len(tracks)) if len(tracks) > 0 else 0.0
            procesados += 1
            # Guardamos progreso cada 20 álbumes
            if procesados % 20 == 0:
                db.session.commit()
                print(f"[{procesados}] Progreso guardado. Evitando rate limit...")
                time.sleep(1) # Pausa más larga cada 20 requests
            else:
                time.sleep(0.1)
            
    db.session.commit() # Guardamos los que falten al final
    print(f"Completado. {procesados} álbumes procesados desde Spotify.")

if __name__ == '__main__':
    with app.app_context():
        import pandas as pd
        
        print("Leyendo lista de álbumes desde el CSV...")
        try:
            df = pd.read_csv('rym_clean1.csv')
            # Extraemos título y artista, eliminando duplicados por si acaso
            df_unique = df[['title', 'artist']].drop_duplicates()
            
            # Convertimos a la lista de diccionarios que espera nuestra función
            albums_a_poblar = df_unique.to_dict('records')
            
            print(f"Se encontraron {len(albums_a_poblar)} álbumes únicos para buscar en Spotify.")
            print("Poblando base de datos con Spotify. Esto puede tardar varios minutos...")
            
            enriquecer_con_spotify(albums_a_poblar)
            
        except FileNotFoundError:
            print("Error: No se encontró el archivo 'rym_clean1.csv'. Asegúrate de que esté en la misma carpeta.")