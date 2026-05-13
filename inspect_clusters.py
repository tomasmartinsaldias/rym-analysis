import joblib
import os
import pandas as pd
from collections import Counter

def analyze_clusters():
    pkl_path = os.path.join('instance', 'recommender_data.pkl')
    if not os.path.exists(pkl_path):
        print(f"Error: {pkl_path} no encontrado.")
        return

    print(f"Cargando datos desde {pkl_path}...")
    data = joblib.load(pkl_path)
    
    info = data['album_info']
    labels = data['cluster_labels']
    
    # Asegurarnos de que el DataFrame tiene los clusters
    info['cluster'] = labels
    
    # Intentar obtener nombres de clusters de las constantes del proyecto
    try:
        from app.recommender.constants import CLUSTER_NAMES
    except ImportError:
        CLUSTER_NAMES = {}

    clusters = sorted(info['cluster'].unique())
    
    print(f"\nSe encontraron {len(clusters)} clusters.\n")
    print("-" * 70)

    for cluster_id in clusters:
        cluster_df = info[info['cluster'] == cluster_id]
        n_albums = len(cluster_df)
        
        # Contar géneros
        all_genres = []
        for g_str in cluster_df['genres'].dropna():
            genres = [g.strip() for g in str(g_str).split(',')]
            all_genres.extend(genres)
        
        genre_counts = Counter(all_genres).most_common(10)
        
        name = CLUSTER_NAMES.get(int(cluster_id), "Sin Nombre")
        print(f"ID: {cluster_id:2} | Albums: {n_albums}")
        
        # Mostrar top 5 géneros con sus porcentajes
        genre_list = []
        for g, count in genre_counts[:5]:
            pct = (count / n_albums) * 100
            genre_list.append(f"{g} ({pct:.0f}%)")
        
        print(f"  Principales géneros: {', '.join(genre_list)}")
        print("-" * 70)

if __name__ == "__main__":
    analyze_clusters()
