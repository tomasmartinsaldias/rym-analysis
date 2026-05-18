import random
import math
import numpy as np
import requests
import urllib.parse
from app.models import Album, Genre, Descriptor
from app.services.recommender.engine import get_data, get_map_bounds
from app.utils import get_cover_url

ATMOSPHERIC_PAIRS = [
    ('Melancholic', 'Uplifting'),
    ('Sparse', 'Dense'),
    ('Mechanical', 'Organic'),
    ('Aggressive', 'Atmospheric')
]

class GameSession:
    def __init__(self, level=1):
        data = get_data()
        if not data:
            self.error = "Recommender data not available."
            return

        self.level = level
        pool_size = min(100 + (level - 1) * 200, 5000)
        popular_df = data['album_info'].sort_values('lastfm_listeners', ascending=False).head(pool_size)
        
        self.target_id = int(random.choice(popular_df['id'].tolist()))
        self.phase = 'calibration' 
        self.step = 1
        self.score = 0
        self.round_score = 0
        self.filters = []
        self.last_feedback = None
        self.cluster_revealed = False
        
    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(d):
        gs = GameSession.__new__(GameSession)
        gs.__dict__.update(d)
        return gs

    def get_candidate_ids(self):
        data = get_data()
        df = data['album_info'].copy()
        df['cluster'] = data['cluster_labels']
        mask_final = df['id'].notnull()
        
        # Extraer modos de lógica granulares
        genre_logic = 'AND'
        desc_logic = 'AND'
        cluster_logic = 'OR' # Por defecto clusters es OR (Galaxias)
        
        for f in self.filters:
            if f[0] == 'genre_logic': genre_logic = f[1]
            if f[0] == 'desc_logic': desc_logic = f[1]
            if f[0] == 'cluster_logic': cluster_logic = f[1]

        for f_type, val, was_correct in self.filters:
            selection = None
            if f_type in ['logic_mode', 'genre_logic', 'desc_logic', 'cluster_logic']: continue
            
            if f_type == 'decade':
                v = int(val)
                selection = (df['release_year'] // 10 * 10) == v
            elif f_type == 'year_range':
                parts = val.split(':')
                if parts[0] == 'range': parts = parts[1:]
                low, high = map(int, parts)
                selection = (df['release_year'] >= low) & (df['release_year'] <= high)
            elif f_type == 'genre':
                selection = df['genres'].astype(str).str.contains(val, case=False, na=False)
            elif f_type == 'genre_list':
                genres = val.split('|')
                if genre_logic == 'AND':
                    selection = df['genres'].apply(lambda x: all(g.lower() in str(x).lower() for g in genres))
                else:
                    selection = df['genres'].apply(lambda x: any(g.lower() in str(x).lower() for g in genres))
            elif f_type == 'listeners_range':
                parts = val.split(':')
                if parts[0] == 'range': parts = parts[1:]
                low, high = map(float, parts)
                selection = (df['lastfm_listeners'].fillna(0) >= low) & (df['lastfm_listeners'].fillna(0) <= high)
            elif f_type == 'rating_range':
                parts = val.split(':')
                if parts[0] == 'range': parts = parts[1:]
                low, high = map(float, parts)
                selection = (df['avg_rating'].fillna(0) >= low) & (df['avg_rating'] <= high)
            elif f_type == 'obsession_range':
                parts = val.split(':')
                if parts[0] == 'range': parts = parts[1:]
                low, high = map(float, parts)
                ratio = df['lastfm_playcount'] / df['lastfm_listeners'].replace(0, 1)
                selection = (ratio >= low) & (ratio <= high)
            elif f_type == 'descriptors':
                selection = df['descriptors'].astype(str).str.contains(val, case=False, na=False)
            elif f_type == 'descriptor_list':
                descs = val.split('|')
                if desc_logic == 'AND':
                    selection = df['descriptors'].apply(lambda x: all(d.lower() in str(x).lower() for d in descs))
                else:
                    selection = df['descriptors'].apply(lambda x: any(d.lower() in str(x).lower() for d in descs))
            elif f_type == 'cluster':
                selection = df['cluster'] == int(val)
            elif f_type == 'cluster_list':
                parts = val.split('|')
                try:
                    # Intentar como IDs numéricos (micro-clusters)
                    clusters_int = [int(c) for c in parts if c.isdigit()]
                    if clusters_int:
                        if cluster_logic == 'AND':
                            selection = df['cluster'].isin(clusters_int)
                        else:
                            selection = df['cluster'].isin(clusters_int)
                    else:
                        # Si no son números, son nombres de Macro Galaxias
                        df['mega_cluster'] = data['mega_clusters']
                        # Galaxias siempre es OR (un album no puede estar en dos sitios)
                        selection = df['mega_cluster'].isin(parts)
                except:
                    df['mega_cluster'] = data['mega_clusters']
                    selection = df['mega_cluster'].isin(parts)
            elif f_type == 'intruder':
                if not was_correct: continue
                target_row = df[df['id'] == self.target_id].iloc[0]
                selection = df['cluster'] == target_row['cluster']
            elif f_type == 'identity':
                if not was_correct: continue
                val_clean = val.strip().lower()
                if val.isdigit():
                    selection = df['id'] == int(val)
                elif " — " in val_clean:
                    try:
                        art_part, tit_part = val_clean.split(" — ", 1)
                        selection = (df['artist'].astype(str).str.lower() == art_part) & \
                                    (df['title'].astype(str).str.lower() == tit_part)
                    except:
                        selection = df['id'] == -1
                else:
                    selection = (df['artist'].astype(str).str.lower() == val_clean) | \
                                (df['title'].astype(str).str.lower() == val_clean)
            else:
                continue

            if was_correct:
                mask_final &= selection
            else:
                mask_final &= ~selection
        
        return df.loc[mask_final, 'id'].tolist()

    def check_signal_loss(self, filters_to_test):
        """Checks if the target album would be lost with the given set of filters."""
        data = get_data()
        df = data['album_info']
        df['cluster'] = data['cluster_labels']
        album_ids = data['album_ids']
        target_row = df[df['id'] == self.target_id].iloc[0]
        target = Album.query.get(self.target_id)
        
        # Extraer modos de lógica granulares
        genre_logic = 'AND'
        desc_logic = 'AND'
        cluster_logic = 'OR'
        for f in self.filters:
            if f[0] == 'genre_logic': genre_logic = f[1]
            if f[0] == 'desc_logic': desc_logic = f[1]
            if f[0] == 'cluster_logic': cluster_logic = f[1]
        
        # También chequear si vienen en los nuevos filtros
        for ft, fv in filters_to_test:
            if ft == 'genre_logic': genre_logic = fv
            if ft == 'desc_logic': desc_logic = fv
            if ft == 'cluster_logic': cluster_logic = fv

        for f_type, val in filters_to_test:
            if f_type in ['logic_mode', 'genre_logic', 'desc_logic', 'cluster_logic']: continue
            match = False
            if f_type == 'year_range':
                try:
                    parts = val.split(':')
                    if parts[0] == 'range': parts = parts[1:]
                    low, high = map(int, parts)
                    match = low <= target_row['release_year'] <= high
                except: match = True
            elif f_type == 'rating_range':
                try:
                    parts = val.split(':')
                    if parts[0] == 'range': parts = parts[1:]
                    low, high = map(float, parts)
                    match = low <= (target_row['avg_rating'] or 0) <= high
                except: match = True
            elif f_type == 'listeners_range':
                try:
                    parts = val.split(':')
                    if parts[0] == 'range': parts = parts[1:]
                    low, high = map(float, parts)
                    match = low <= (target_row['lastfm_listeners'] or 0) <= high
                except: match = True
            elif f_type == 'genre_list':
                genres = val.split('|')
                target_genres = [g.name.lower() for g in target.genres]
                if genre_logic == 'AND':
                    if not all(g.lower() in target_genres for g in genres): return True
                else:
                    if not any(g.lower() in target_genres for g in genres): return True
                match = True
            elif f_type == 'descriptor_list':
                descs = val.split('|')
                target_descs = [d.name.lower() for d in target.descriptors]
                if desc_logic == 'AND':
                    if not all(d.lower() in target_descs for d in descs): return True
                else:
                    if not any(d.lower() in target_descs for d in descs): return True
                match = True
            elif f_type == 'cluster_list':
                parts = val.split('|')
                try:
                    # Caso 1: Micro Clusters numéricos
                    clusters_int = [int(c) for c in parts if c.isdigit()]
                    if clusters_int:
                        match = int(target_row['cluster']) in clusters_int
                    else:
                        # Caso 2: Macro Galaxias por nombre (Siempre OR)
                        idx = album_ids.index(self.target_id)
                        target_mega = str(data['mega_clusters'][idx]).strip().lower()
                        parts_clean = [p.strip().lower() for p in parts]
                        match = target_mega in parts_clean
                except:
                    match = True
            else:
                match = True 
            
            if not match:
                return True # Lost!
        return False # Safe

def generate_question(gs, target):
    data = get_data()
    info = data['album_info']
    c_ids = gs.get_candidate_ids()
    df_c = info[info['id'].isin(c_ids)]

    if gs.phase == 'calibration':
        if gs.step == 1:
            year = target.release_date.year if target.release_date else 1990
            correct_decade = (year // 10) * 10
            all_decades = sorted(list(set((info['release_year'] // 10 * 10).dropna().astype(int).tolist())))
            return {'text': "¿En qué década fue lanzado este álbum?", 'type': 'decade', 
                    'options': [{'val': d, 'label': f"{d}s"} for d in all_decades]}
        elif gs.step == 2:
            correct_genre = target.genres[0].name if target.genres else "Rock"
            all_genres = [g.name for g in Genre.query.limit(100).all()]
            others = random.sample([g for g in all_genres if g != correct_genre], 3)
            opts = [correct_genre] + others
            random.shuffle(opts)
            return {'text': "¿Cuál es el género principal de esta señal?", 'type': 'genre', 
                    'options': [{'val': g, 'label': g} for g in opts]}
        else:
            q = generate_descriptors_question(target)
            if q: return q
            return {'text': "¿Cómo clasificarías la frecuencia dominante?", 'type': 'descriptors', 
                    'options': [{'val': 'Atmospheric', 'label': 'Atmospheric'}, {'val': 'Melodic', 'label': 'Melodic'}]}

    
    elif gs.phase == 'reduction':
        data = get_data()
        all_albums = data['album_info']
        target_row = all_albums[all_albums['id'] == gs.target_id].iloc[0]
        target_cluster = target_row['cluster']

        if gs.step == 1:
            qs = df_c['lastfm_listeners'].quantile([0.25, 0.5, 0.75]).tolist()
            opts = [
                {'val': f'range:0:{qs[0]}', 'label': f"Underground Profundo (<{int(qs[0]):,})"},
                {'val': f'range:{qs[0]}:{qs[1]}', 'label': f"Nicho de Culto ({int(qs[0]):,} - {int(qs[1]):,})"},
                {'val': f'range:{qs[1]}:{qs[2]}', 'label': f"Señal en Ascenso ({int(qs[1]):,} - {int(qs[2]):,})"},
                {'val': f'range:{qs[2]}:1e12', 'label': f"Mainstream / Éxito Global (>{int(qs[2]):,})"}
            ]
            return {'text': "¿Cuál es el alcance de su audiencia (Signal Reach)?", 'type': 'listeners_range', 'options': opts}
        elif gs.step == 2:
            valid_ratings = df_c['avg_rating'].dropna()
            if len(valid_ratings) > 4:
                qs = sorted(valid_ratings.quantile([0.25, 0.5, 0.75]).unique().tolist())
                while len(qs) < 3: 
                    last = qs[-1] if qs else 3.0
                    qs.append(min(5.0, last + 0.1))
            else:
                qs = [3.0, 3.5, 4.0]
            
            opts = [
                {'val': f'range:0:{qs[0]}', 'label': f"Cuestionado / Polarizante (<{qs[0]:.2f}★)"},
                {'val': f'range:{qs[0]}:{qs[1]}', 'label': f"Nivel Regular ({qs[0]:.2f} - {qs[1]:.2f}★)"},
                {'val': f'range:{qs[1]}:{qs[2]}', 'label': f"Muy Recomendado ({qs[1]:.2f} - {qs[2]:.2f}★)"},
                {'val': f'range:{qs[2]}:5.0', 'label': f"Aclamación / Obra Maestra (>{qs[2]:.2f}★)"}
            ]
            return {'text': "¿Cuál es la recepción crítica de la señal (RYM Rating)?", 'type': 'rating_range', 'options': opts}
        elif gs.step == 3:
            df_c = df_c.copy()
            df_c['ratio'] = df_c['lastfm_playcount'] / df_c['lastfm_listeners'].replace(0, 1)
            qs = df_c['ratio'].quantile([0.25, 0.5, 0.75]).tolist()
            opts = [
                {'val': f'range:0:{qs[0]}', 'label': f"Base Casual / Pasajera (<{qs[0]:.1f} escuchas/pers)"},
                {'val': f'range:{qs[0]}:{qs[1]}', 'label': f"Interés Moderado ({qs[0]:.1f} - {qs[1]:.1f})"},
                {'val': f'range:{qs[1]}:{qs[2]}', 'label': f"Fidelidad Alta ({qs[1]:.1f} - {qs[2]:.1f})"},
                {'val': f'range:{qs[2]}:5000', 'label': f"Objeto de Culto Total (>{qs[2]:.1f})"}
            ]
            return {'text': "¿Cuál es su Índice de Fidelidad (Oyentes vs Escuchas)?", 'type': 'obsession_range', 'options': opts}
        elif gs.step == 4:
            same_family = all_albums[all_albums['cluster'] == target_cluster]
            if len(same_family) < 3:
                return generate_descriptors_question(target)
            
            opts_same = same_family[same_family['id'] != gs.target_id].sample(min(3, len(same_family)-1)).to_dict('records')
            if len(opts_same) < 3:
                return generate_descriptors_question(target)

            intruders = all_albums[all_albums['cluster'] != target_cluster]
            opt_intruder = intruders.sample(1).to_dict('records')[0]
            
            options = []
            for alb in opts_same:
                options.append({'val': 'same', 'label': f"{alb['title']} - {alb['artist']}", 'cover': get_cover_url(alb)})
            options.append({'val': 'intruder', 'label': f"{opt_intruder['title']} - {opt_intruder['artist']}", 'cover': get_cover_url(opt_intruder)})
            random.shuffle(options)
            
            return {'text': "ANOMALÍA DETECTADA: Identifica al intruso que no pertenece al cluster estelar.", 'type': 'intruder', 'options': options}

    elif gs.phase == 'interference':
        data = get_data()
        all_albums = data['album_info']
        decoys = all_albums[all_albums['id'] != gs.target_id].sample(3).to_dict('records')
        target_info = all_albums[all_albums['id'] == gs.target_id].iloc[0].to_dict()
        
        options = []
        options.append({'val': 'correct', 'label': 'SEÑAL OBJETIVO', 'cover': get_cover_url(target_info)})
        for d in decoys:
            options.append({'val': 'decoy', 'label': 'RUIDO / INTERFERENCIA', 'cover': get_cover_url(d)})
        random.shuffle(options)
        
        return {
            'text': "¡INTERFERENCIA DETECTADA! El canal está distorsionado. Identifica la señal correcta antes de que se pierda el rastro.",
            'type': 'interference',
            'options': options
        }
    elif gs.phase == 'identification':
        c_ids = gs.get_candidate_ids()
        options_map = {}
        
        for aid in c_ids:
            row = info[info['id'] == aid].iloc[0]
            artist = str(row['artist'])
            album = str(row['title'])
            options_map[f"{artist} — {album}"] = aid
            if artist not in options_map:
                options_map[artist] = aid

        options = [{'val': v, 'label': l} for l, v in options_map.items()]
        options.sort(key=lambda x: info.loc[info['id']==x['val'], 'lastfm_listeners'].iloc[0] or 0, reverse=True)
        options = options[:600]
            
        return {
            'text': "¿Has identificado la señal? Escribe el nombre del álbum:",
            'type': 'identity',
            'options': options
        }
    return None

def get_investigation_metadata():
    """Returns ranges and options for the manual investigation panel."""
    data = get_data()
    info = data['album_info']
    
    # Ranges
    years = info['release_year'].dropna().unique()
    ratings = info['avg_rating'].dropna().unique()
    listeners = info['lastfm_listeners'].dropna().unique()
    
    # Categories
    from app.models import Genre, Descriptor
    all_genres = [g.name for g in Genre.query.order_by(Genre.name).all()]
    from sqlalchemy import func
    all_descriptors = [d.name for d in Descriptor.query
                       .join(Descriptor.albums)
                       .group_by(Descriptor.id)
                       .order_by(func.count(Album.id).desc())
                       .limit(40).all()]
    all_descriptors.sort() # Ordenar alfabéticamente para el usuario, pero solo los top 40
    
    from app.services.recommender.constants import MEGA_CLUSTER_COLORS
    clusters = [{'id': k, 'name': k} for k in MEGA_CLUSTER_COLORS.keys() if k != 'Otros']
    
    return {
        'year': {'min': int(min(years)), 'max': int(max(years))},
        'rating': {'min': float(min(ratings)), 'max': float(max(ratings))},
        'listeners': {'min': int(min(listeners)), 'max': int(max(listeners))},
        'genres': all_genres,
        'descriptors': all_descriptors,
        'clusters': clusters
    }

def generate_descriptors_question(target):
    if not target.descriptors:
        return None
    
    correct_desc = random.choice(target.descriptors).name
    all_desc = Descriptor.query.limit(50).all()
    all_names = [d.name for d in all_desc if d.name.lower() != correct_desc.lower()]
    
    if len(all_names) < 3:
        others = ["Atmospheric", "Melodic", "Raw", "Complex"][:3]
    else:
        others = random.sample(all_names, 3)
        
    opts = [correct_desc] + others
    random.shuffle(opts)
    
    return {
        'text': "¿Cuál de estos descriptores define mejor la atmósfera de este álbum?",
        'type': 'descriptors',
        'options': [{'val': d, 'label': d} for d in opts]
    }

def process_answer(gs, target, ans, q_type):
    is_correct = False
    data = get_data()
    info = data['album_info']
    t_row = info[info['id'] == gs.target_id].iloc[0]

    bonus = 0
    if q_type == 'decade':
        is_correct = bool((t_row['release_year'] // 10 * 10) == int(ans))
    elif q_type == 'genre':
        is_correct = bool(ans in str(t_row['genres']))
    elif q_type == 'listeners_range':
        low, high = map(float, ans.split(':')[1:])
        val = t_row['lastfm_listeners'] or 0
        is_correct = bool(low <= val < high)
    elif q_type == 'rating_range':
        low, high = map(float, ans.split(':')[1:])
        val = t_row['avg_rating'] or 0
        is_correct = bool(low <= val < high)
    elif q_type == 'obsession_range':
        low, high = map(float, ans.split(':')[1:])
        ratio = (t_row['lastfm_playcount'] or 0) / (t_row['lastfm_listeners'] or 1)
        is_correct = bool(low <= ratio < high)
    elif q_type == 'atmospheric':
        is_correct = bool(ans.lower() in [d.name.lower() for d in target.descriptors])
    elif q_type == 'descriptors':
        is_correct = bool(ans.lower() in [d.name.lower() for d in target.descriptors])
    elif q_type == 'intruder':
        is_correct = (ans == 'intruder')
        if is_correct:
            gs.cluster_revealed = True
    elif q_type == 'interference':
        is_correct = (ans == 'correct')
        if not is_correct:
            gs.score -= 100
            gs.last_feedback = "INTERFERENCIA CRÍTICA: Rastro perdido (-100)"
            return
    elif q_type == 'identity':
        target_label = f"{target.artist} — {target.title}".lower()
        ans_clean = ans.strip().lower()
        
        if ans_clean == target_label or ans_clean == target.title.lower():
            is_correct = True
            bonus = 500
            gs.last_feedback = "¡ÁLBUM IDENTIFICADO! (+500)"
        elif ans_clean == target.artist.lower():
            is_correct = True
            bonus = 250
            gs.last_feedback = "ARTISTA IDENTIFICADO (+250)"
        else:
            is_correct = False
            bonus = -100
            gs.last_feedback = "FALLO DE IDENTIFICACIÓN (-100)"
        gs.score += bonus
        gs.round_score += bonus
    
    if q_type != 'identity':
        pts = 0 # Las preguntas ya no dan puntos, solo filtran datos
        gs.last_feedback = "FILTRO APLICADO" if is_correct else "FALLO DE FILTRADO"
        gs.score += pts
        gs.round_score += pts

    gs.filters.append((q_type, ans, is_correct))
    gs.step += 1
    return is_correct

def calculate_final_score(gs, target, click_x, click_y):
    data = get_data()
    all_coords = np.array(data['tsne_coords'])
    album_ids = list(data['album_ids'])
    clusters = data['cluster_labels']
    from app.services.recommender.constants import CLUSTER_NAMES

    idx = album_ids.index(target.id)
    target_coords = all_coords[idx]
    target_cluster = clusters[idx]

    min_x, max_x, min_y, max_y = get_map_bounds()
    
    user_x = min_x + (click_x / 800.0) * (max_x - min_x)
    user_y = max_y - (click_y / 800.0) * (max_y - min_y)
    
    dist = math.sqrt((user_x - target_coords[0])**2 + (user_y - target_coords[1])**2)
    max_dist = (max_x - min_x) / 2.0 # Más generoso (antes era / 4.0)
    base_score = max(0, 1000 * (1 - (dist / max_dist)))
    
    user_p = np.array([[user_x, user_y]])
    from scipy.spatial.distance import cdist
    dists = cdist(user_p, all_coords)
    closest_idx = np.argmin(dists)
    user_cluster = clusters[closest_idx]
    
    bonus = 0
    bonus_text = ""
    if user_cluster == target_cluster and target_cluster != -1:
        bonus = 200
        bonus_text = "¡Bonus de Coherencia! Aterrizaste en el cluster correcto."
    elif user_cluster != -1:
        c_name = CLUSTER_NAMES.get(int(user_cluster), "Niche Sector")
        bonus_text = f"Aterrizaste en el sector de: {c_name}."

    return int(base_score + bonus), round(dist, 2), target_coords, user_p[0], bonus_text

def get_deezer_preview(album):
    try:
        term = f"{album.artist} {album.title}"
        url = f"https://api.deezer.com/search?q={urllib.parse.quote(term)}"
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            data = r.json().get('data', [])
            if data: return data[0].get('preview')
    except: pass
    return None
