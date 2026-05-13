import plotly.express as px
import plotly.graph_objects as go
from app.models import Album, Genre, album_genres
from app import db
from sqlalchemy import func
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from app.recommender.engine import get_data
from app.recommender.constants import MEGA_CLUSTER_MAP, MEGA_CLUSTER_COLORS, CLUSTER_NAMES

# --- 1. CONFIGURACIÓN BASE ---

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
        xaxis=dict(gridcolor='rgba(240, 236, 224, 0.05)', gridwidth=0.5, zeroline=False),
        yaxis=dict(gridcolor='rgba(240, 236, 224, 0.05)', gridwidth=0.5, zeroline=False)
    )

_LAYOUT_SCATTER = dict(
    title=None,
    xaxis_title='', yaxis_title='',
    xaxis=dict(showticklabels=False, showgrid=False, zeroline=False, showline=False, ticks=''),
    yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, showline=False, ticks=''),
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    showlegend=True,
    legend=dict(
        orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5,
        font=dict(size=10, family='DM Mono, monospace')
    ),
    autosize=True,
    margin=dict(t=30, b=0, l=0, r=0),
    hoverlabel=dict(
        bgcolor='rgba(8,10,18,0.95)',
        bordercolor='rgba(232,164,48,0.6)',
        font=dict(family='DM Mono, monospace', size=12, color='#f0ece0'),
    ),
)

def _fig_to_html(fig):
    """Convierte figura a HTML asegurando responsividad total."""
    return fig.to_html(
        full_html=False, 
        include_plotlyjs=False, 
        config={'responsive': True, 'displayModeBar': False}
    )

# --- 2. RANKINGS Y ESTADÍSTICAS (DB BASED) ---

def get_rankings_data():
    """Retorna diccionarios de rankings desde la DB para CSS Bars."""
    data = {}
    genres_count = db.session.query(Genre.name, func.count(Genre.id).label('count'))\
            .join(album_genres, Genre.id == album_genres.c.genre_id)\
            .filter(album_genres.c.is_primary == True)\
            .group_by(Genre.id).order_by(db.desc('count')).limit(15).all()
    data['genres_count'] = [dict(name=r[0], count=r[1]) for r in genres_count]

    genres_rating = db.session.query(Genre.name, func.avg(Album.avg_rating).label('avg'))\
            .join(album_genres, Genre.id == album_genres.c.genre_id)\
            .join(Album, Album.id == album_genres.c.album_id)\
            .group_by(Genre.id).having(func.count(Album.id) >= 20)\
            .order_by(db.desc('avg')).limit(15).all()
    data['genres_rating'] = [dict(name=r[0], avg=round(r[1], 2)) for r in genres_rating]

    labels_count = db.session.query(Album.label, func.count(Album.id).label('count'))\
            .filter(Album.label != None, Album.label != '[no label]', Album.label != '')\
            .group_by(Album.label).order_by(db.desc('count')).limit(15).all()
    data['labels_count'] = [dict(name=r[0], count=r[1]) for r in labels_count]

    labels_rating = db.session.query(Album.label, func.avg(Album.avg_rating).label('avg'), func.count(Album.id).label('count'))\
            .filter(Album.label != None, Album.label != '[no label]', Album.label != '')\
            .group_by(Album.label).having(func.count(Album.id) >= 10)\
            .order_by(db.desc('avg')).limit(15).all()
    data['labels_rating'] = [dict(name=r[0], avg=round(r[1], 2), count=r[2]) for r in labels_rating]

    artists_count = db.session.query(Album.artist, func.count(Album.id).label('count'))\
            .group_by(Album.artist).order_by(db.desc('count')).limit(15).all()
    data['artists_count'] = [dict(name=r[0], count=r[1]) for r in artists_count]

    # Rankings desde el Recomenedador (Clusters)
    rec_data = get_data()
    if rec_data is not None:
        df_rec = rec_data['album_info'].copy()
        df_rec['cluster'] = rec_data['cluster_labels']
        df_rec['mega'] = rec_data['mega_clusters']

        # Micro-clusters (Count)
        c_counts = df_rec['cluster'].value_counts()
        data['clusters_count'] = []
        for cid, count in c_counts.head(15).items():
            if cid == -1: continue
            name = CLUSTER_NAMES.get(int(cid), f"Cluster {cid}")
            data['clusters_count'].append({'name': name, 'count': int(count)})
            
        # Micro-clusters (Rating)
        c_ratings = df_rec.groupby('cluster')['avg_rating'].mean().sort_values(ascending=False)
        data['clusters_rating'] = []
        for cid, avg in c_ratings.head(15).items():
            if cid == -1: continue
            name = CLUSTER_NAMES.get(int(cid), f"Cluster {cid}")
            data['clusters_rating'].append({'name': name, 'avg': round(avg, 2)})

        # Macro-clusters (Count)
        m_counts = df_rec['mega'].value_counts()
        data['mega_count'] = []
        for mname, count in m_counts.items():
            if mname == "Otros": continue
            data['mega_count'].append({'name': mname, 'count': int(count)})
            
        # Macro-clusters (Rating)
        m_ratings = df_rec.groupby('mega')['avg_rating'].mean().sort_values(ascending=False)
        data['mega_rating'] = []
        for mname, avg in m_ratings.items():
            if mname == "Otros": continue
            data['mega_rating'].append({'name': mname, 'avg': round(avg, 2)})

    return data

