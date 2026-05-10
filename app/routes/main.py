from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.recommender import (get_album_list, recommend, get_scatter_html,
    get_filtered_scatter_html, get_affinities,
    make_ratings_chart, make_listeners_chart, make_radar_chart)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    from app.models import Album, Genre
    from app import db
    
    recommender_available = current_app.recommender_data is not None
    scatter_html = None
    stats = {}
    q = request.args.get('q', '').strip()
    album_id = request.args.get('album_id', type=int)
    
    found = None
    selected_album = None
    radar_chart_html = None
    
    if recommender_available:
        if q:
            resolved_id = _resolve_album_id(q)
            found = Album.query.get(resolved_id) if resolved_id else None
            
        highlight = album_id if album_id else (found.id if found else None)
        scatter_html = get_scatter_html(highlighted_id=highlight)
        
        data = current_app.recommender_data
        stats = {
            'album_count': len(data['album_ids']),
            'cluster_count': len(set(data['cluster_labels'])) - (1 if -1 in data['cluster_labels'] else 0),
            'avg_rating': data['album_info']['avg_rating'].mean(),
            'genre_count': len(data['genre_names']),
            'avg_listeners': f"{int(data['album_info']['lastfm_listeners'].mean() / 1000)}K",
            'total_ratings': f"{int(data['album_info']['rating_count'].sum() / 1000000):.1f}M" 
        }
    else:
        # Fallback if recommender not built
        if q:
            resolved_id = _resolve_album_id(q)
            found = Album.query.get(resolved_id) if resolved_id else None
        stats = {
            'album_count': Album.query.count(),
            'cluster_count': 0,
            'avg_rating': db.session.query(db.func.avg(Album.avg_rating)).scalar() or 0,
            'genre_count': Genre.query.count()
        }

    if album_id:
        selected_album = Album.query.get(album_id)
        if selected_album and recommender_available:
            radar_chart_html = make_radar_chart(selected_album.id)

    # Charts del dashboard — generados en Python
    ratings_chart_html = make_ratings_chart() if recommender_available else ""
    listeners_chart_html = make_listeners_chart() if recommender_available else ""

    # Top géneros (query a la DB para sacar los 10 con más álbumes)
    top_genres = db.session.query(
        Genre.name, 
        db.func.count(Genre.id).label('count')
    ).join(Album.genres).group_by(Genre.id).order_by(db.desc('count')).limit(10).all()

    return render_template('index.html',
        q=q,
        found=found,
        selected_album=selected_album,
        radar_chart_html=radar_chart_html,
        all_albums=Album.query.with_entities(Album.title, Album.artist, Album.id, Album.release_date).all(),
        scatter_html=scatter_html,
        stats=stats,
        top_albums=Album.query.order_by(Album.avg_rating.desc()).limit(10).all(),
        top_genres=top_genres,
        ratings_chart_html=ratings_chart_html,
        listeners_chart_html=listeners_chart_html,
    )

@main_bp.route('/album/<int:album_id>')
def album_detail(album_id):
    from app.models import Album
    album = Album.query.get_or_404(album_id)
    radar_chart_html = ""
    if current_app.recommender_data is not None:
        radar_chart_html = make_radar_chart(album.id)
    
    return render_template('album_detail.html', 
                           album=album, 
                           radar_chart_html=radar_chart_html,
                           page_title=album.title)


