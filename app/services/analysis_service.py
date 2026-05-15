from app.models import Album, Genre, album_genres
from app import db
from sqlalchemy import func
import pandas as pd
from app.services.recommender.engine import get_data
from app.services.recommender.constants import CLUSTER_NAMES

def get_rankings_data():
    """Retorna diccionarios de rankings desde la DB para CSS Bars."""
    data = {}
    genres_count = db.session.query(Genre.name, func.count(Genre.id).label('count'))\
            .join(album_genres, Genre.id == album_genres.c.genre_id)\
            .filter(album_genres.c.is_primary == True)\
            .group_by(Genre.id).order_by(db.desc('count')).limit(15).all()
    data['genres_count'] = [dict(name=r[0], count=r[1]) for r in genres_count]

    genres_rating = db.session.query(Genre.name, func.avg(Album.avg_rating).label('avg'))\
            .join(album_genres, Genre.id == album_genres.c.genre_id)\
            .join(Album, Album.id == album_genres.c.album_id)\
            .group_by(Genre.id).having(func.count(Album.id) >= 20)\
            .order_by(db.desc('avg')).limit(15).all()
    data['genres_rating'] = [dict(name=r[0], avg=round(r[1], 2)) for r in genres_rating]

    labels_count = db.session.query(Album.label, func.count(Album.id).label('count'))\
            .filter(Album.label != None, Album.label != '[no label]', Album.label != '')\
            .group_by(Album.label).order_by(db.desc('count')).limit(15).all()
    data['labels_count'] = [dict(name=r[0], count=r[1]) for r in labels_count]

    labels_rating = db.session.query(Album.label, func.avg(Album.avg_rating).label('avg'), func.count(Album.id).label('count'))\
            .filter(Album.label != None, Album.label != '[no label]', Album.label != '')\
            .group_by(Album.label).having(func.count(Album.id) >= 10)\
            .order_by(db.desc('avg')).limit(15).all()
    data['labels_rating'] = [dict(name=r[0], avg=round(r[1], 2), count=r[2]) for r in labels_rating]

    artists_count = db.session.query(Album.artist, func.count(Album.id).label('count'))\
            .group_by(Album.artist).order_by(db.desc('count')).limit(15).all()
    data['artists_count'] = [dict(name=r[0], count=r[1]) for r in artists_count]

    # Rankings desde el Recomenedador (Clusters)
    rec_data = get_data()
    if rec_data is not None:
        df_rec = rec_data['album_info'].copy()
        df_rec['cluster'] = rec_data['cluster_labels']
        df_rec['mega'] = rec_data['mega_clusters']

        # Micro-clusters (Count)
        c_counts = df_rec['cluster'].value_counts()
        data['clusters_count'] = []
        for cid, count in c_counts.head(15).items():
            if cid == -1: continue
            name = CLUSTER_NAMES.get(int(cid), f"Cluster {cid}")
            data['clusters_count'].append({'name': name, 'count': int(count)})
            
        # Micro-clusters (Rating)
        c_ratings = df_rec.groupby('cluster')['avg_rating'].mean().sort_values(ascending=False)
        data['clusters_rating'] = []
        for cid, avg in c_ratings.head(15).items():
            if cid == -1: continue
            name = CLUSTER_NAMES.get(int(cid), f"Cluster {cid}")
            data['clusters_rating'].append({'name': name, 'avg': round(avg, 2)})

        # Macro-clusters (Count)
        m_counts = df_rec['mega'].value_counts()
        data['mega_count'] = []
        for mname, count in m_counts.items():
            if mname == "Otros": continue
            data['mega_count'].append({'name': mname, 'count': int(count)})
            
        # Macro-clusters (Rating)
        m_ratings = df_rec.groupby('mega')['avg_rating'].mean().sort_values(ascending=False)
        data['mega_rating'] = []
        for mname, avg in m_ratings.items():
            if mname == "Otros": continue
            data['mega_rating'].append({'name': mname, 'avg': round(avg, 2)})

    return data

def get_hall_of_fame_data():
    """Genera rankings especiales para el Hall of Fame."""
    res = db.session.query(Album.id, Album.title, Album.artist, Album.avg_rating, 
                           Album.rating_count, Album.review_count, Album.lastfm_listeners).all()
    df = pd.DataFrame(res, columns=['id', 'title', 'artist', 'rating', 'votes', 'reviews', 'listeners'])
    df = df.dropna(subset=['votes', 'listeners'])
    
    # Filtro de calidad sugerido por el usuario
    df = df[df['listeners'] >= 1000]
    
    data = {}
    
    # 1. RYM Darlings (Favoritos de la Crítica)
    df['daring_ratio'] = df['votes'] / (df['listeners'] + 1)
    darlings = df.sort_values('daring_ratio', ascending=False).head(10)
    data['darlings'] = darlings.to_dict('records')
    
    # 2. Underground Gold (Tesoros Ocultos)
    gold = df[df['rating'] >= 4.0].sort_values('listeners', ascending=True).head(10)
    data['gold'] = gold.to_dict('records')
    
    # 3. Provocadores (Engagement)
    df['provoc_ratio'] = df['reviews'] / (df['votes'] + 1)
    provocadores = df.sort_values('provoc_ratio', ascending=False).head(10)
    data['provocadores'] = provocadores.to_dict('records')
    
    # 4. Los Inevitables (Popular pero "Cuestionable" en RYM)
    inevitable = df[df['rating'] < 3.1].sort_values('listeners', ascending=False).head(10)
    data['inevitable'] = inevitable.to_dict('records')
    
    return data

def get_affinities(results):
    data = get_data()
    if data is None or not results: return {}
    info, album_ids = data['album_info'], data['album_ids']
    id_to_idx = {aid: i for i, aid in enumerate(album_ids)}
    result_rows = [info.iloc[id_to_idx[r['album_id']]] for r in results if r['album_id'] in id_to_idx]
    if not result_rows: return {}
    def _get_top(rows, col):
        counts = {}
        for r in rows:
            for v in str(r[col]).split(', '):
                v = v.strip()
                if v: counts[v] = counts.get(v, 0) + 1
        if not counts: return []
        top = sorted(counts.items(), key=lambda x: -x[1])[:15]
        mx = top[0][1]
        return [{'name': k, 'count': v, 'pct': round((v / mx) * 100)} for k, v in top]
    return {'genres': _get_top(result_rows, 'genres'), 'descriptors': _get_top(result_rows, 'descriptors')}
