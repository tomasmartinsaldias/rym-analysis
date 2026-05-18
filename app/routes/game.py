from flask import Blueprint, render_template, request, session, redirect, url_for
from app.models import Album
from app.services.recommender.engine import get_data
from app.services.game_logic import (
    GameSession, generate_question, process_answer, 
    calculate_final_score, get_deezer_preview, get_investigation_metadata
)
from app.visualizations.game_viz import (
    get_filtered_game_map_html, get_game_svg_map, get_game_result_map_html
)
from app.utils import get_cover_url
import base64
import random

# CONFIGURACIÓN DEL JUEGO
LEVEL_START_INVESTIGATION = 3  # Nivel donde empieza el filtrado manual
LEVEL_START_EXPERT_MODE = 6     # Nivel donde el sistema deja de avisar si pierdes la señal
SCORE_TO_NEXT_LEVEL = 800      # Puntos necesarios para subir de nivel (ajustado para filosofía de solo-puntos-en-mapa)
PROB_INTERFERENCE = 0.3         # Probabilidad de fase de interferencia en nivel > 1
COST_SCAN = 25                  # Costo en puntos de cada escaneo manual

game_bp = Blueprint('game', __name__, url_prefix='/game')

@game_bp.route('/')
def index():
    return render_template('game_intro.html', level=session.get('current_level', 1))

@game_bp.route('/start')
def start():
    level = session.get('current_level', 1)
    gs = GameSession(level=level)
    
    # Si ya estamos en nivel de investigación, saltamos la calibración
    if level >= LEVEL_START_INVESTIGATION:
        gs.phase = 'investigation'
        gs.step = 1
    
    if hasattr(gs, 'error'): return gs.error
    session['game_state'] = gs.to_dict()
    return redirect(url_for('game.play'))

@game_bp.route('/next-level')
def next_level():
    state_dict = session.get('game_state')
    if state_dict:
        gs = GameSession.from_dict(state_dict)
        session['current_level'] = gs.level
    
    session.pop('game_state', None)
    return redirect(url_for('game.start'))

@game_bp.route('/reset')
def reset():
    session['current_level'] = 1
    session.pop('game_state', None)
    return redirect(url_for('game.start'))

@game_bp.route('/skip-id')
def skip_id():
    state_dict = session.get('game_state')
    if not state_dict: return redirect(url_for('game.index'))
    gs = GameSession.from_dict(state_dict)
    if gs.phase == 'identification':
        gs.phase = 'triangulation'
        gs.step = 1
        gs.last_feedback = "IDENTIFICACIÓN SALTEADA (0 pts)"
        session['game_state'] = gs.to_dict()
    return redirect(url_for('game.play'))

@game_bp.route('/play')
def play():
    state_dict = session.get('game_state')
    if not state_dict: return redirect(url_for('game.index'))
    gs = GameSession.from_dict(state_dict)
    target = Album.query.get(gs.target_id)
    
    # Get cluster name for the intruder reveal
    data = get_data()
    try:
        idx = list(data['album_ids']).index(gs.target_id)
        c_id = data['cluster_labels'][idx]
        from app.services.recommender.constants import CLUSTER_NAMES
        cluster_name = CLUSTER_NAMES.get(int(c_id), "Niche Sector")
    except:
        cluster_name = "Unknown Sector"

    question = generate_question(gs, target)
    
    map_html = ""
    triangulation_svg = None
    if gs.phase != 'triangulation':
        map_html = get_filtered_game_map_html(gs.get_candidate_ids())
    else:
        svg_content = get_game_svg_map(gs.get_candidate_ids())
        triangulation_svg = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')

    preview_url = get_deezer_preview(target)
    
    investigation_meta = None
    current_filters = {}
    if gs.phase == 'investigation':
        investigation_meta = get_investigation_metadata()
        # Mapear filtros actuales para que el form los recuerde
        for f_type, val, *rest in gs.filters:
            if f_type.endswith('_range'):
                parts = val.split(':')
                if parts[0] == 'range': parts = parts[1:]
                if len(parts) == 2:
                    key_base = f_type.replace('_range', '')
                    current_filters[f'{key_base}_min'] = parts[0]
                    current_filters[f'{key_base}_max'] = parts[1]
            elif f_type in ['genre_list', 'descriptor_list', 'cluster_list']:
                current_filters[f_type] = val.split('|')
            elif f_type in ['genre_logic', 'desc_logic', 'cluster_logic']:
                current_filters[f_type] = val

    return render_template('game_play.html', gs=gs, question=question, map_html=map_html, 
                           triangulation_svg=triangulation_svg, preview_url=preview_url, 
                           cluster_name=cluster_name, investigation_meta=investigation_meta,
                           current_filters=current_filters,
                           COST_SCAN=COST_SCAN, plotly_required=True)

