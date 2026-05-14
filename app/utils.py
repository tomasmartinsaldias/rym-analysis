import requests
import urllib.parse
import pandas as pd
from datetime import datetime
from app import db
from app.models import Album, Genre, Descriptor, album_genres
from sqlalchemy import func

def process_csv_to_db(file_or_path):
    data = pd.read_csv(file_or_path)
    count = 0
    for index, row in data.iterrows():
        # 1. Transformar la fecha (M/D/Y o YYYY-MM-DD -> objeto Date)
        try:
            fecha_str = str(row['release_date']).strip()
            if fecha_str and fecha_str.lower() != 'nan':
                try:
                    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        fecha_obj = datetime.strptime(fecha_str, '%Y').date()
                    except ValueError:
                        fecha_obj = datetime.strptime(fecha_str, '%m/%d/%Y').date()
            else:
                fecha_obj = None
        except (ValueError, TypeError):
            fecha_obj = None

        # 2. Lógica de "Merge"
        album = Album.query.filter(
            func.lower(Album.title) == func.lower(str(row['release_name'])),
            func.lower(Album.artist) == func.lower(str(row['artist_name'])),
            Album.release_date == fecha_obj
        ).first()

        if album:
            album.position = row['position']
            album.release_date = fecha_obj
            album.avg_rating = row['avg_rating']
            album.rating_count = row['rating_count']
            album.review_count = row['review_count']
        else:
            album = Album(
                position=row['position'],
                title=row['release_name'],
                artist=row['artist_name'],
                release_date=fecha_obj,
                avg_rating=row['avg_rating'],
                rating_count=row['rating_count'],
                review_count=row['review_count']
            )
            db.session.add(album)

        # 3. Lógica para Géneros (Muchos a Muchos con is_primary) de tu compañero
        db.session.flush() # Asegurar que el album tenga ID

        def add_genres(genres_str, primary_flag):
            if pd.notna(genres_str):
                g_list = [g.strip() for g in str(genres_str).split(',') if g.strip()]
                for g_name in g_list:
                    genero = Genre.query.filter_by(name=g_name).first()
                    if not genero:
                        genero = Genre(name=g_name)
                        db.session.add(genero)
                        db.session.flush()
                    
                    # Chequear si ya existe el vínculo en la tabla intermedia
                    exists = db.session.query(album_genres).filter_by(
                        album_id=album.id, genre_id=genero.id
                    ).first()
                    
                    if not exists:
                        db.session.execute(
                            album_genres.insert().values(
                                album_id=album.id, 
                                genre_id=genero.id, 
                                is_primary=primary_flag
                            )
                        )

        add_genres(row.get('primary_genres'), True)
        add_genres(row.get('secondary_genres'), False)

        # 4. Lógica para Descriptores
        if pd.notna(row.get('descriptors')):
            descriptors_list = str(row['descriptors']).split(',')
            for d_name in descriptors_list:
                d_name = d_name.strip()
                descriptor = Descriptor.query.filter_by(name=d_name).first()
                if not descriptor:
                    descriptor = Descriptor(name=d_name)
                    db.session.add(descriptor)
                if descriptor not in album.descriptors:
                    album.descriptors.append(descriptor)
                    
        # 5. Guardar por bloques para evitar 'database is locked' (mi mejora)
        count += 1
        if count % 100 == 0:
            db.session.commit()
            
    db.session.commit()

def resolve_album_id(text):
    """
    Resuelve un texto de búsqueda a un ID de álbum.
    Soporta formato "Título — Artista" o búsquedas parciales.
    """
    if not text:
        return None
    
    # 1. Intentar coincidencia exacta con formato "Título — Artista"
    if ' — ' in text:
        parts = text.split(' — ', 1)
        title_part = parts[0].strip()
        artist_part = parts[1].strip()
        # Limpiar año si viene en formato "Artista (1995)"
        if artist_part and artist_part.endswith(')') and '(' in artist_part:
            artist_part = artist_part[:artist_part.rfind('(')].strip()
            
        album = Album.query.filter(
            Album.title.ilike(title_part), 
            Album.artist.ilike(artist_part)
        ).first()
        if album:
            return album.id
    
    # 2. Intentar por título
    album = Album.query.filter(Album.title.ilike(f'%{text}%')).first()
    if album:
        return album.id
    
    # 3. Intentar por artista
    album = Album.query.filter(Album.artist.ilike(f'%{text}%')).first()
    if album:
        return album.id
    
    return None

def get_cover_url(album):
    """
    Consigue la URL de la portada de un álbum de forma robusta.
    1. Intenta iTunes con búsqueda refinada y validación de título.
    2. Si no hay match claro, intenta MusicBrainz (CAA) si el MBID existe.
    3. Si falla, intenta iTunes de nuevo con una búsqueda más laxa.
    """
    if not album:
        return None

    # Puede recibir un objeto Album o un diccionario (del recomendador)
    title = getattr(album, 'title', album.get('title') if isinstance(album, dict) else "")
    artist = getattr(album, 'artist', album.get('artist') if isinstance(album, dict) else "")
    mbid = getattr(album, 'mbid', album.get('mbid') if isinstance(album, dict) else None)

    if not title or not artist:
        return None

    # Limpiar título para mejor matching (ej: quitar "(remaster)", etc)
    clean_title = title.split(' (')[0].split(' [')[0].strip()

    # --- INTENTO 1: iTunes con Validación Estricta ---
    try:
        # Probamos "Artista Título" que suele dar mejores resultados en el buscador de iTunes
        term = urllib.parse.quote(f"{artist} {clean_title}")
        url = f"https://itunes.apple.com/search?term={term}&entity=album&limit=5"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            results = resp.json().get('results', [])
            for res in results:
                itunes_title = res.get('collectionName', '').lower()
                itunes_artist = res.get('artistName', '').lower()
                
                # Validación: El título debe coincidir casi exactamente
                if clean_title.lower() == itunes_title or \
                   (clean_title.lower() in itunes_title and artist.lower() in itunes_artist):
                    return res['artworkUrl100'].replace('100x100bb', '500x500bb')
    except Exception:
        pass

    # --- INTENTO 2: MusicBrainz / Cover Art Archive (Fallback si iTunes falló o no fue preciso) ---
    if mbid:
        caa_url = f"https://coverartarchive.org/release-group/{mbid}/front"
        try:
            # Verificamos que la imagen exista (el usuario mencionó errores previos con MBID)
            check = requests.head(caa_url, allow_redirects=True, timeout=1.5)
            if check.status_code == 200:
                return caa_url
        except Exception:
            pass

    # --- INTENTO 3: iTunes laxo (último recurso) ---
    try:
        term = urllib.parse.quote(f"{title} {artist}")
        url = f"https://itunes.apple.com/search?term={term}&entity=album&limit=1"
        resp = requests.get(url, timeout=1.5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('results'):
                return data['results'][0]['artworkUrl100'].replace('100x100bb', '500x500bb')
    except Exception:
        pass

    return None