def make_histogram_html(df, column, color, nbins=20, height=140):
    """Genera un histograma simple en HTML."""
    fig = px.histogram(df, x=column, nbins=nbins, color_discrete_sequence=[color])
    fig.update_layout(**_get_dark_layout())
    fig.update_layout(height=height, margin=dict(t=5, b=5, l=5, r=5), xaxis_title=None, yaxis_title=None, showlegend=False)
    return _fig_to_html(fig)

# --- 3. GRÁFICOS TEMPORALES Y CORRELACIONES (DB BASED) ---

def chart_rating_by_year():
    res = db.session.query(func.strftime('%Y', Album.release_date).label('year'), func.avg(Album.avg_rating).label('avg'))\
            .filter(Album.release_date != None).group_by('year').all()
    df = pd.DataFrame(res, columns=['Year', 'Rating']).sort_values('Year')
    # Solo mostrar años con sentido histórico en este dataset
    df['Year'] = pd.to_numeric(df['Year'])
    df = df[df['Year'] >= 1950]
    
    fig = px.line(df, x='Year', y='Rating', title='Evolución de Ratings', color_discrete_sequence=[COLOR_AMBAR], markers=True, height=450)
    fig.update_layout(**_get_dark_layout())
    # Forzar rangos para evitar zoom out si hay datos dispersos
    fig.update_yaxes(range=[3.0, 4.2], dtick=0.2)
    fig.update_xaxes(range=[df['Year'].min() - 0.5, df['Year'].max() + 0.5])
    return _fig_to_html(fig)

def chart_albums_by_year():
    res = db.session.query(func.strftime('%Y', Album.release_date).label('year'), func.count(Album.id).label('count'))\
            .filter(Album.release_date != None).group_by('year').all()
    df = pd.DataFrame(res, columns=['Year', 'Count']).sort_values('Year')
    fig = px.bar(df, x='Year', y='Count', title='Lanzamientos por Año', color_discrete_sequence=[COLOR_CIAN])
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

