"""
recommender/loader.py
─────────────────────
Responsabilidad única: cargar y cachear el pkl pre-computado.

Expone:
  load_recommender_data() → dict | None
  get_data()              → dict | None
"""

import os
import joblib

from .constants import MEGA_CLUSTER_MAP

_data = None


def load_recommender_data():
    """Carga el .pkl pre-computado. Retorna el dict o None si no existe."""
    global _data
    pkl_path = os.path.join('instance', 'recommender_data.pkl')
    if os.path.exists(pkl_path):
        _data = joblib.load(pkl_path)
        
        # Enriquecer con Mega Clusters si no están en el PKL
        if _data and 'mega_clusters' not in _data:
            labels = _data['cluster_labels']
            _data['mega_clusters'] = [MEGA_CLUSTER_MAP.get(int(c), "Otros") for c in labels]
            
        print(f"[OK] Recommender data loaded: {len(_data['album_ids'])} albums")
        return _data
    else:
        print("[WARN] recommender_data.pkl no encontrado. Ejecuta: python build_recommender.py")
        return None


def get_data():
    """Retorna los datos cargados, o intenta cargarlos si aún no lo fueron."""
    global _data
    if _data is None:
        load_recommender_data()
    return _data
