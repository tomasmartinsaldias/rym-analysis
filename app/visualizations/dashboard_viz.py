import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from app import db
from sqlalchemy import func
from app.models import Album
from app.services.recommender.engine import get_data
from app.services.recommender.constants import MEGA_CLUSTER_COLORS, CLUSTER_NAMES
from app.visualizations.common import (
    COLOR_AMBAR, COLOR_CIAN, get_dark_layout, LAYOUT_SCATTER, fig_to_html
)

def make_histogram_html(df, column, color, nbins=20, height=140):
    """Genera un histograma simple en HTML."""
    fig = px.histogram(df, x=column, nbins=nbins, color_discrete_sequence=[color])
    fig.update_layout(**get_dark_layout())
    fig.update_layout(height=height, margin=dict(t=5, b=5, l=5, r=5), xaxis_title=None, yaxis_title=None, showlegend=False)
    return fig_to_html(fig)

def chart_rating_by_year():
    res = db.session.query(func.strftime('%Y', Album.release_date).label('year'), func.avg(Album.avg_rating).label('avg'))\
            .filter(Album.release_date != None).group_by('year').all()
    df = pd.DataFrame(res, columns=['Year', 'Rating']).sort_values('Year')
    df['Year'] = pd.to_numeric(df['Year'])
    df = df[df['Year'] >= 1950]
    
    fig = px.line(df, x='Year', y='Rating', title='Evolución de Ratings', color_discrete_sequence=[COLOR_AMBAR], markers=True, height=450)
    fig.update_layout(**get_dark_layout())
    fig.update_yaxes(range=[3.0, 4.2], dtick=0.2)
    fig.update_xaxes(range=[df['Year'].min() - 0.5, df['Year'].max() + 0.5])
    return fig_to_html(fig)

def chart_albums_by_year():
    res = db.session.query(func.strftime('%Y', Album.release_date).label('year'), func.count(Album.id).label('count'))\
            .filter(Album.release_date != None).group_by('year').all()
    df = pd.DataFrame(res, columns=['Year', 'Count']).sort_values('Year')
    fig = px.bar(df, x='Year', y='Count', title='Lanzamientos por Año', color_discrete_sequence=[COLOR_CIAN])
    fig.update_layout(**get_dark_layout())
    return fig_to_html(fig)

