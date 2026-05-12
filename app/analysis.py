import plotly.express as px
import plotly.graph_objects as go
from app.models import Album, Genre, album_genres
from app import db
from sqlalchemy import func
import pandas as pd
from scipy.stats import pearsonr, spearmanr

# Colores de la estética "Needle Drop"
COLOR_AMBAR = '#e8a430'
COLOR_CIAN = '#4dc9e6'
COLOR_TEXTO = '#f0ece0'
COLOR_FONDO = '#080a12'

def _get_dark_layout():
    """Layout base optimizado para que no desborde."""
    return dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLOR_TEXTO, family='DM Mono, monospace', size=10),
        title_font=dict(family='Playfair Display, serif', size=20, color=COLOR_AMBAR),
        margin=dict(t=40, b=40, l=40, r=20),
        autosize=True,
        xaxis=dict(
            gridcolor='rgba(240, 236, 224, 0.05)', # Muy sutil, cercano al fondo
            gridwidth=0.5,
            zeroline=False
        ),
        yaxis=dict(
            gridcolor='rgba(240, 236, 224, 0.05)',
            gridwidth=0.5,
            zeroline=False
        )
    )

def _fig_to_html(fig):
    """Convierte figura a HTML asegurando responsividad total."""
    return fig.to_html(
        full_html=False, 
        include_plotlyjs=False, 
        config={'responsive': True, 'displayModeBar': False}
    )

# --- 2.1 ANÁLISIS DE GÉNEROS ---

def chart_top_genres_by_count():
    res = db.session.query(Genre.name, func.count(Genre.id).label('count'))\
            .join(album_genres, Genre.id == album_genres.c.genre_id)\
            .filter(album_genres.c.is_primary == True)\
            .group_by(Genre.id).order_by(db.desc('count')).limit(15).all()
    
    df = pd.DataFrame(res, columns=['Genre', 'Count'])
    fig = px.bar(df, x='Count', y='Genre', orientation='h',
                 title='Géneros Predominantes',
                 color_discrete_sequence=[COLOR_CIAN])
    
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

def chart_genres_by_avg_rating():
    res = db.session.query(Genre.name, func.avg(Album.avg_rating).label('avg'))\
            .join(album_genres, Genre.id == album_genres.c.genre_id)\
            .join(Album, Album.id == album_genres.c.album_id)\
            .group_by(Genre.id).having(func.count(Album.id) >= 20)\
            .order_by(db.desc('avg')).limit(15).all()
    
    df = pd.DataFrame(res, columns=['Genre', 'Rating'])
    fig = px.bar(df, x='Rating', y='Genre', orientation='h',
                 title='Calificación Media',
                 color_discrete_sequence=[COLOR_AMBAR],
                 range_x=[3.5, 4.5])
    
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

def chart_genres_by_listeners():
    res = db.session.query(Genre.name, func.avg(Album.lastfm_listeners).label('listeners'))\
            .join(album_genres, Genre.id == album_genres.c.genre_id)\
            .join(Album, Album.id == album_genres.c.album_id)\
            .group_by(Genre.id).having(func.count(Album.id) >= 15)\
            .order_by(db.desc('listeners')).limit(15).all()
    
    df = pd.DataFrame(res, columns=['Genre', 'Listeners'])
    fig = px.bar(df, x='Listeners', y='Genre', orientation='h',
                 title='Géneros con Más Oyentes',
                 color_discrete_sequence=[COLOR_CIAN])
    
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

# --- 2.2 ANÁLISIS DE LABELS ---

def chart_top_labels_by_count():
    # Obtenemos los 15 sellos con más discos (Top 15)
    res = db.session.query(Album.label, func.count(Album.id).label('count'))\
            .filter(Album.label != None, Album.label != '[no label]', Album.label != '')\
            .group_by(Album.label).order_by(db.desc('count')).limit(15).all()
    
    df = pd.DataFrame(res, columns=['Label', 'Count'])
    
    # Ordenamos para que el mayor aparezca arriba en el gráfico horizontal
    df = df.sort_values('Count', ascending=True)

    fig = px.bar(df, x='Count', y='Label', orientation='h',
                 title='Sellos con más Lanzamientos',
                 color_discrete_sequence=[COLOR_CIAN])
    
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

