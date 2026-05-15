import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from app.services.recommender.engine import get_data, get_map_bounds
from app.services.recommender.constants import MEGA_CLUSTER_COLORS
from app.visualizations.common import LAYOUT_SCATTER, fig_to_html, COLOR_AMBAR, COLOR_CIAN

def get_filtered_game_map_html(candidate_ids):
    """
    Genera un mapa de Plotly para el juego.
    Los candidatos están en color pleno, el resto en gris tenue.
    """
    data = get_data()
    if data is None: return ""
    
    coords = np.array(data['tsne_coords'])
    info, album_ids, mega_cl = data['album_info'], data['album_ids'], data['mega_clusters']
    
    c_set = set(candidate_ids)
    
    df = pd.DataFrame({
        'x': coords[:, 0],
        'y': coords[:, 1],
        'galaxy': mega_cl,
        'is_candidate': [aid in c_set for aid in album_ids]
    })
    
    fig = go.Figure()
    
    # 1. El Fondo (No candidatos)
    bg = df[~df['is_candidate']]
    fig.add_trace(go.Scattergl(
        x=bg['x'], y=bg['y'],
        mode='markers',
        marker=dict(color='rgba(255,255,255,0.02)', size=3),
        hoverinfo='none',
        showlegend=False
    ))
    
    # 2. Los Candidatos (Por Galaxia)
    fg = df[df['is_candidate']]
    for galaxy, color in MEGA_CLUSTER_COLORS.items():
        g_df = fg[fg['galaxy'] == galaxy]
        if g_df.empty: continue
        fig.add_trace(go.Scattergl(
            x=g_df['x'], y=g_df['y'],
            mode='markers',
            name=galaxy,
            marker=dict(color=color, size=7, opacity=0.9, line=dict(width=0.5, color='white')),
            showlegend=False
        ))

    fig.update_layout(**LAYOUT_SCATTER)
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        xaxis=dict(range=[df['x'].min()-1, df['x'].max()+1]),
        yaxis=dict(range=[df['y'].min()-1, df['y'].max()+1])
    )
    
    return fig_to_html(fig)

def get_game_svg_map(candidate_ids=None):
    """
    Genera un SVG puro del UMAP para permitir clicks de coordenadas sin JS.
    """
    data = get_data()
    if data is None: return ""
    
    coords = np.array(data['tsne_coords'])
    mega_cl = data['mega_clusters']
    album_ids = list(data['album_ids'])
    
    c_set = set(candidate_ids) if candidate_ids else set()
    min_x, max_x, min_y, max_y = get_map_bounds()
    range_x = max_x - min_x
    range_y = max_y - min_y
    
    svg_parts = [
        '<svg viewBox="0 0 1000 1000" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet" style="background: #080a12; width: 100%; height: 100%;">'
    ]
    
    for i in range(len(coords)):
        x = ((coords[i, 0] - min_x) / range_x) * 1000
        y = 1000 - (((coords[i, 1] - min_y) / range_y) * 1000)
        
        is_candidate = (candidate_ids is None) or (album_ids[i] in c_set)
        
        if is_candidate:
            color = MEGA_CLUSTER_COLORS.get(mega_cl[i], '#4dc9e6')
            opacity = 0.8
            radius = 2.0
        else:
            color = "rgba(255,255,255,0.05)"
            opacity = 0.2
            radius = 1.0
            
        svg_parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{color}" opacity="{opacity}" />')
    
    svg_parts.append('</svg>')
    return "".join(svg_parts)

def get_game_result_map_html(target_coords, user_coords):
    """
    Muestra el mapa final con una línea conectando el click del usuario con el objetivo real.
    """
    data = get_data()
    if data is None: return ""
    
    coords = np.array(data['tsne_coords'])
    
    fig = go.Figure()
    
    # 1. Fondo tenue
    fig.add_trace(go.Scattergl(
        x=coords[:, 0], y=coords[:, 1],
        mode='markers',
        marker=dict(color='rgba(255,255,255,0.03)', size=3),
        hoverinfo='none',
        showlegend=False
    ))
    
    # 2. Línea de conexión
    fig.add_trace(go.Scatter(
        x=[user_coords[0], target_coords[0]],
        y=[user_coords[1], target_coords[1]],
        mode='lines+markers',
        line=dict(color=COLOR_CIAN, width=2, dash='dash'),
        marker=dict(size=[12, 12], color=[COLOR_CIAN, COLOR_AMBAR], symbol=['circle-open', 'star']),
        name='Trayectoria'
    ))
    
    # 3. Anotaciones
    fig.add_annotation(
        x=user_coords[0], y=user_coords[1], 
        text="📍 TU POSICIÓN", 
        showarrow=True, arrowhead=2, 
        bordercolor=COLOR_CIAN, borderpad=4,
        bgcolor="#080a12", opacity=0.9,
        font=dict(color=COLOR_CIAN, size=10)
    )
    fig.add_annotation(
        x=target_coords[0], y=target_coords[1], 
        text="⭐ OBJETIVO REAL", 
        showarrow=True, arrowhead=2, 
        bordercolor=COLOR_AMBAR, borderpad=4,
        bgcolor="#080a12", opacity=0.9,
        font=dict(color=COLOR_AMBAR, size=10)
    )

    fig.update_layout(**LAYOUT_SCATTER)
    
    margin_x = abs(user_coords[0] - target_coords[0]) * 0.5 + 2
    margin_y = abs(user_coords[1] - target_coords[1]) * 0.5 + 2
    
    center_x = (user_coords[0] + target_coords[0]) / 2
    center_y = (user_coords[1] + target_coords[1]) / 2
    
    fig.update_xaxes(range=[center_x - margin_x, center_x + margin_x])
    fig.update_yaxes(range=[center_y - margin_y, center_y + margin_y])
    
    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
    
    return fig_to_html(fig)