def chart_rating_by_decade():
    res = db.session.query(func.strftime('%Y', Album.release_date).label('year'), Album.avg_rating).filter(Album.release_date != None).all()
    df = pd.DataFrame(res, columns=['Year', 'Rating'])
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df.dropna(subset=['Year'])
    df['DecadeInt'] = (df['Year'] // 10) * 10
    df_grouped = df.groupby('DecadeInt')['Rating'].mean().reset_index().sort_values('DecadeInt')
    df_grouped['Decade'] = df_grouped['DecadeInt'].astype(int).astype(str) + 's'
    fig = px.bar(df_grouped, x='Decade', y='Rating', title='Promedio por Década', color_discrete_sequence=[COLOR_AMBAR], range_y=[3.0, 3.9])
    fig.update_layout(**_get_dark_layout())
    return _fig_to_html(fig)

def chart_rym_rating_vs_listeners():
    res = db.session.query(Album.avg_rating, Album.lastfm_listeners, Album.title, Album.artist).all()
    df = pd.DataFrame(res, columns=['Rating', 'Listeners', 'Title', 'Artist'])
    df['Listeners'] = df['Listeners'].fillna(0) + 1
    df = df.sort_values('Rating', ascending=False)
    df['RYM_Rank'] = range(1, len(df) + 1)
    
    fig = px.scatter(df, x='RYM_Rank', y='Listeners', log_y=True, 
                     hover_data=['Title', 'Artist', 'Rating'], 
                     color_discrete_sequence=[COLOR_CIAN], opacity=0.4, height=450,
                     render_mode='webgl')
    
    fig.update_layout(**_get_dark_layout())
    fig.update_layout(title=None) # Título ya está en el HTML
    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
    return _fig_to_html(fig)

def chart_rym_rating_vs_playcount():
    res = db.session.query(Album.avg_rating, Album.lastfm_playcount, Album.title, Album.artist).all()
    df = pd.DataFrame(res, columns=['Rating', 'Playcount', 'Title', 'Artist'])
    df['Playcount'] = df['Playcount'].fillna(0) + 1
    
    fig = px.scatter(df, x='Rating', y='Playcount', log_y=True, 
                     hover_data=['Title', 'Artist'], 
                     color_discrete_sequence=[COLOR_AMBAR], opacity=0.4, height=450,
                     render_mode='webgl')
    
    fig.update_layout(**_get_dark_layout())
    fig.update_layout(title=None) # Título ya está en el HTML
    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
    return _fig_to_html(fig)

def chart_mega_cluster_playcount_boxplot():
    rec_data = get_data()
    if rec_data is None: return ""
    
    df = rec_data['album_info'].copy()
    df['galaxy'] = rec_data['mega_clusters']
    df = df[df['galaxy'] != 'Otros']
    
    # Ordenar por mediana
    order = df.groupby('galaxy')['lastfm_playcount'].median().sort_values(ascending=False).index
    
    fig = px.box(df, x='galaxy', y='lastfm_playcount', 
                 color='galaxy', color_discrete_map=MEGA_CLUSTER_COLORS,
                 category_orders={'galaxy': list(order)},
                 points=False, log_y=True,
                 height=500)
    
    fig.update_layout(**_get_dark_layout())
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title='Reproducciones (log)', title=None)
    # Rango fijo para evitar zoom out en pestañas ocultas
    fig.update_yaxes(range=[2.5, 8]) # De 300 a 100M
    return _fig_to_html(fig)



# --- 4. VISUALIZACIONES BASADAS EN CACHÉ (RECOMENDADOR) ---

def make_ratings_chart():
    data = get_data()
    if data is None: return ""
    return make_histogram_html(data['album_info'], 'avg_rating', COLOR_AMBAR, nbins=80, height=180)

def make_listeners_chart():
    data = get_data()
    if data is None: return ""
    info = data['album_info'].copy()
    info['listeners_chart'] = info['lastfm_listeners'].fillna(0)
    return make_histogram_html(info, 'listeners_chart', COLOR_CIAN, nbins=40, height=180)

def make_radar_chart(album_id):
    data = get_data()
    if data is None: return ""
    info = data['album_info']
    row  = info[info['id'] == album_id]
    if row.empty: return ""
    row = row.iloc[0]
    p_rating    = (info['avg_rating'].fillna(0)        <= (row['avg_rating']        or 0)).mean()
    p_ratings   = (info['rating_count'].fillna(0)      <= (row['rating_count']      or 0)).mean()
    p_listeners = (info['lastfm_listeners'].fillna(0)  <= (row['lastfm_listeners']  or 0)).mean()
    p_plays     = (info['lastfm_playcount'].fillna(0)  <= (row['lastfm_playcount']  or 0)).mean()
    categories = ['RATING', 'RATINGS', 'OYENTES', 'PLAYS', 'RATING']
    values     = [p_rating, p_ratings, p_listeners, p_plays, p_rating]
    fig = go.Figure(data=go.Scatterpolar(r=values, theta=categories, fill='toself', fillcolor='rgba(232, 164, 48, 0.15)', line=dict(color='#e8a430', width=1.5), marker=dict(color='#e8a430', size=6), customdata=[row['avg_rating'], row['rating_count'], row['lastfm_listeners'], row['lastfm_playcount'], row['avg_rating']], hovertemplate='<b>%{theta}</b><br>Valor real: %{customdata:,.2f}<br>Percentil: %{r:.1%}<extra></extra>'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1], showticklabels=False, gridcolor='rgba(255,255,255,0.06)'), bgcolor='rgba(0,0,0,0)'), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=30, r=30, t=30, b=30), height=240)
    return _fig_to_html(fig)

