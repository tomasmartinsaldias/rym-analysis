from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.utils import process_csv_to_db
from app.models import Album, Genre, Descriptor
from sqlalchemy import extract
import plotly.graph_objects as go

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('landing.html')

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

