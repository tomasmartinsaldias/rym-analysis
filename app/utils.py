import pandas as pd
from datetime import datetime
from app import db
from app.models import Album, Genre, Descriptor
from sqlalchemy import func

def process_csv_to_db(file_or_path):
    data = pd.read_csv(file_or_path)
    for index, row in data.iterrows():
        # 1. Transformar la fecha (M/D/Y -> objeto Date)
        try:
            fecha_obj = datetime.strptime(str(row['release_date']), '%m/%d/%Y').date()
        except (ValueError, TypeError):
            fecha_obj = None # Manejo de errores por si la fecha está mal

        # 2. Lógica de "Merge": Buscar si el álbum ya existe (cargado por API)
        # title y artist vienen del CSV. Se usa ilike para ignorar mayúsculas/minúsculas
        album = Album.query.filter(
            func.lower(Album.title) == func.lower(str(row['title'])),
            func.lower(Album.artist) == func.lower(str(row['artist']))
        ).first()

        if album:
            # Pegamos los datos del CSV a lo que ya existe
            album.position = row['position']
            album.release_date = fecha_obj
            album.avg_rating = row['avg_rating']
            album.rating_count = row['rating_count']
            album.review_count = row['review_count']
        else:
            # Si no existe, lo creamos de cero
            album = Album(
                position=row['position'],
                title=row['title'],
                artist=row['artist'],
                release_date=fecha_obj,
                avg_rating=row['avg_rating'],
                rating_count=row['rating_count'],
                review_count=row['review_count']
            )
            db.session.add(album)

        # 3. Lógica para Géneros (Muchos a Muchos)
        if pd.notna(row.get('primary_genres')):
            genres_list = str(row['primary_genres']).split(',')
            for g_name in genres_list:
                g_name = g_name.strip()
                genero = Genre.query.filter_by(name=g_name).first()
                if not genero:
                    genero = Genre(name=g_name)
                    db.session.add(genero)
                if genero not in album.genres:
                    album.genres.append(genero)

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
                    
    # 5. Guardar todo al final de los registros
    db.session.commit()