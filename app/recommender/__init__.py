"""
recommender/__init__.py
───────────────────────
Re-exporta la API pública del paquete para que los imports existentes
en main.py y app/__init__.py sigan funcionando sin modificación:

  from app.recommender import get_scatter_html, recommend, ...
"""

from .loader  import load_recommender_data, get_data          # noqa: F401
from .engine  import get_album_list, recommend                # noqa: F401
from .scatter import get_scatter_html, get_filtered_scatter_html  # noqa: F401
from .charts  import (                                        # noqa: F401
    make_ratings_chart,
    make_listeners_chart,
    make_radar_chart,
    get_affinities,
)
from .constants import CLUSTER_NAMES

__all__ = [
    'load_recommender_data',
    'get_data',
    'get_album_list',
    'recommend',
    'get_scatter_html',
    'get_filtered_scatter_html',
    'make_ratings_chart',
    'make_listeners_chart',
    'make_radar_chart',
    'get_affinities',
    'CLUSTER_NAMES',
]
