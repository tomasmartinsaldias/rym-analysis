import plotly.express as px
import plotly.graph_objects as go

# Colores de la estética "Needle Drop"
COLOR_AMBAR = '#e8a430'
COLOR_CIAN = '#4dc9e6'
COLOR_TEXTO = '#f0ece0'
COLOR_FONDO = '#080a12'

def get_dark_layout():
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

LAYOUT_SCATTER = dict(
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
        font=dict(size=10, family='DM Mono, monospace'),
        itemsizing='constant'
    ),
    autosize=True,
    margin=dict(t=30, b=0, l=0, r=0),
    hoverlabel=dict(
        bgcolor='rgba(8,10,18,0.95)',
        bordercolor='rgba(232,164,48,0.6)',
        font=dict(family='DM Mono, monospace', size=12, color='#f0ece0'),
    ),
)

def fig_to_html(fig):
    """Convierte figura a HTML asegurando responsividad total."""
    return fig.to_html(
        full_html=False, 
        include_plotlyjs=False, 
        config={'responsive': True, 'displayModeBar': False}
    )
