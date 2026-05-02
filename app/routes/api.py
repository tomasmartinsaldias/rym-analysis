from flask import Blueprint, jsonify, request
from app.models import Album, Genre
from app import db
from sqlalchemy import func

api_bp = Blueprint('api', __name__)

@api_bp.route('/status')
def status():
    return jsonify({"status": "API configurada y lista."})

# 1. Endpoint para obtener álbumes (Paginado)
@api_bp.route('/albums', methods=['GET'])
def get_albums():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Soporte para filtrado por artista
    artist = request.args.get('artist')
    query = Album.query
    
    if artist:
        query = query.filter(Album.artist.ilike(f'%{artist}%'))
        
    pagination = query.order_by(Album.position).paginate(page=page, per_page=per_page, error_out=False)
    
    albums = []
    for album in pagination.items:
        albums.append({
            'id': album.id,
            'position': album.position,
            'title': album.title,
            'artist': album.artist,
            'release_date': album.release_date.strftime('%Y-%m-%d') if album.release_date else None,
            'avg_rating': album.avg_rating,
            'rating_count': album.rating_count,
            'review_count': album.review_count
        })
        
    return jsonify({
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'albums': albums
    })

# 2. Endpoint de Análisis Básico (Promedios, Máximos, Mínimos)
@api_bp.route('/analysis/basic', methods=['GET'])
def basic_analysis():
    # Álbum mejor puntuado
    top_album = Album.query.order_by(Album.avg_rating.desc()).first()
    # Promedio global de rating
    avg_rating_global = db.session.query(func.avg(Album.avg_rating)).scalar()
    # Total de reviews en la DB
    total_reviews = db.session.query(func.sum(Album.review_count)).scalar()
    
    return jsonify({
        'avg_rating_global': round(avg_rating_global, 2) if avg_rating_global else 0,
        'total_reviews_analyzed': total_reviews or 0,
        'top_rated_album': {
            'title': top_album.title,
            'artist': top_album.artist,
            'rating': top_album.avg_rating
        } if top_album else None
    })

# 3. Endpoint de Tendencias (Análisis más avanzado por década o año)
@api_bp.route('/analysis/trends', methods=['GET'])
def trends_analysis():
    # Calcula el promedio de rating por año de lanzamiento
    # SQLite usa strftime para extraer el año
    trends = db.session.query(
        func.strftime('%Y', Album.release_date).label('year'),
        func.avg(Album.avg_rating).label('avg_rating'),
        func.count(Album.id).label('album_count')
    ).filter(Album.release_date != None)\
     .group_by('year')\
     .order_by('year').all()
     
    results = [
        {
            'year': int(t.year),
            'avg_rating': round(t.avg_rating, 2),
            'album_count': t.album_count
        } for t in trends if t.year
    ]
    
    return jsonify({'trends': results})