def chart_rating_by_decade():
    res = db.session.query(func.strftime('%Y', Album.release_date).label('year'), Album.avg_rating).filter(Album.release_date != None).all()
    df = pd.DataFrame(res, columns=['Year', 'Rating'])
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df.dropna(subset=['Year'])
    df['DecadeInt'] = (df['Year'] // 10) * 10
    df_grouped = df.groupby('DecadeInt')['Rating'].mean().reset_index().sort_values('DecadeInt')
    df_grouped['Decade'] = df_grouped['DecadeInt'].astype(int).astype(str) + 's'
    fig = px.bar(df_grouped, x='Decade', y='Rating', title='Promedio por Década', color_discrete_sequence=[COLOR_AMBAR], range_y=[3.0, 3.9])
    fig.update_layout(**get_dark_layout())
    return fig_to_html(fig)

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
    
    fig.update_layout(**get_dark_layout())
    fig.update_layout(title=None)
    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
    return fig_to_html(fig)

def chart_rym_rating_vs_playcount():
    res = db.session.query(Album.avg_rating, Album.lastfm_playcount, Album.title, Album.artist).all()
    df = pd.DataFrame(res, columns=['Rating', 'Playcount', 'Title', 'Artist'])
    df['Playcount'] = df['Playcount'].fillna(0) + 1
    
    fig = px.scatter(df, x='Rating', y='Playcount', log_y=True, 
                     hover_data=['Title', 'Artist'], 
                     color_discrete_sequence=[COLOR_AMBAR], opacity=0.4, height=450,
                     render_mode='webgl')
    
    fig.update_layout(**get_dark_layout())
    fig.update_layout(title=None)
    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
    return fig_to_html(fig)

def chart_playcount_vs_listeners():
    res = db.session.query(Album.lastfm_listeners, Album.lastfm_playcount, Album.title, Album.artist).all()
    df = pd.DataFrame(res, columns=['Listeners', 'Playcount', 'Title', 'Artist'])
    df = df.dropna(subset=['Listeners', 'Playcount'])
    
    fig = px.scatter(df, x='Listeners', y='Playcount', 
                     hover_data=['Title', 'Artist'], 
                     color_discrete_sequence=[COLOR_CIAN], opacity=0.4, height=450,
                     render_mode='webgl')
    
    fig.update_layout(**get_dark_layout())
    fig.update_layout(title=None)
    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Oyentes (Last.fm)")
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Reproducciones (Last.fm)")
    return fig_to_html(fig)

def chart_rym_vs_lastfm():
    res = db.session.query(Album.rating_count, Album.lastfm_listeners, Album.title, Album.artist, Album.avg_rating).all()
    df = pd.DataFrame(res, columns=['RYM_Votes', 'Listeners', 'Title', 'Artist', 'Rating'])
    df = df.dropna(subset=['RYM_Votes', 'Listeners'])
    df = df[df['Listeners'] >= 1000]
    df['ratio'] = df['RYM_Votes'] / (df['Listeners'] + 1)
    
    fig = px.scatter(df, x='Listeners', y='RYM_Votes', 
                     log_x=True, log_y=True,
                     hover_data=['Title', 'Artist', 'Rating'], 
                     color_discrete_sequence=[COLOR_AMBAR], opacity=0.4, height=500,
                     render_mode='webgl')
    
    fig.update_layout(**get_dark_layout())
    fig.update_layout(title=None)
    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Oyentes Last.fm (Log)")
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Votos RYM (Log)")
    return fig_to_html(fig)

def chart_mega_cluster_playcount_boxplot():
    rec_data = get_data()
    if rec_data is None: return ""
    df = rec_data['album_info'].copy()
    df['galaxy'] = rec_data['mega_clusters']
    df = df[df['galaxy'] != 'Otros']
    order = df.groupby('galaxy')['lastfm_playcount'].median().sort_values(ascending=False).index
    fig = px.box(df, x='galaxy', y='lastfm_playcount', 
                 color='galaxy', color_discrete_map=MEGA_CLUSTER_COLORS,
                 category_orders={'galaxy': list(order)},
                 points=False, log_y=True,
                 height=500)
    fig.update_layout(**get_dark_layout())
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title='Reproducciones (log)', title=None)
    fig.update_yaxes(range=[2.5, 8])
    return fig_to_html(fig)

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
    return fig_to_html(fig)