@game_bp.route('/answer', methods=['POST'])
def answer():
    state_dict = session.get('game_state')
    if not state_dict: return redirect(url_for('game.index'))
    gs = GameSession.from_dict(state_dict)
    target = Album.query.get(gs.target_id)
    ans = request.form.get('answer')
    q_type = request.form.get('q_type', '')
    
    if not ans: return redirect(url_for('game.play'))

    is_correct = process_answer(gs, target, ans, q_type)
    
    if gs.phase == 'calibration' and gs.step > 3:
        if gs.level >= LEVEL_START_INVESTIGATION:
            gs.phase = 'investigation'
            gs.step = 1
        else:
            gs.phase = 'reduction'
            gs.step = 1
    elif gs.phase == 'reduction' and (gs.step > 4 or len(gs.get_candidate_ids()) < 20):
        if gs.level > 1 and random.random() < PROB_INTERFERENCE:
            gs.phase = 'interference'
            gs.step = 1
        else:
            gs.phase = 'identification'
            gs.step = 1
    elif gs.phase == 'interference':
        gs.phase = 'identification'
        gs.step = 1
    elif gs.phase == 'identification' and (gs.step > 2 or is_correct or gs.cluster_revealed):
        gs.phase = 'triangulation'
        gs.step = 1
    
    session['game_state'] = gs.to_dict()
    return redirect(url_for('game.play'))

@game_bp.route('/investigate', methods=['POST'])
def investigate():
    from flask import flash
    state_dict = session.get('game_state')
    if not state_dict: return redirect(url_for('game.index'))
    gs = GameSession.from_dict(state_dict)
    
    # Recoger filtros del panel manual
    new_filters = []
    y_min = request.form.get('year_min')
    y_max = request.form.get('year_max')
    if y_min and y_max: new_filters.append(('year_range', f"{y_min}:{y_max}"))
    
    r_min = request.form.get('rating_min')
    r_max = request.form.get('rating_max')
    if r_min and r_max: new_filters.append(('rating_range', f"{r_min}:{r_max}"))
    
    l_min = request.form.get('listeners_min')
    l_max = request.form.get('listeners_max')
    if l_min and l_max: new_filters.append(('listeners_range', f"{l_min}:{l_max}"))
    
    genres = request.form.getlist('genres')
    if genres: new_filters.append(('genre_list', "|".join(genres)))
    
    descs = request.form.getlist('descriptors')
    if descs: new_filters.append(('descriptor_list', "|".join(descs)))
    
    clusters = request.form.getlist('clusters')
    if clusters: new_filters.append(('cluster_list', "|".join(clusters)))

    # Capturar lógicas granulares
    new_filters.append(('genre_logic', request.form.get('genre_logic', 'AND')))
    new_filters.append(('desc_logic', request.form.get('desc_logic', 'AND')))
    new_filters.append(('cluster_logic', request.form.get('cluster_logic', 'OR')))

    # Validar pérdida de señal (si nivel < LEVEL_START_EXPERT_MODE)
    if gs.level < LEVEL_START_EXPERT_MODE:
        if gs.check_signal_loss(new_filters):
            flash("SEÑAL PERDIDA: El filtro aplicado excluiría el objetivo. Operación cancelada.", "investigation_error")
            return redirect(url_for('game.play'))

    # Aplicar filtros permanentemente
    gs.filters = [f for f in gs.filters if f[0] not in ['year_range', 'rating_range', 'listeners_range', 'genre_list', 'descriptor_list', 'cluster_list']]
    
    for ft, fv in new_filters:
        gs.filters.append((ft, fv, True))
    
    gs.score -= COST_SCAN # Costo de escaneo
    gs.round_score -= COST_SCAN
    
    session['game_state'] = gs.to_dict()
    flash(f"FILTRO APLICADO: Candidatos reducidos a {len(gs.get_candidate_ids())}.", "investigation_success")
    return redirect(url_for('game.play'))

@game_bp.route('/finish-investigation')
def finish_investigation():
    state_dict = session.get('game_state')
    if not state_dict: return redirect(url_for('game.index'))
    gs = GameSession.from_dict(state_dict)
    if gs.phase == 'investigation':
        gs.phase = 'identification'
        gs.step = 1
        session['game_state'] = gs.to_dict()
    return redirect(url_for('game.play'))

@game_bp.route('/triangulate', methods=['POST'])
def triangulate():
    state_dict = session.get('game_state')
    if not state_dict: return redirect(url_for('game.index'))
    gs = GameSession.from_dict(state_dict)
    target = Album.query.get(gs.target_id)
    x = request.form.get('coords.x', type=int)
    y = request.form.get('coords.y', type=int)
    
    if x is None: x = request.form.get('coords_x', type=int)
    if y is None: y = request.form.get('coords_y', type=int)
    if x is None: x = request.form.get('x', type=int)
    if y is None: y = request.form.get('y', type=int)

    if x is None or y is None: return redirect(url_for('game.play'))

    final_score, distance, target_coords, user_umap_coords, bonus_info = calculate_final_score(gs, target, x, y)
    gs.score += final_score
    gs.round_score += final_score
    gs.phase = 'result'
    gs.final_distance = distance
    gs.target_coords = target_coords.tolist()
    gs.user_coords = user_umap_coords.tolist()
    gs.bonus_info = bonus_info
    
    gs.level_completed = bool(gs.round_score >= SCORE_TO_NEXT_LEVEL)
    if gs.level_completed:
        gs.level += 1
    
    session['game_state'] = gs.to_dict()
    return redirect(url_for('game.result'))

@game_bp.route('/result')
def result():
    state_dict = session.get('game_state')
    if not state_dict: return redirect(url_for('game.index'))
    gs = GameSession.from_dict(state_dict)
    target = Album.query.get(gs.target_id)
    cover_url = get_cover_url(target)
    result_map_html = get_game_result_map_html(gs.target_coords, gs.user_coords)
    return render_template('game_play.html', gs=gs, target=target, cover_url=cover_url, 
                           result_map_html=result_map_html, plotly_required=True)
