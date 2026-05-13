"""
recommender/__init__.py
───────────────────────
Re-exporta la API pública del paquete para que los imports existentes
en main.py y app/__init__.py sigan funcionando sin modificación:

  from app.recommender import get_scatter_html, recommend, ...
"""

from .engine import load_recommender_data, get_data, get_album_list, recommend
from .constants import CLUSTER_NAMES


__all__ = [
    'load_recommender_data',
    'get_data',
    'get_album_list',
    'recommend',
    'CLUSTER_NAMES',
]