def get_scatter_html(seed_id=None, recommended_ids=None, highlighted_id=None, show_legend=True):
    data = get_data()
    if data is None: return ""
    coords, clusters, info, album_ids, mega_cl = data['tsne_coords'], data['cluster_labels'], data['album_info'], data['album_ids'], data['mega_clusters']
    id_to_idx = {aid: i for i, aid in enumerate(album_ids)}
    df = pd.DataFrame({'x': coords[:, 0], 'y': coords[:, 1], 'galaxy': mega_cl, 'title': info['title'], 'artist': info['artist'], 'genres': info['genres'], 'role': 'Otros', 'cluster': [f"C{c}: {CLUSTER_NAMES.get(int(c), 'Otros')}" if c != -1 else "Otros" for c in clusters]})
    if seed_id and seed_id in id_to_idx: df.loc[id_to_idx[seed_id], 'role'] = 'Semilla'
    if recommended_ids:
        for rid in recommended_ids:
            if rid in id_to_idx and df.loc[id_to_idx[rid], 'role'] != 'Semilla': df.loc[id_to_idx[rid], 'role'] = 'Recomendado'
    if highlighted_id and highlighted_id in id_to_idx: df.loc[id_to_idx[highlighted_id], 'role'] = 'Buscado'
    has_h = bool(seed_id or recommended_ids or highlighted_id)
    fig = px.scatter(df[df['role'] == 'Otros'] if has_h else df, x='x', y='y', color='galaxy', color_discrete_map=MEGA_CLUSTER_COLORS, custom_data=['title', 'artist', 'genres', 'cluster', 'galaxy'], opacity=0.35 if has_h else 0.75, render_mode='webgl', labels={'galaxy': ''})
    fig.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br><span style="color:#e8a430">%{customdata[4]}</span> > %{customdata[3]}<extra></extra>')
    if recommended_ids:
        recs = df[df['role'] == 'Recomendado']
        fig.add_trace(go.Scattergl(x=recs['x'], y=recs['y'], mode='markers', marker=dict(size=10, color='red', symbol='diamond', line=dict(width=1, color='white')), name='Recomendados', customdata=recs[['title', 'artist']].values, hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br><span style="color:#ff6b6b;">Recomendado</span><extra></extra>'))
    if seed_id:
        seeds = df[df['role'] == 'Semilla']
        fig.add_trace(go.Scattergl(x=seeds['x'], y=seeds['y'], mode='markers', marker=dict(size=14, color='gold', symbol='star', line=dict(width=1.5, color='white')), name='Semilla', customdata=seeds[['artist', 'cluster', 'title']].values, hovertemplate='<b>%{customdata[2]}</b><br>%{customdata[0]}<br><span style="color:gold;">Semilla</span><extra></extra>'))
    if highlighted_id:
        h = df[df['role'] == 'Buscado']
        fig.add_trace(go.Scattergl(x=h['x'], y=h['y'], mode='markers', marker=dict(size=12, color='white', symbol='circle', line=dict(width=3, color='#4dc9e6')), name='Buscado', customdata=h[['artist', 'cluster', 'title']].values, hovertemplate='<b>%{customdata[2]}</b><br>%{customdata[0]}<br><span style="color:#4dc9e6;">Buscado</span><extra></extra>'))
    
    fig.update_layout(**LAYOUT_SCATTER)
    if not show_legend:
        fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
    return fig_to_html(fig)

def get_filtered_scatter_html(filtered_ids):
    data = get_data()
    if data is None or not filtered_ids: return ""
    coords, clusters, info, album_ids, mega_cl = data['tsne_coords'], data['cluster_labels'], data['album_info'], data['album_ids'], data['mega_clusters']
    mask = np.array([aid in filtered_ids for aid in album_ids])
    if mask.sum() == 0: return ""
    df = pd.DataFrame({'x': coords[mask, 0], 'y': coords[mask, 1], 'galaxy': [mega_cl[i] for i, v in enumerate(mask) if v], 'title': info[mask]['title'].values, 'artist': info[mask]['artist'].values, 'genres': info[mask]['genres'].values, 'cluster': [f"C{c}: {CLUSTER_NAMES.get(int(c), 'Otros')}" if c != -1 else "Otros" for c in clusters[mask]]}).sort_values(by='galaxy')
    fig = px.scatter(df, x='x', y='y', color='galaxy', color_discrete_map=MEGA_CLUSTER_COLORS, custom_data=['title', 'artist', 'genres', 'cluster', 'galaxy'], opacity=0.85, labels={'galaxy': ''})
    fig.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br><span style="color:#e8a430">%{customdata[4]}</span> > %{customdata[3]}<extra></extra>')
    fig.update_layout(**LAYOUT_SCATTER)
    return fig_to_html(fig)

def get_user_collection_map_html(album_counts):
    data = get_data()
    if data is None or not album_counts: return ""
    coords, info, album_ids, clusters, mega_cl = data['tsne_coords'], data['album_info'], data['album_ids'], data['cluster_labels'], data['mega_clusters']
    ids_arr = np.array(album_ids)
    u_ids = set(album_counts.keys())
    mask = np.array([aid in u_ids for aid in ids_arr])
    if mask.sum() == 0: return ""
    matched = ids_arr[mask]
    df = pd.DataFrame({'x': coords[mask, 0], 'y': coords[mask, 1], 'galaxy': [mega_cl[i] for i, v in enumerate(mask) if v], 'title': info[mask]['title'].values, 'artist': info[mask]['artist'].values, 'count': [album_counts.get(int(aid), 1) for aid in matched], 'cluster': [f"C{c}: {CLUSTER_NAMES.get(int(c), 'Otros')}" if c != -1 else "Otros" for c in clusters[mask]]}).sort_values(by='galaxy')
    df['size'] = np.log1p(df['count']) * 8 + 4
    fig = px.scatter(df, x='x', y='y', color='galaxy', color_discrete_map=MEGA_CLUSTER_COLORS, size='size', custom_data=['title', 'artist', 'count', 'cluster', 'galaxy'], render_mode='webgl', opacity=0.9, labels={'galaxy': ''})
    fig.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Canciones: %{customdata[2]}<br><span style="color:#e8a430">%{customdata[4]}</span> > %{customdata[3]}<extra></extra>')
    fig.update_layout(**LAYOUT_SCATTER)
    return fig_to_html(fig)
