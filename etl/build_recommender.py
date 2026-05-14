"""
build_recommender.py — Script offline de pre-cómputo para el recomendador.

Ejecutar UNA VEZ antes de levantar la app:
    python build_recommender.py

Genera: instance/recommender_data.pkl
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
import joblib
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import MinMaxScaler, normalize
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import KNeighborsClassifier
import umap
import hdbscan

from app import create_app, db
from app.models import Album, Genre, Descriptor, album_genres, album_descriptors


def build():
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("  BUILD RECOMMENDER — Pre-cómputo de vectores")
        print("=" * 60)

        # -------------------------------------------------------
        # 1. Cargar datos de la DB
        # -------------------------------------------------------
        albums = Album.query.order_by(Album.id).all()
        all_descriptors = Descriptor.query.order_by(Descriptor.id).all()
        all_genres = Genre.query.order_by(Genre.id).all()

        print(f"\nÁlbumes: {len(albums)}")
        print(f"Descriptores: {len(all_descriptors)}")
        print(f"Géneros: {len(all_genres)}")

        # Mapeos de ID a índice
        album_id_to_idx = {a.id: i for i, a in enumerate(albums)}
        desc_id_to_idx = {d.id: i for i, d in enumerate(all_descriptors)}
        genre_id_to_idx = {g.id: i for i, g in enumerate(all_genres)}

        n_albums = len(albums)
        n_desc = len(all_descriptors)
        n_genres = len(all_genres)

        # -------------------------------------------------------
        # 2. Construir matriz binaria de descriptores (TF-IDF)
        # -------------------------------------------------------
        print("\n[1/7] Construyendo matriz de descriptores (TF-IDF)...")
        desc_matrix = np.zeros((n_albums, n_desc), dtype=np.float32)

        # Query directa a la tabla de asociación
        links = db.session.query(album_descriptors).all()
        for album_id, descriptor_id in links:
            if album_id in album_id_to_idx and descriptor_id in desc_id_to_idx:
                desc_matrix[album_id_to_idx[album_id], desc_id_to_idx[descriptor_id]] = 1.0

        # Transformación TF-IDF
        tfidf = TfidfTransformer()
        desc_matrix = tfidf.fit_transform(desc_matrix).toarray()

        # Filtrar álbumes sin descriptores
        has_descriptors = desc_matrix.sum(axis=1) > 0
        print(f"  Álbumes con descriptores: {has_descriptors.sum()}/{n_albums}")

        # -------------------------------------------------------
        # 3. One-hot de géneros (1.0 Primario, 0.5 Secundario)
        # -------------------------------------------------------
        print("[2/7] Construyendo ponderación de géneros...")
        genre_matrix = np.zeros((n_albums, n_genres), dtype=np.float32)

        genre_links = db.session.query(album_genres).all()
        for album_id, genre_id, is_primary in genre_links:
            if album_id in album_id_to_idx and genre_id in genre_id_to_idx:
                peso = 1.0 if is_primary else 0.5
                genre_matrix[album_id_to_idx[album_id], genre_id_to_idx[genre_id]] = peso

        # -------------------------------------------------------
        # 4. Escalado de bloques (Inercia de Frobenius)
        # -------------------------------------------------------
        print("[3/7] Normalizando bloques por inercia de Frobenius...")
        norm_g = np.linalg.norm(genre_matrix, 'fro')
        norm_d = np.linalg.norm(desc_matrix, 'fro')

        if norm_g > 0:
            genre_matrix = genre_matrix / norm_g
        if norm_d > 0:
            desc_matrix = desc_matrix / norm_d

        feature_matrix_base = np.hstack([genre_matrix, desc_matrix])

        # -------------------------------------------------------
        # 5. LSA Dinámico (TruncatedSVD al 80% varianza)
        # -------------------------------------------------------
        print("[4/7] LSA Dinámico (Buscando 80% de varianza explicada)...")
        target_variance = 0.80
        step = 20
        max_components = min(400, feature_matrix_base.shape[1] - 1)
        k = step

        best_svd = None
        while k <= max_components:
            svd = TruncatedSVD(n_components=k, random_state=42)
            svd.fit(feature_matrix_base)
            var_exp = svd.explained_variance_ratio_.sum()
            print(f"  Probando k={k} -> Varianza: {var_exp:.2%}")
            best_svd = svd
            if var_exp >= target_variance:
                break
            k += step

        feature_matrix = best_svd.transform(feature_matrix_base)
        feature_matrix = normalize(feature_matrix, norm='l2')
        print(f"  Dimensiones finales de la matriz latente: {feature_matrix.shape}")

        # -------------------------------------------------------
        # 6. Caché de Afinidades (Float16)
        # -------------------------------------------------------
        print("[5/7] Pre-calculando caché de similitud del coseno (float16)...")
        similarity_cache = cosine_similarity(feature_matrix).astype(np.float16)

        # -------------------------------------------------------
        # 7. UMAP (20D -> HDBSCAN) + UMAP (2D -> Visual) (Capa 2)
        # -------------------------------------------------------
        print("[6/7] Calculando UMAP y HDBSCAN...")
        print("  UMAP (20D) para clustering sin perder información...")

        reducer_20d = umap.UMAP(
            n_components=20,
            metric='cosine',
            random_state=42,
            n_neighbors=15,
            min_dist=0.0
        )
        umap_20d_coords = reducer_20d.fit_transform(feature_matrix)

        print("  Clusterizando con HDBSCAN en 20 dimensiones...")
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=40,
            min_samples=5,


            cluster_selection_method='leaf',
            metric='euclidean'
        )
        cluster_labels = clusterer.fit_predict(umap_20d_coords)
        
        # --- Asignar ruido (-1) al cluster más cercano ---
        noise_mask = (cluster_labels == -1)
        if noise_mask.any():
            print("  Asignando ruido (-1) al cluster más cercano usando KNN...")
            knn = KNeighborsClassifier(n_neighbors=5)
            # Entrenar solo con los puntos que sí tienen cluster
            knn.fit(umap_20d_coords[~noise_mask], cluster_labels[~noise_mask])
            # Predecir para el ruido
            cluster_labels[noise_mask] = knn.predict(umap_20d_coords[noise_mask])
            
        n_clusters_found = len(set(cluster_labels))
        n_noise = list(cluster_labels).count(-1)
        print(f"  Clusters finales: {n_clusters_found} (Ruido: {n_noise} álbumes)")

        print("  UMAP (2D) exclusivo para visualización en pantalla...")
        reducer_2d = umap.UMAP(
            n_components=2,
            metric='cosine',
            random_state=42,
            n_neighbors=15,
            min_dist=0.1
        )
        tsne_coords = reducer_2d.fit_transform(feature_matrix)

        # -------------------------------------------------------
        # 8. Info de álbumes para el frontend (con géneros distinguidos)
        # -------------------------------------------------------
        print("[7/7] Preparando info de álbumes y formateando géneros...")
        
        # Optimizamos: traemos todos los links de géneros de una vez
        all_genre_links = db.session.query(album_genres.c.album_id, Genre.name, album_genres.c.is_primary)\
            .join(Genre, Genre.id == album_genres.c.genre_id).all()
            
        from collections import defaultdict
        album_to_genres = defaultdict(lambda: {'p': [], 's': []})
        seen_per_album = defaultdict(set)  # Evita duplicados si la DB tiene filas repetidas
        for aid, gname, is_p in all_genre_links:
            if gname not in seen_per_album[aid]:
                seen_per_album[aid].add(gname)
                album_to_genres[aid]['p' if is_p else 's'].append(gname)

        rows = []
        for a in albums:
            g_data = album_to_genres[a.id]
            rows.append({
                'id': a.id,
                'title': a.title,
                'artist': a.artist,
                'mbid': a.mbid,
                'avg_rating': a.avg_rating,
                'rating_count': a.rating_count,
                'lastfm_listeners': a.lastfm_listeners,
                'lastfm_playcount': a.lastfm_playcount,
                'release_year': a.release_date.year if a.release_date else '',
                'genres': ', '.join(g_data['p']),           # Solo primarios
                'genres_secondary': ', '.join(g_data['s']), # Solo secundarios
                'descriptors': ', '.join([d.name for d in a.descriptors]) if a.descriptors else '',
                'has_descriptors': bool(a.descriptors),
            })
            
        album_info = pd.DataFrame(rows)

        # -------------------------------------------------------
        # 9. Guardar todo
        # -------------------------------------------------------
        print("[7/7] Guardando archivos y metadatos...")
        data = {
            'feature_matrix': feature_matrix,
            'similarity_cache': similarity_cache,
            'album_ids': [a.id for a in albums],
            'tsne_coords': tsne_coords,
            'cluster_labels': cluster_labels,
            'album_info': album_info,
            'has_descriptors': has_descriptors,
            'descriptor_names': [d.name for d in all_descriptors],
            'genre_names': [g.name for g in all_genres],
        }

        output_path = 'instance/recommender_data.pkl'
        joblib.dump(data, output_path)
        print(f"\n[OK] Guardado en {output_path}")
        import os
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"   Tamano: {size_mb:.1f} MB")
        print("=" * 60)


if __name__ == '__main__':
    build()
