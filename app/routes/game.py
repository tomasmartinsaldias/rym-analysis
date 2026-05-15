from flask import Blueprint, render_template, request, session, redirect, url_for
from app.models import Album
from app.services.recommender.engine import get_data
from app.services.game_logic import (
    GameSession, generate_question, process_answer, 
    calculate_final_score, get_deezer_preview
)
from app.visualizations.game_viz import (
    get_filtered_game_map_html, get_game_svg_map, get_game_result_map_html
)
from app.utils import get_cover_url
import base64
import random

game_bp = Blueprint('game', __name__, url_prefix='/game')

@game_bp.route('/')
def index():
    return render_template('game_intro.html', level=session.get('current_level', 1))

@game_bp.route('/start')
def start():
    level = session.get('current_level', 1)
    gs = GameSession(level=level)
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
    return render_template('game_play.html', gs=gs, question=question, map_html=map_html, 
                           triangulation_svg=triangulation_svg, preview_url=preview_url, 
                           cluster_name=cluster_name, plotly_required=True)

@game_bp.route('/answer', methods=['POST'])
def answer():
    state_dict = session.get('game_state')
    if not state_dict: return redirect(url_for('game.index'))
    gs = GameSession.from_dict(state_dict)
    target = Album.query.get(gs.target_id)
    ans = request.form.get('answer')
    q_type = request.form.get('q_type', '')
    
    if not ans: return redirect(url_for('game.play'))

    process_answer(gs, target, ans, q_type)
    
    if gs.phase == 'calibration' and gs.step > 3:
        gs.phase = 'reduction'
        gs.step = 1
    elif gs.phase == 'reduction' and (gs.step > 4 or len(gs.get_candidate_ids()) < 20):
        if gs.level > 1 and random.random() < 0.4:
            gs.phase = 'interference'
            gs.step = 1
        else:
            gs.phase = 'identification'
            gs.step = 1
    elif gs.phase == 'interference':
        gs.phase = 'identification'
        gs.step = 1
    elif gs.phase == 'identification' and (gs.step > 2 or gs.cluster_revealed):
        gs.phase = 'triangulation'
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
    
    gs.level_completed = bool(gs.round_score >= 1200)
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