@main_bp.route('/data')
def data():
    from app.models import Album, Genre, Descriptor
    from app import db

    PER_PAGE = 25

    # ── Leer parámetros GET ──────────────────────────────────────────────────
    q            = request.args.get('q', '').strip()
    sel_genres   = request.args.getlist('genre')
    sel_descs    = request.args.getlist('descriptor')
    genre_mode   = request.args.get('genre_mode',  'and')  # 'and' (intersección) | 'or' (unión)
    desc_mode    = request.args.get('desc_mode',   'and')  # 'and' | 'or'
    rating_min   = request.args.get('rating_min',   type=float)
    rating_max   = request.args.get('rating_max',   type=float)
    sel_cluster  = request.args.get('cluster',      type=int)
    sort         = request.args.get('sort',  'rating')
    order        = request.args.get('order', 'desc')
    page         = request.args.get('page',  1, type=int)

    # Validar
    valid_sorts = {'rating', 'rating_count', 'listeners', 'playcount', 'year', 'title'}
    if sort not in valid_sorts:
        sort = 'rating'
    if order not in {'asc', 'desc'}:
        order = 'desc'
    if genre_mode not in {'and', 'or'}:
        genre_mode = 'and'
    if desc_mode not in {'and', 'or'}:
        desc_mode = 'and'

    # ── Construir query SQLAlchemy ───────────────────────────────────────────
    qry = Album.query

    if q:
        qry = qry.filter(
            db.or_(Album.title.ilike(f'%{q}%'),
                   Album.artist.ilike(f'%{q}%'))
        )

    # Filtro de géneros: AND (cada género debe estar) o OR (al menos uno)
    if sel_genres:
        if genre_mode == 'or':
            qry = qry.filter(
                db.or_(*[Album.genres.any(Genre.name == g) for g in sel_genres])
            )
        else:  # 'and'
            for g in sel_genres:
                qry = qry.filter(Album.genres.any(Genre.name == g))

    # Filtro de descriptores: AND o OR
    if sel_descs:
        if desc_mode == 'or':
            qry = qry.filter(
                db.or_(*[Album.descriptors.any(Descriptor.name == d) for d in sel_descs])
            )
        else:  # 'and'
            for d in sel_descs:
                qry = qry.filter(Album.descriptors.any(Descriptor.name == d))

    if rating_min is not None:
        qry = qry.filter(Album.avg_rating >= rating_min)
    if rating_max is not None:
        qry = qry.filter(Album.avg_rating <= rating_max)

    # Filtro de cluster (requiere el pkl)
    if sel_cluster is not None and current_app.recommender_data is not None:
        pkl      = current_app.recommender_data
        ids_pkl  = pkl['album_ids']
        labels   = pkl['cluster_labels']
        ids_in_cluster = {aid for aid, lbl in zip(ids_pkl, labels)
                          if lbl == sel_cluster}
        if ids_in_cluster:
            qry = qry.filter(Album.id.in_(ids_in_cluster))
        else:
            # Cluster sin resultados → filtro imposible
            qry = qry.filter(db.false())

    # ── Ordenamiento ─────────────────────────────────────────────────────────
    sort_col_map = {
        'rating':       Album.avg_rating,
        'rating_count': Album.rating_count,
        'listeners':    Album.lastfm_listeners,
        'playcount':    Album.lastfm_playcount,
        'year':         Album.release_date,
        'title':        Album.title,
    }
    sort_col = sort_col_map[sort]
    if order == 'asc':
        qry = qry.order_by(sort_col.asc().nullslast())
    else:
        qry = qry.order_by(sort_col.desc().nullsfirst())

    # ── Paginación ───────────────────────────────────────────────────────────
    pagination = qry.paginate(page=page, per_page=PER_PAGE, error_out=False)
    albums     = pagination.items

    # ── UMAP filtrado (solo si recommender disponible) ───────────────────────
    scatter_html = None
    if current_app.recommender_data is not None:
        # Obtenemos los IDs del total filtrado (sin paginar, cap 5000 para perf)
        all_filtered_ids = {a.id for a in qry.with_entities(Album.id).limit(5000).all()}
        scatter_html = get_filtered_scatter_html(all_filtered_ids)

    # ── Opciones para los selects / listas de filtros ────────────────────────
    all_genres      = Genre.query.order_by(Genre.name).all()
    all_descriptors = Descriptor.query.filter(Descriptor.name != '...').order_by(Descriptor.name).all()

    all_clusters = []
    if current_app.recommender_data is not None:
        raw_labels   = current_app.recommender_data['cluster_labels']
        all_clusters = sorted({int(c) for c in raw_labels if c != -1})

    # Opciones para el autocompletado de búsqueda (datalist)
    titles_query = db.session.query(Album.title).all()
    artists_query = db.session.query(Album.artist).distinct().all()
    search_suggestions = sorted(list(set([t[0] for t in titles_query if t[0]] + [a[0] for a in artists_query if a[0]])))

    has_filters = bool(q or sel_genres or sel_descs
                       or rating_min is not None or rating_max is not None
                       or sel_cluster is not None)

    return render_template('data.html',
        page_title='Explorador de Álbumes',
        plotly_required=True,
        # Datos
        albums=albums,
        pagination=pagination,
        scatter_html=scatter_html,
        # Opciones de filtros
        all_genres=all_genres,
        all_descriptors=all_descriptors,
        all_clusters=all_clusters,
        search_suggestions=search_suggestions,
        # Valores actuales de filtros
        q=q,
        sel_genres=sel_genres,
        sel_descs=sel_descs,
        genre_mode=genre_mode,
        desc_mode=desc_mode,
        rating_min=rating_min,
        rating_max=rating_max,
        sel_cluster=sel_cluster,
        sort=sort,
        order=order,
        has_filters=has_filters,
    )

