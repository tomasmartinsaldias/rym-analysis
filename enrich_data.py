from app import create_app, db
from app.utils import process_csv_to_db
from app.models import Album
from sqlalchemy import func
import time
import os
import json
import pylast
import musicbrainzngs
from datetime import datetime

app = create_app()

def enriquecer_con_lastfm_mb(albums_list):
    """
    Recibe una lista de diccionarios [{'title': '...', 'artist': '...', 'year': '...'}, ...]
    y usa las APIs de Last.fm y MusicBrainz para poblar la base de datos de manera inicial.
    """
    # Config Last.fm
    lastfm_api_key = os.environ.get("LASTFM_API_KEY", "TU_API_KEY")
    lastfm_api_secret = os.environ.get("LASTFM_API_SECRET", "TU_API_SECRET")
    network = pylast.LastFMNetwork(api_key=lastfm_api_key, api_secret=lastfm_api_secret)
    
    # Config MusicBrainz
    musicbrainzngs.set_useragent("RYMAnalysisBackend", "1.0", "tu_email@ejemplo.com")
    
    procesados = 0
    errores = []  # Lista para trackear álbumes con errores
    
    for item in albums_list:
        title = item.get('title')
        artist = item.get('artist')
        year_str = item.get('year', '')  # Ej: "1977-02-01" o "1977"
        
        if not title or not artist:
            continue
        
        # Parsear la fecha del CSV a un objeto Date
        fecha_obj = None
        if year_str and str(year_str) != 'nan':
            try:
                fecha_obj = datetime.strptime(str(year_str), '%Y-%m-%d').date()
            except ValueError:
                try:
                    fecha_obj = datetime.strptime(str(year_str), '%Y').date()
                except ValueError:
                    pass
            
        print(f"Buscando: {title} - {artist} ({year_str})")
        
        # 1. Chequeamos si el álbum ya existe en DB (título + artista + fecha)
        album_db = Album.query.filter(
            func.lower(Album.title) == func.lower(title),
            func.lower(Album.artist) == func.lower(artist),
            Album.release_date == fecha_obj
        ).first()
        
        if album_db and album_db.mbid:
            print(f"Skipping {title} ({year_str}) - ya enriquecido.")
            continue

        if not album_db:
            album_db = Album(
                title=title,
                artist=artist,
                release_date=fecha_obj,
                position=0,
                avg_rating=0.0,
                rating_count=0,
                review_count=0
            )
            db.session.add(album_db)

        # 2. Obtener datos de MusicBrainz (MBID y Label)
        # Pasamos la fecha para que encuentre la release correcta
        mb_ok = False
        for intento in range(3):  # Hasta 3 reintentos
            try:
                mb_kwargs = {"artist": artist, "release": title, "limit": 1}
                if fecha_obj:
                    mb_kwargs["date"] = str(fecha_obj.year)
                
                mb_results = musicbrainzngs.search_releases(**mb_kwargs)
                if mb_results.get("release-list"):
                    release = mb_results["release-list"][0]
                    album_db.mbid = release["id"]
                    
                    # Buscar label si está disponible
                    if "label-info-list" in release:
                        label_info = release["label-info-list"][0]
                        if isinstance(label_info.get("label"), dict):
                            album_db.label = label_info["label"].get("name", "")
                mb_ok = True
                break  # Salimos del retry si todo fue bien
            except Exception as e:
                print(f"Error MB (intento {intento+1}/3): {e}")
                time.sleep(3)  # Esperamos antes de reintentar
        
        if not mb_ok:
            errores.append({"title": title, "artist": artist, "year": str(year_str), "error": "MusicBrainz"})
            
        # 3. Obtener datos de Last.fm (Listeners y Playcount)
        # Last.fm no soporta filtrar por fecha, pero como busca por artista+título
        # y los álbumes homónimos son raros, generalmente devuelve el más popular.
        try:
            lf_album = network.get_album(artist, title)
            listeners = lf_album.get_listener_count()
            playcount = lf_album.get_playcount()
            
            album_db.lastfm_listeners = listeners
            album_db.lastfm_playcount = playcount
        except pylast.WSError:
            album_db.lastfm_listeners = 0
            album_db.lastfm_playcount = 0
        except Exception as e:
            print(f"Error Last.fm: {e}")
            errores.append({"title": title, "artist": artist, "year": str(year_str), "error": f"Last.fm: {e}"})

        procesados += 1
        
        # MusicBrainz requiere máximo 1 request por segundo.
        time.sleep(1)

        # Guardamos progreso cada 20 álbumes
        if procesados % 20 == 0:
            db.session.commit()
            print(f"[{procesados}] Progreso guardado.")
            
    db.session.commit()
    print(f"Completado. {procesados} álbumes procesados.")
    
    # Guardar lista de errores a un archivo
    if errores:
        with open('errores_enrich.json', 'w', encoding='utf-8') as f:
            json.dump(errores, f, ensure_ascii=False, indent=2)
        print(f"Se guardaron {len(errores)} errores en 'errores_enrich.json'.")
    else:
        print("No hubo errores.")

if __name__ == '__main__':
    with app.app_context():
        import pandas as pd
        
        print("Leyendo lista de álbumes desde el CSV...")
        try:
            df = pd.read_csv('rym_clean1.csv')
            # Enriquecemos el criterio de unicidad incluyendo la fecha
            df_unique = df[['release_name', 'artist_name', 'release_date']].drop_duplicates()

            # Renombramos para el diccionario
            df_unique = df_unique.rename(columns={
                'release_name': 'title', 
                'artist_name': 'artist',
                'release_date': 'year'
            })
            albums_a_poblar = df_unique.to_dict('records')
            
            print(f"Se encontraron {len(albums_a_poblar)} álbumes únicos para buscar.")
            print("Poblando base de datos con Last.fm y MusicBrainz. Esto puede tardar varios minutos...")
            
            enriquecer_con_lastfm_mb(albums_a_poblar)
            
        except FileNotFoundError:
            print("Error: No se encontró el archivo 'rym_clean1.csv'. Asegúrate de que esté en la misma carpeta.")