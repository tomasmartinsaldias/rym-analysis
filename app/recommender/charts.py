"""
recommender/charts.py
─────────────────────
Responsabilidad única: generar gráficos Plotly auxiliares (no el scatter UMAP).

Expone:
  make_ratings_chart()   → str (HTML)
  make_listeners_chart() → str (HTML)
  make_radar_chart(album_id) → str (HTML)
  get_affinities(results)    → dict[str, str]
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .loader import get_data


def make_ratings_chart():
    data = get_data()
    if data is None:
        return ""
    info = data['album_info']

    fig = px.histogram(info, x='avg_rating', nbins=80,
                       color_discrete_sequence=['#e8a430'])
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=5, b=35, l=45, r=10),
        xaxis_title='', yaxis_title='',
        showlegend=False,
        height=180,
    )
    fig.update_xaxes(
        showgrid=False, zeroline=False,
        range=[0, 5], autorange=False,
        tickmode='linear', tick0=0, dtick=1,
        automargin=True, ticklabelstandoff=10,
        tickfont=dict(size=10, color='rgba(200,200,200,0.7)'),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor='rgba(255,255,255,0.06)',
        zeroline=False, nticks=5, rangemode='tozero',
        automargin=True, ticklabelstandoff=10,
        tickfont=dict(size=10, color='rgba(200,200,200,0.7)'),
    )
    return fig.to_html(
        full_html=False, include_plotlyjs=False,
        config={'displayModeBar': False, 'responsive': True},
    )


def make_listeners_chart():
    data = get_data()
    if data is None:
        return ""
    info = data['album_info'].copy()
    info['listeners_chart'] = info['lastfm_listeners'].fillna(0)

    fig = px.histogram(info, x='listeners_chart', nbins=40,
                       color_discrete_sequence=['#4dc9e6'])
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=10, b=50, l=50, r=10),
        xaxis_title='', yaxis_title='',
        showlegend=False,
        height=180,
    )
    fig.update_xaxes(
        showgrid=False, zeroline=False, nticks=6,
        automargin=True, ticklabelstandoff=10,
        tickfont=dict(size=10, color='rgba(200,200,200,0.7)'),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor='rgba(255,255,255,0.06)',
        zeroline=False, nticks=5,
        automargin=True, range=[0, None], ticklabelstandoff=10,
        tickfont=dict(size=10, color='rgba(200,200,200,0.7)'),
    )
    return fig.to_html(
        full_html=False, include_plotlyjs=False,
        config={'displayModeBar': False, 'responsive': True},
    )


def make_radar_chart(album_id):
    """
    Genera un radar chart Plotly HTML para un álbum dado,
    calculando percentiles contra el dataset completo.
    """
    data = get_data()
    if data is None:
        return ""

    info = data['album_info']
    row  = info[info['id'] == album_id]
    if row.empty:
        return ""

    row = row.iloc[0]

    p_rating    = (info['avg_rating'].fillna(0)        <= (row['avg_rating']        or 0)).mean()
    p_ratings   = (info['rating_count'].fillna(0)      <= (row['rating_count']      or 0)).mean()
    p_listeners = (info['lastfm_listeners'].fillna(0)  <= (row['lastfm_listeners']  or 0)).mean()
    p_plays     = (info['lastfm_playcount'].fillna(0)  <= (row['lastfm_playcount']  or 0)).mean()

    categories = ['RATING', 'RATINGS', 'OYENTES', 'PLAYS', 'RATING']  # loop cerrado
    values     = [p_rating, p_ratings, p_listeners, p_plays, p_rating]

    fig = go.Figure(data=go.Scatterpolar(
        r=values, theta=categories,
        fill='toself',
        fillcolor='rgba(232, 164, 48, 0.15)',
        line=dict(color='#e8a430', width=1.5),
        marker=dict(color='#e8a430', size=6),
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1],
                            showticklabels=False,
                            gridcolor='rgba(255,255,255,0.06)',
                            linecolor='rgba(255,255,255,0.07)'),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.06)',
                             linecolor='rgba(255,255,255,0.07)',
                             tickfont=dict(family="'DM Mono', monospace",
                                          size=10, color='rgba(240,236,224,0.45)')),
            bgcolor='rgba(0,0,0,0)',
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=30, t=30, b=30),
        height=240,
    )

    return fig.to_html(full_html=False, include_plotlyjs=False,
                       config={'displayModeBar': False})


def get_affinities(results):
    """
    Genera gráficos de affinities (géneros + descriptores) para una lista de
    resultados del recomendador. Retorna dict con HTML de cada gráfico.
    """
    data = get_data()
    if data is None or not results:
        return {}

    info      = data['album_info']
    album_ids = data['album_ids']
    id_to_idx = {aid: i for i, aid in enumerate(album_ids)}

    result_rows = [
        info.iloc[id_to_idx[r['album_id']]]
        for r in results
        if r['album_id'] in id_to_idx
    ]

    if not result_rows:
        return {}

    result_html = {}

    # ── Géneros ──────────────────────────────────────────────────────────────
    genre_counts = {}
    for row in result_rows:
        for g in str(row['genres']).split(', '):
            g = g.strip()
            if g:
                genre_counts[g] = genre_counts.get(g, 0) + 1

    if genre_counts:
        genre_df = pd.DataFrame([
            {'Género': g, 'Frecuencia': c}
            for g, c in sorted(genre_counts.items(), key=lambda x: -x[1])[:15]
        ]).sort_values('Frecuencia', ascending=True)

        fig_genres = px.bar(
            genre_df, x='Frecuencia', y='Género', orientation='h',
            title='Géneros predominantes en tus Recomendaciones',
            color='Frecuencia', color_continuous_scale='Viridis',
            height=max(300, len(genre_df) * 30),
        )
        fig_genres.update_layout(template='plotly_dark',
                                 paper_bgcolor='rgba(0,0,0,0)',
                                 plot_bgcolor='rgba(0,0,0,0)',
                                 margin=dict(l=150))
        result_html['genres'] = fig_genres.to_html(full_html=False, include_plotlyjs=False)

    # ── Descriptores ─────────────────────────────────────────────────────────
    desc_counts = {}
    for row in result_rows:
        for d in str(row['descriptors']).split(', '):
            d = d.strip()
            if d:
                desc_counts[d] = desc_counts.get(d, 0) + 1

    if desc_counts:
        desc_df = pd.DataFrame([
            {'Descriptor': d, 'Frecuencia': c}
            for d, c in sorted(desc_counts.items(), key=lambda x: -x[1])[:15]
        ]).sort_values('Frecuencia', ascending=True)

        fig_desc = px.bar(
            desc_df, x='Frecuencia', y='Descriptor', orientation='h',
            title='Descriptores dominantes en tus Recomendaciones',
            color='Frecuencia', color_continuous_scale='Magma',
            height=max(300, len(desc_df) * 30),
        )
        fig_desc.update_layout(template='plotly_dark',
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                margin=dict(l=150))
        result_html['descriptors'] = fig_desc.to_html(full_html=False, include_plotlyjs=False)

    return result_html