@main_bp.route('/analysis')
def analysis():
    return "Aquí se mostrarán los gráficos y análisis."

@main_bp.route('/recommend', methods=['GET', 'POST'])
def recommend_page():
    from app.models import Album
    recommender_available = current_app.recommender_data is not None
    
    if request.method == 'POST' and recommender_available:
        # ── Server-side album resolution (reemplaza el JS) ──
        seed_text = request.form.get('seed_text', '').strip()
        min_rating = request.form.get('min_rating', type=float)
        
        seed_id = _resolve_album_id(seed_text)
        
        if not seed_id:
            flash('No se encontró un álbum que coincida. Probá con otro nombre.', 'error')
            return redirect(url_for('main.recommend_page'))
        
        # Calcular recomendaciones
        results = recommend(
            seed_id, 
            top_n=12, 
            min_rating=min_rating
        )
        
        # Generar scatter con semilla y recomendaciones resaltadas
        rec_ids = [r['album_id'] for r in results]
        scatter_html = get_scatter_html(seed_id=seed_id, recommended_ids=rec_ids)
        
        # Generar affinities de los resultados
        affinities = get_affinities(results)
        
        return render_template('recommend.html',
                             page_title='Recomendaciones — RYM Analysis',
                             recommender_available=True,
                             albums_list=get_album_list(),
                             results=results,
                             scatter_html=scatter_html,
                             affinities=affinities,
                             min_rating=min_rating,
                             seed_text=seed_text)
    
    # GET: formulario vacío
    return render_template('recommend.html',
                         page_title='Recomendador — RYM Analysis',
                         recommender_available=recommender_available,
                         albums_list=get_album_list() if recommender_available else [],
                         results=None)


def _resolve_album_id(text):
    """
    Resuelve un texto de búsqueda a un album ID.
    Acepta formatos:
      - "Title — Artist (Year)"  (formato exacto del datalist)
      - "Title — Artist"
      - "Title" (búsqueda parcial)
    Retorna el ID del álbum o None.
    """
    from app.models import Album
    
    if not text:
        return None
    
    # Intentar parsear formato del datalist: "Title — Artist (Year)"
    if ' — ' in text:
        parts = text.split(' — ', 1)
        title_part = parts[0].strip()
        artist_part = parts[1].strip()
        
        # Quitar año si está entre paréntesis al final
        if artist_part and artist_part[-1] == ')' and '(' in artist_part:
            artist_part = artist_part[:artist_part.rfind('(')].strip()
        
        # Búsqueda exacta por título + artista
        album = Album.query.filter(
            Album.title.ilike(title_part),
            Album.artist.ilike(artist_part)
        ).first()
        if album:
            return album.id
    
    # Fallback: búsqueda parcial por título
    album = Album.query.filter(Album.title.ilike(f'%{text}%')).first()
    if album:
        return album.id
    
    # Último intento: búsqueda parcial por artista
    album = Album.query.filter(Album.artist.ilike(f'%{text}%')).first()
    if album:
        return album.id
    
    return None

