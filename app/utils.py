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