def chart_labels_by_avg_rating():
    # Obtenemos sello, promedio de rating y conteo de álbumes
    res = db.session.query(
        Album.label, 
        func.avg(Album.avg_rating).label('avg'),
        func.count(Album.id).label('count')
    )\
    .filter(Album.label != None, Album.label != '[no label]', Album.label != '')\
    .group_by(Album.label).having(func.count(Album.id) >= 10)\
    .order_by(db.desc('avg')).limit(15).all()
    
    df = pd.DataFrame(res, columns=['Label', 'Rating', 'Count'])
    
    # Para que el mejor aparezca ARRIBA en el gráfico horizontal, 
    # Plotly suele requerir el orden inverso o configurar el eje.
    # Usaremos el orden descendente y nos aseguraremos de que Plotly lo respete.
    df = df.sort_values('Rating', ascending=True) 

    fig = px.bar(df, x='Rating', y='Label', orientation='h',
                 title='Sellos con Mejores Calificaciones',
                 color_discrete_sequence=[COLOR_AMBAR],
                 text='Count', # Añadimos el conteo de discos
                 range_x=[3.5, 4.1])
    
    fig.update_traces(texttemplate='%{text} álbumes', textposition='outside')
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

# --- 2.3 ANÁLISIS DE ARTISTAS ---

def chart_top_artists():
    res = db.session.query(Album.artist, func.count(Album.id).label('count'))\
            .group_by(Album.artist).order_by(db.desc('count')).limit(15).all()
    
    df = pd.DataFrame(res, columns=['Artist', 'Album Count'])
    fig = px.bar(df, x='Album Count', y='Artist', orientation='h',
                 title='Artistas con más Álbumes en el Top',
                 color_discrete_sequence=[COLOR_CIAN])
    
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

# --- 2.4 ANÁLISIS TEMPORAL ---

def chart_rating_by_year():
    res = db.session.query(func.strftime('%Y', Album.release_date).label('year'), 
                           func.avg(Album.avg_rating).label('avg'))\
            .filter(Album.release_date != None)\
            .group_by('year').all()
    
    df = pd.DataFrame(res, columns=['Year', 'Rating'])
    df = df.sort_values('Year')
    fig = px.line(df, x='Year', y='Rating', title='Evolución de Ratings',
                  color_discrete_sequence=[COLOR_AMBAR])
    
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

def chart_albums_by_year():
    res = db.session.query(func.strftime('%Y', Album.release_date).label('year'), 
                           func.count(Album.id).label('count'))\
            .filter(Album.release_date != None)\
            .group_by('year').all()
    
    df = pd.DataFrame(res, columns=['Year', 'Count'])
    df = df.sort_values('Year')
    fig = px.bar(df, x='Year', y='Count', title='Lanzamientos por Año',
                 color_discrete_sequence=[COLOR_CIAN])
    
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