def get_affinities(results):
    data = get_data()
    if data is None or not results: return {}
    info, album_ids = data['album_info'], data['album_ids']
    id_to_idx = {aid: i for i, aid in enumerate(album_ids)}
    result_rows = [info.iloc[id_to_idx[r['album_id']]] for r in results if r['album_id'] in id_to_idx]
    if not result_rows: return {}
    def _get_top(rows, col):
        counts = {}
        for r in rows:
            for v in str(r[col]).split(', '):
                v = v.strip()
                if v: counts[v] = counts.get(v, 0) + 1
        if not counts: return []
        top = sorted(counts.items(), key=lambda x: -x[1])[:15]
        mx = top[0][1]
        return [{'name': k, 'count': v, 'pct': round((v / mx) * 100)} for k, v in top]
    return {'genres': _get_top(result_rows, 'genres'), 'descriptors': _get_top(result_rows, 'descriptors')}

def get_scatter_html(seed_id=None, recommended_ids=None, highlighted_id=None, show_legend=True):
    data = get_data()
    if data is None: return ""
    coords, clusters, info, album_ids, mega_cl = data['tsne_coords'], data['cluster_labels'], data['album_info'], data['album_ids'], data['mega_clusters']
    id_to_idx = {aid: i for i, aid in enumerate(album_ids)}
    df = pd.DataFrame({'x': coords[:, 0], 'y': coords[:, 1], 'galaxy': mega_cl, 'title': info['title'], 'artist': info['artist'], 'genres': info['genres'], 'role': 'Otros', 'cluster': [f"C{c}: {CLUSTER_NAMES.get(int(c), 'Otros')}" if c != -1 else "Otros" for c in clusters]})
    if seed_id and seed_id in id_to_idx: df.loc[id_to_idx[seed_id], 'role'] = '⭐ Semilla'
    if recommended_ids:
        for rid in recommended_ids:
            if rid in id_to_idx and df.loc[id_to_idx[rid], 'role'] != '⭐ Semilla': df.loc[id_to_idx[rid], 'role'] = '🎯 Recomendado'
    if highlighted_id and highlighted_id in id_to_idx: df.loc[id_to_idx[highlighted_id], 'role'] = '🔍 Buscado'
    has_h = bool(seed_id or recommended_ids or highlighted_id)
    fig = px.scatter(df[df['role'] == 'Otros'] if has_h else df, x='x', y='y', color='galaxy', color_discrete_map=MEGA_CLUSTER_COLORS, custom_data=['title', 'artist', 'genres', 'cluster', 'galaxy'], opacity=0.35 if has_h else 0.75, render_mode='webgl', labels={'galaxy': ''})
    fig.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br><span style="color:#e8a430">%{customdata[4]}</span> > %{customdata[3]}<extra></extra>')
    if recommended_ids:
        recs = df[df['role'] == '🎯 Recomendado']
        fig.add_trace(go.Scattergl(x=recs['x'], y=recs['y'], mode='markers', marker=dict(size=12, color='red', symbol='diamond', line=dict(width=1, color='white')), name='🎯 Recomendados', customdata=recs[['title', 'artist']].values, hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br><span style="color:#ff6b6b;">🎯 Recomendado</span><extra></extra>'))
    if seed_id:
        seeds = df[df['role'] == '⭐ Semilla']
        fig.add_trace(go.Scattergl(x=seeds['x'], y=seeds['y'], mode='markers', marker=dict(size=18, color='gold', symbol='star', line=dict(width=2, color='white')), name='⭐ Semilla', customdata=seeds[['artist', 'cluster', 'title']].values, hovertemplate='<b>%{customdata[2]}</b><br>%{customdata[0]}<br><span style="color:gold;">⭐ Semilla</span><extra></extra>'))
    if highlighted_id:
        h = df[df['role'] == '🔍 Buscado']
        fig.add_trace(go.Scattergl(x=h['x'], y=h['y'], mode='markers', marker=dict(size=12, color='white', symbol='circle', line=dict(width=3, color='#4dc9e6')), name='🔍 Buscado', customdata=h[['artist', 'cluster', 'title']].values, hovertemplate='<b>%{customdata[2]}</b><br>%{customdata[0]}<br><span style="color:#4dc9e6;">🔍 Buscado</span><extra></extra>'))
    
    fig.update_layout(**_LAYOUT_SCATTER)
    if not show_legend:
        fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        
    return _fig_to_html(fig)

def get_filtered_scatter_html(filtered_ids):
    data = get_data()
    if data is None or not filtered_ids: return ""
    coords, clusters, info, album_ids, mega_cl = data['tsne_coords'], data['cluster_labels'], data['album_info'], data['album_ids'], data['mega_clusters']
    import numpy as np
    mask = np.array([aid in filtered_ids for aid in album_ids])
    if mask.sum() == 0: return ""
    df = pd.DataFrame({'x': coords[mask, 0], 'y': coords[mask, 1], 'galaxy': [mega_cl[i] for i, v in enumerate(mask) if v], 'title': info[mask]['title'].values, 'artist': info[mask]['artist'].values, 'genres': info[mask]['genres'].values, 'cluster': [f"C{c}: {CLUSTER_NAMES.get(int(c), 'Otros')}" if c != -1 else "Otros" for c in clusters[mask]]}).sort_values(by='galaxy')
    fig = px.scatter(df, x='x', y='y', color='galaxy', color_discrete_map=MEGA_CLUSTER_COLORS, custom_data=['title', 'artist', 'genres', 'cluster', 'galaxy'], opacity=0.85, labels={'galaxy': ''})
    fig.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br><span style="color:#e8a430">%{customdata[4]}</span> > %{customdata[3]}<extra></extra>')
    fig.update_layout(**_LAYOUT_SCATTER)
    return _fig_to_html(fig)

def get_user_collection_map_html(album_counts):
    data = get_data()
    if data is None or not album_counts: return ""
    coords, info, album_ids, clusters, mega_cl = data['tsne_coords'], data['album_info'], data['album_ids'], data['cluster_labels'], data['mega_clusters']
    import numpy as np
    ids_arr = np.array(album_ids)
    u_ids = set(album_counts.keys())
    mask = np.array([aid in u_ids for aid in ids_arr])
    if mask.sum() == 0: return ""
    matched = ids_arr[mask]
    df = pd.DataFrame({'x': coords[mask, 0], 'y': coords[mask, 1], 'galaxy': [mega_cl[i] for i, v in enumerate(mask) if v], 'title': info[mask]['title'].values, 'artist': info[mask]['artist'].values, 'count': [album_counts.get(int(aid), 1) for aid in matched], 'cluster': [f"C{c}: {CLUSTER_NAMES.get(int(c), 'Otros')}" if c != -1 else "Otros" for c in clusters[mask]]}).sort_values(by='galaxy')
    df['size'] = np.log1p(df['count']) * 8 + 4
    fig = px.scatter(df, x='x', y='y', color='galaxy', color_discrete_map=MEGA_CLUSTER_COLORS, size='size', custom_data=['title', 'artist', 'count', 'cluster', 'galaxy'], render_mode='webgl', opacity=0.9, labels={'galaxy': ''})
    fig.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Canciones: %{customdata[2]}<br><span style="color:#e8a430">%{customdata[4]}</span> > %{customdata[3]}<extra></extra>')
    fig.update_layout(**_LAYOUT_SCATTER)
    return _fig_to_html(fig)

