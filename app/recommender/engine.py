"""
recommender/engine.py
─────────────────────
Responsabilidad única: lógica de recomendación por similitud coseno + RRF.

Expone:
  get_album_list() → list[dict]
  recommend(seed_id, top_n, min_rating) → list[dict]
"""

import math
import numpy as np
from .loader import get_data


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
        min_rating: Rating mínimo (float) o None (se calcula dinámicamente).

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

    id_to_idx = {aid: i for i, aid in enumerate(album_ids)}

    if seed_id not in id_to_idx:
        return []

    seed_idx    = id_to_idx[seed_id]
    artists     = album_info['artist'].values
    ratings     = album_info['avg_rating'].values
    seed_artist = artists[seed_idx]

    if min_rating is None:
        seed_rating = ratings[seed_idx] or 0
        min_rating  = max(2.5, (seed_rating or 3.0) - 0.5)

    p_log    = np.array([math.log1p(l or 0) for l in album_info['lastfm_listeners']])
    alpha    = 0.25
    cluster_s = clusters[seed_idx]
    p_log_s  = p_log[seed_idx]

    candidates = []
    for c_idx in range(len(album_ids)):
        if c_idx == seed_idx or not has_descriptors[c_idx]:
            continue
        if artists[c_idx] == seed_artist:
            continue
        if (ratings[c_idx] or 0) < min_rating:
            continue

        cos_sim   = similarity_cache[seed_idx, c_idx]
        cluster_c = clusters[c_idx]
        bonus     = 1.05 if (cluster_s == cluster_c and cluster_s != -1) else 1.0
        delta_log_pop = abs(p_log_s - p_log[c_idx])
        final_score   = cos_sim * bonus * (1.0 - alpha * delta_log_pop)

        candidates.append((c_idx, final_score, cos_sim, delta_log_pop))

    candidates.sort(key=lambda x: x[1], reverse=True)

    final_results = []
    used_artists  = {seed_artist}

    for c_idx, f_score, cos_sim, delta_log_pop in candidates:
        if len(final_results) >= top_n:
            break
        artist_c = artists[c_idx]
        if artist_c not in used_artists:
            used_artists.add(artist_c)
            final_results.append({'c_idx': c_idx, 'score': f_score, 'is_wildcard': False})

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
            'is_wildcard':     item['is_wildcard'],
        })

    return results