def chart_rating_by_decade():
    # Obtenemos años y ratings
    res = db.session.query(func.strftime('%Y', Album.release_date).label('year'), 
                           Album.avg_rating)\
            .filter(Album.release_date != None).all()
    
    df = pd.DataFrame(res, columns=['Year', 'Rating'])
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df.dropna(subset=['Year'])
    
    # Agrupamos por década (ej: 1974 -> 1970)
    df['DecadeInt'] = (df['Year'] // 10) * 10
    
    df_grouped = df.groupby('DecadeInt')['Rating'].mean().reset_index()
    df_grouped = df_grouped.sort_values('DecadeInt')
    df_grouped['Decade'] = df_grouped['DecadeInt'].astype(int).astype(str) + 's'
    
    # Rango en 3.0 para que se vean las décadas recientes (que rondan 3.3)
    fig = px.bar(df_grouped, x='Decade', y='Rating', title='Promedio por Década',
                 color_discrete_sequence=[COLOR_AMBAR], range_y=[3.0, 3.9])
    
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

# --- 2.5 CORRELACIONES ---

def chart_rym_rating_vs_listeners():
    res = db.session.query(Album.avg_rating, Album.lastfm_listeners, Album.title, Album.artist).all()
    df = pd.DataFrame(res, columns=['Rating', 'Listeners', 'Title', 'Artist'])
    
    # Calcular el Ranking RYM basado en el rating (1 es el mejor)
    df = df.sort_values('Rating', ascending=False)
    df['RYM_Rank'] = range(1, len(df) + 1)
    
    fig = px.scatter(df, x='RYM_Rank', y='Listeners', log_y=True,
                     hover_data=['Title', 'Artist', 'Rating'],
                     title='Calidad (Rank) vs Popularidad (Oyentes)',
                     color_discrete_sequence=[COLOR_CIAN],
                     opacity=0.5, height=450)
    
    fig.update_layout(**_get_dark_layout())
    fig.update_xaxes(title='Posición en RYM (Rank)')
    fig.update_yaxes(title='Oyentes Last.fm (Log)')
    return _fig_to_html(fig)

def chart_rym_rating_vs_playcount():
    res = db.session.query(Album.avg_rating, Album.lastfm_playcount, Album.title, Album.artist).all()
    df = pd.DataFrame(res, columns=['Rating', 'Playcount', 'Title', 'Artist'])
    
    fig = px.scatter(df, x='Rating', y='Playcount', log_y=True,
                     hover_data=['Title', 'Artist'],
                     title='Rating vs Reproducciones',
                     color_discrete_sequence=[COLOR_AMBAR],
                     opacity=0.6, height=400)
    
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

def chart_ratingcount_vs_listeners():
    res = db.session.query(Album.rating_count, Album.lastfm_listeners, Album.title, Album.artist).all()
    df = pd.DataFrame(res, columns=['RYM_Ratings', 'LastFM_Listeners', 'Title', 'Artist'])
    
    fig = px.scatter(df, x='RYM_Ratings', y='LastFM_Listeners', log_x=True, log_y=True,
                     hover_data=['Title', 'Artist'],
                     title='Ratings RYM vs Oyentes Last.fm',
                     color_discrete_sequence=[COLOR_CIAN],
                     opacity=0.6, height=450)
    
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

def get_rankings_data():
    """
    Retorna un diccionario con los datos de rankings (Géneros, Sellos, Artistas)
    para ser renderizados como componentes nativos en el template.
    """
    data = {}

    # 1. Top Géneros por Conteo
    genres_count = db.session.query(Genre.name, func.count(Genre.id).label('count'))\
            .join(album_genres, Genre.id == album_genres.c.genre_id)\
            .filter(album_genres.c.is_primary == True)\
            .group_by(Genre.id).order_by(db.desc('count')).limit(15).all()
    data['genres_count'] = [dict(name=r[0], count=r[1]) for r in genres_count]

    # 2. Géneros por Rating
    genres_rating = db.session.query(Genre.name, func.avg(Album.avg_rating).label('avg'))\
            .join(album_genres, Genre.id == album_genres.c.genre_id)\
            .join(Album, Album.id == album_genres.c.album_id)\
            .group_by(Genre.id).having(func.count(Album.id) >= 20)\
            .order_by(db.desc('avg')).limit(15).all()
    data['genres_rating'] = [dict(name=r[0], avg=round(r[1], 2)) for r in genres_rating]

    # 3. Sellos por Conteo
    labels_count = db.session.query(Album.label, func.count(Album.id).label('count'))\
            .filter(Album.label != None, Album.label != '[no label]', Album.label != '')\
            .group_by(Album.label).order_by(db.desc('count')).limit(15).all()
    data['labels_count'] = [dict(name=r[0], count=r[1]) for r in labels_count]

    # 4. Sellos por Rating
    labels_rating = db.session.query(
        Album.label, 
        func.avg(Album.avg_rating).label('avg'),
        func.count(Album.id).label('count')
    )\
    .filter(Album.label != None, Album.label != '[no label]', Album.label != '')\
    .group_by(Album.label).having(func.count(Album.id) >= 10)\
    .order_by(db.desc('avg')).limit(15).all()
    data['labels_rating'] = [dict(name=r[0], avg=round(r[1], 2), count=r[2]) for r in labels_rating]

    # 5. Top Artistas
    artists_count = db.session.query(Album.artist, func.count(Album.id).label('count'))\
            .group_by(Album.artist).order_by(db.desc('count')).limit(15).all()
    data['artists_count'] = [dict(name=r[0], count=r[1]) for r in artists_count]

    return data
