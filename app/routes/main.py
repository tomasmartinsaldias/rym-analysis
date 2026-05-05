from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.utils import process_csv_to_db
from app.models import Album, Genre, Descriptor
from sqlalchemy import extract
import plotly.graph_objects as go

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    top_albums = [
        {"position": 1, "title": "OK Computer", "artist": "Radiohead", "mbid": "541a0976-ca45-3c0f-89e5-26bc376f58d1"},
        {"position": 2, "title": "Kid A", "artist": "Radiohead", "mbid": "d3bbdcaa-5a13-4285-80e4-09fac885b1ec"},
        {"position": 3, "title": "The Dark Side of the Moon", "artist": "Pink Floyd", "mbid": "12ac832a-ffdb-49f2-90c0-9d4c8f828edd"},
        {"position": 4, "title": "Loveless", "artist": "My Bloody Valentine", "mbid": "b1ce7f03-4835-489e-9a0a-13124c6c0a9e"},
        {"position": 5, "title": "My Beautiful Dark Twisted Fantasy", "artist": "Kanye West", "mbid": "2fcfcaaa-6594-4291-b79f-2d354139e108"},
        {"position": 6, "title": "In Rainbows", "artist": "Radiohead", "mbid": "3b408cb5-7d51-4188-b07c-fabcf308cda3"},
        {"position": 7, "title": "Wish You Were Here", "artist": "Pink Floyd", "mbid": "476f385f-50e3-3beb-9465-a0f22da58a8e"},
        {"position": 8, "title": "In the Aeroplane Over the Sea", "artist": "Neutral Milk Hotel", "mbid": "4b01b4c7-bca1-4cd5-b5f7-a4c14f50730b"},
        {"position": 9, "title": "The Bends", "artist": "Radiohead", "mbid": "c50176ce-676c-4f30-a168-b333cfe1ed82"},
        {"position": 10, "title": "To Pimp a Butterfly", "artist": "Kendrick Lamar", "mbid": "a9337d06-b079-467a-b023-10b246ccff38"}
    ]
    return render_template('landing.html', top_albums=top_albums)

@main_bp.route('/data')
def data():
    # Obtener parámetros de los filtros
    artist = request.args.get('artist', '')
    title = request.args.get('title', '')
    genre = request.args.get('genre', '')
    min_rating = request.args.get('min_rating', type=float)
    year_from = request.args.get('year_from', type=int)
    year_to = request.args.get('year_to', type=int)
    page = request.args.get('page', 1, type=int)
    
    query = Album.query
    
    # Aplicar filtros a la query
    if artist:
        query = query.filter(Album.artist.ilike(f'%{artist}%'))
    if title:
        query = query.filter(Album.title.ilike(f'%{title}%'))
    if genre:
        query = query.join(Album.genres).filter(Genre.name == genre)
    if min_rating is not None:
        query = query.filter(Album.avg_rating >= min_rating)
    if year_from:
        query = query.filter(extract('year', Album.release_date) >= year_from)
    if year_to:
        query = query.filter(extract('year', Album.release_date) <= year_to)

    # Paginar resultados
    pagination = query.order_by(Album.position).paginate(page=page, per_page=50, error_out=False)
    
    # Obtener géneros para poblar el <select> del filtro
    all_genres = Genre.query.order_by(Genre.name).all()
    
    return render_template('data.html', pagination=pagination, genres=all_genres)

@main_bp.route('/analysis')
def analysis():
    return render_template('analysis.html')

@main_bp.route('/recommend')
def recommend():
    return render_template('recommend.html')

@main_bp.route('/album/<int:id>')
def album_detail(id):
    album = Album.query.get_or_404(id)
    
    # Normalización simplificada (idealmente calculada desde la DB)
    fig = go.Figure(data=go.Scatterpolar(
      r=[
          album.avg_rating / 5.0,
          min(album.rating_count / 50000, 1), 
          min(album.review_count / 1000, 1),
          min(album.lastfm_listeners / 2000000, 1) if album.lastfm_listeners else 0,
          min(album.lastfm_playcount / 15000000, 1) if album.lastfm_playcount else 0
      ],
      theta=['Rating', 'Pop. RYM', 'Reviews', 'Oyentes', 'Playcount'],
      fill='toself'
    ))
    
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False)
    chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    return render_template('album.html', album=album, chart=chart_html)

@main_bp.route('/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        flash('No se subió ningún archivo')
        return redirect(url_for('main.index'))
        
    file = request.files['file']
    if file.filename == '':
        flash('Archivo no seleccionado')
        return redirect(url_for('main.index'))
        
    if file and file.filename.endswith('.csv'):
        # process_csv_to_db ahora soporta file-like objects, así que le pasamos el file de Flask
        process_csv_to_db(file)
        flash('Datos del CSV fusionados con éxito en la base de datos.')
        return redirect(url_for('main.data'))
    else:
        flash('Por favor sube un archivo .csv')
        return redirect(url_for('main.index'))

