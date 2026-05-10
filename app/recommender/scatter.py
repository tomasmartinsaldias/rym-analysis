"""
recommender/scatter.py
──────────────────────
Responsabilidad única: generar HTML del scatter UMAP (Plotly).

Expone:
  get_scatter_html(seed_id, recommended_ids, highlighted_id) → str
  get_filtered_scatter_html(filtered_ids)                    → str
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .loader import get_data


# ── Configuración de layout compartida ───────────────────────────────────────
_LAYOUT_BASE = dict(
    title=None,
    xaxis_title='', yaxis_title='',
    xaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
               showline=False, ticks=''),
    yaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
               showline=False, ticks=''),
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    showlegend=False,
    autosize=True,
    margin=dict(t=0, b=0, l=0, r=0),
    hoverlabel=dict(
        bgcolor='rgba(8,10,18,0.95)',
        bordercolor='rgba(232,164,48,0.6)',
        font=dict(family='DM Mono, monospace', size=12, color='#f0ece0'),
    ),
)


def get_scatter_html(seed_id=None, recommended_ids=None, highlighted_id=None):
    """
    Genera un scatter 2D coloreado por cluster (Plotly HTML).
    Resalta semilla, recomendaciones y álbum buscado si se proporcionan.
    """
    data = get_data()
    if data is None:
        return "<p>Datos del recomendador no disponibles.</p>"

    coords    = data['tsne_coords']
    clusters  = data['cluster_labels']
    info      = data['album_info']
    album_ids = data['album_ids']

    id_to_idx = {aid: i for i, aid in enumerate(album_ids)}

    scatter_df = pd.DataFrame({
        'x':       coords[:, 0],
        'y':       coords[:, 1],
        'cluster': [f'Cluster {c}' for c in clusters],
        'title':   info['title'],
        'artist':  info['artist'],
        'genres':  info['genres'],
        'role':    'Otros',
    })

    scatter_df['album_id'] = [str(aid) for aid in album_ids]

    # Mapear el ruido (-1) a 'Otros'
    scatter_df['cluster'] = [f'Cluster {c}' if c != -1 else 'Otros' for c in clusters]

    if seed_id and seed_id in id_to_idx:
        scatter_df.loc[id_to_idx[seed_id], 'role'] = '⭐ Semilla'
    if recommended_ids:
        for rid in recommended_ids:
            if rid in id_to_idx and scatter_df.loc[id_to_idx[rid], 'role'] != '⭐ Semilla':
                scatter_df.loc[id_to_idx[rid], 'role'] = '🎯 Recomendado'
    if highlighted_id and highlighted_id in id_to_idx:
        scatter_df.loc[id_to_idx[highlighted_id], 'role'] = '🔍 Buscado'

    # Ordenar para que "Otros" quede al fondo y los clusters encima
    scatter_df = scatter_df.sort_values(by='cluster', ascending=False)

    has_highlights = bool(seed_id or recommended_ids or highlighted_id)
    base_opacity = 0.4 if has_highlights else 0.8

    # Filtrar el DataFrame base para no dibujar dos veces los puntos resaltados
    base_df = scatter_df[scatter_df['role'] == 'Otros'] if has_highlights else scatter_df

    fig = px.scatter(
        base_df, x='x', y='y', color='cluster',
        custom_data=['title', 'artist', 'genres', 'cluster'],
        opacity=base_opacity,
    )
    
    # Actualizar hovertemplate para todos los trazos generados por px.scatter
    fig.update_traces(
        hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br><i>%{customdata[2]}</i><br><br>%{customdata[3]}<extra></extra>'
    )

    if seed_id:
        seeds_df = scatter_df[scatter_df['role'] == '⭐ Semilla']
        if not seeds_df.empty:
            fig.add_trace(go.Scatter(
                x=seeds_df['x'], y=seeds_df['y'],
                mode='markers+text',
                marker=dict(size=20, color='gold', symbol='star',
                            line=dict(width=2, color='black')),
                text=seeds_df['title'], textposition='top center',
                name='⭐ Semilla',
                hovertemplate='<b>%{text}</b><br>%{customdata[0]}<extra>Semilla</extra>',
                customdata=seeds_df[['artist']].values,
            ))

    if recommended_ids:
        recs_df = scatter_df[scatter_df['role'] == '🎯 Recomendado']
        if not recs_df.empty:
            fig.add_trace(go.Scatter(
                x=recs_df['x'], y=recs_df['y'],
                mode='markers',
                marker=dict(size=14, color='red', symbol='diamond',
                            line=dict(width=1.5, color='white')),
                name='🎯 Recomendados',
                hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<extra>Recomendado</extra>',
                customdata=recs_df[['title', 'artist']].values,
            ))

    if highlighted_id:
        h_df = scatter_df[scatter_df['role'] == '🔍 Buscado']
        if not h_df.empty:
            fig.add_trace(go.Scatter(
                x=h_df['x'], y=h_df['y'],
                mode='markers+text',
                marker=dict(size=18, color='#4dc9e6', symbol='circle',
                            line=dict(width=2, color='white')),
                text=h_df['title'], textposition='top center',
                name='🔍 Buscado',
                hovertemplate='<b>%{text}</b><br>%{customdata[0]}<extra>Buscado</extra>',
                customdata=h_df[['artist']].values,
            ))

    fig.update_layout(**_LAYOUT_BASE)
    return fig.to_html(
        full_html=False, include_plotlyjs=False,
        config={'displayModeBar': False, 'responsive': True},
    )


def get_filtered_scatter_html(filtered_ids: set):
    """
    Genera el scatter UMAP mostrando *solo* los álbumes presentes en
    `filtered_ids`. Usa las coordenadas pre-calculadas — no re-entrena UMAP.

    Args:
        filtered_ids: conjunto de album IDs a mostrar.

    Returns:
        HTML string del gráfico Plotly, listo para {{ ... | safe }}.
    """
    data = get_data()
    if data is None:
        return ""

    if not filtered_ids:
        return ""

    coords    = data['tsne_coords']
    clusters  = data['cluster_labels']
    info      = data['album_info']
    album_ids = data['album_ids']

    # Máscara booleana — O(n) sin loops Python
    import numpy as np
    mask = np.array([aid in filtered_ids for aid in album_ids])

    if mask.sum() == 0:
        return ""

    filtered_info = info[mask].reset_index(drop=True)
    filtered_clusters = clusters[mask]

    # Mapear el ruido (-1) a 'Otros'
    filtered_cluster_labels = [f'Cluster {c}' if c != -1 else 'Otros' for c in filtered_clusters]

    scatter_df = pd.DataFrame({
        'x':       coords[mask, 0],
        'y':       coords[mask, 1],
        'cluster': filtered_cluster_labels,
        'title':   filtered_info['title'].values,
        'artist':  filtered_info['artist'].values,
        'genres':  filtered_info['genres'].values,
    })
    
    # Ordenar para que "Otros" quede al fondo
    scatter_df = scatter_df.sort_values(by='cluster', ascending=False)

    fig = px.scatter(
        scatter_df, x='x', y='y', color='cluster',
        custom_data=['title', 'artist', 'genres', 'cluster'],
        opacity=0.85,
    )
    
    fig.update_traces(
        hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br><i>%{customdata[2]}</i><br><br>%{customdata[3]}<extra></extra>'
    )

    layout = dict(_LAYOUT_BASE)
    layout['margin'] = dict(t=4, b=4, l=4, r=4)
    fig.update_layout(**layout)

    return fig.to_html(
        full_html=False, include_plotlyjs=False,
        config={'displayModeBar': False, 'responsive': True},
    )
