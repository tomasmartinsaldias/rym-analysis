"""
recommender/engine.py
─────────────────────
Responsabilidad única: lógica de recomendación por similitud coseno + RRF.

Expone:
  get_album_list() → list[dict]
  recommend(seed_id, top_n, min_rating) → list[dict]
"""

import os
import joblib
import math
import numpy as np
from .constants import MEGA_CLUSTER_MAP, CLUSTER_NAMES

_data = None

def load_recommender_data():
    """Carga el .pkl pre-computado. Retorna el dict o None si no existe."""
    global _data
    pkl_path = os.path.join('instance', 'recommender_data.pkl')
    if os.path.exists(pkl_path):
        _data = joblib.load(pkl_path)
        
        # Enriquecer con Mega Clusters si no están en el PKL
        if _data:
            labels = _data['cluster_labels']
            if 'mega_clusters' not in _data:
                mega_list = []
                for c in labels:
                    mega_label = MEGA_CLUSTER_MAP.get(int(c), "Otros")
                    mega_list.append(mega_label)
                _data['mega_clusters'] = mega_list
            
            # Asegurar que el DataFrame album_info tenga la columna cluster
            if 'cluster' not in _data['album_info'].columns:
                _data['album_info']['cluster'] = labels
            
            # Precomputar diccionario de IDs para búsquedas O(1) con bucle explícito
            if 'album_id_to_index' not in _data:
                id_dict = {}
                for index, aid in enumerate(_data['album_ids']):
                    id_dict[aid] = index
                _data['album_id_to_index'] = id_dict
            
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



def get_album_list():
    """Retorna lista de {id, title, artist, release_year} para el autocomplete."""
    data = get_data()
    if data is None:
        return []
    info = data['album_info']
    cols = ['id', 'title', 'artist']
    if 'release_year' in info.columns:
        cols.append('release_year')
    return info[cols].to_dict('records')


def recommend(seed_id, top_n=20, min_rating=None):
    """
    Recomienda álbumes basándose en una semilla.

    Args:
        seed_id:    ID del álbum semilla.
        top_n:      Cantidad de recomendaciones a devolver.

    Returns:
        Lista de dicts con info del álbum + score + is_wildcard.
    """
    data = get_data()
    if data is None:
        return []

    similarity_cache = data.get('similarity_cache')
    if similarity_cache is None:
        from sklearn.metrics.pairwise import cosine_similarity
        similarity_cache = cosine_similarity(data['feature_matrix']).astype(np.float16)

    album_ids      = data['album_ids']
    album_info     = data['album_info']
    has_descriptors = data['has_descriptors']
    clusters       = data['cluster_labels']

    id_to_idx = data.get('album_id_to_index', {})

    if seed_id not in id_to_idx:
        return []

    seed_idx    = id_to_idx[seed_id]
    artists     = album_info['artist'].values
    ratings     = album_info['avg_rating'].values
    seed_artist = artists[seed_idx]

    listeners_log_list = []
    for listeners in album_info['lastfm_listeners']:
        if not listeners:
            listeners = 0
        listeners_log_list.append(math.log1p(listeners))
    p_log = np.array(listeners_log_list)
    alpha    = 0.1  # Peso de la diferencia de popularidad
    beta     = 0.4  # Peso de la diferencia de rating
    cluster_s = clusters[seed_idx]
    mega_cls = data['mega_clusters']
    mega_s = mega_cls[seed_idx]
    p_log_s  = p_log[seed_idx]
    rating_s = ratings[seed_idx]

    candidates = []
    for c_idx in range(len(album_ids)):
        if c_idx == seed_idx or not has_descriptors[c_idx]:
            continue
        if artists[c_idx] == seed_artist:
            continue

        cos_sim   = similarity_cache[seed_idx, c_idx]
        cluster_c = clusters[c_idx]
        mega_c    = mega_cls[c_idx]
        
        # Bonos por jerarquía
        bonus = 1.0
        if cluster_s == cluster_c and cluster_s != -1:
            bonus = 1.20 # Bonus fuerte por mismo micro-cluster
        elif mega_s == mega_c and mega_s != "Otros":
            bonus = 1.05 # Bonus ligero por misma galaxia (macro)
        
        delta_log_pop = abs(p_log_s - p_log[c_idx])
        delta_rating  = abs(rating_s - ratings[c_idx])
        
        # Penalizamos usando decaimiento exponencial (más estable y suave)
        pop_penalty    = np.exp(-alpha * delta_log_pop)
        rating_penalty = np.exp(-beta * delta_rating)
        final_score    = cos_sim * bonus * pop_penalty * rating_penalty

        candidates.append((c_idx, final_score, cos_sim, delta_log_pop, delta_rating))

    candidates.sort(key=lambda x: x[1], reverse=True)

    final_results = []
    used_artists  = {seed_artist}

    for c_idx, f_score, cos_sim, delta_log_pop, delta_rating in candidates:
        if len(final_results) >= top_n:
            break
        artist_c = artists[c_idx]
        if artist_c not in used_artists:
            used_artists.add(artist_c)
            final_results.append({
                'c_idx': c_idx, 
                'score': f_score, 
                'cos_sim': cos_sim,
                'cluster': clusters[c_idx],
                'mega': mega_cls[c_idx],
                'is_wildcard': False
            })

    results = []
    for item in final_results:
        idx = item['c_idx']
        row = album_info.iloc[idx]
        results.append({
            'album_id':        int(row['id']),
            'title':           row['title'],
            'artist':          row['artist'],
            'mbid':            row['mbid'],
            'avg_rating':      row['avg_rating'],
            'genres':          row['genres'],
            'lastfm_listeners': row['lastfm_listeners'],
            'score':           round(float(item['score']), 4),
            'cos_sim':         round(float(item['cos_sim']), 4),
            'cluster':         CLUSTER_NAMES.get(int(item['cluster']), 'Otros') if item['cluster'] != -1 else 'Otros',
            'mega_cluster':    item['mega'],
            'is_wildcard':     item['is_wildcard'],
        })

    return results

def get_map_bounds(margin=5):
    """Retorna los límites (min_x, max_x, min_y, max_y) consistentes para todo el juego."""
    data = get_data()
    if data is None: return 0, 100, 0, 100
    
    coords = np.array(data['tsne_coords'])
    # Usar nanmin/nanmax por seguridad
    min_x = float(np.nanmin(coords[:, 0]) - margin)
    max_x = float(np.nanmax(coords[:, 0]) + margin)
    min_y = float(np.nanmin(coords[:, 1]) - margin)
    max_y = float(np.nanmax(coords[:, 1]) + margin)
    
    return min_x, max_x, min_y, max_y
