from app import db
from sqlalchemy.sql import func

# --- Tablas de Asociación (Many-to-Many) ---
album_genres = db.Table('album_genres',
    db.Column('album_id', db.Integer, db.ForeignKey('album.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True),
    db.Column('is_primary', db.Boolean, default=True) 
)

album_descriptors = db.Table('album_descriptors',
    db.Column('album_id', db.Integer, db.ForeignKey('album.id'), primary_key=True),
    db.Column('descriptor_id', db.Integer, db.ForeignKey('descriptor.id'), primary_key=True)
)

# --- Modelo Principal ---
class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    release_date = db.Column(db.Date) # Usamos Date para rigor con 9/21/1993
    
    # Métricas de RYM (Crítica)
    avg_rating = db.Column(db.Float, nullable=False)
    rating_count = db.Column(db.Integer, nullable=False)
    review_count = db.Column(db.Integer, nullable=False)

    # MusicBrainz
    mbid = db.Column(db.String(36), unique=True) # UUID
    label = db.Column(db.String(150))
    
    # Last.fm
    lastfm_listeners = db.Column(db.Integer)
    lastfm_playcount = db.Column(db.Integer)

    # Relaciones Muchos a Muchos (Poder analítico real)
    genres = db.relationship('Genre', secondary=album_genres, backref=db.backref('albums', lazy='dynamic'))
    descriptors = db.relationship('Descriptor', secondary=album_descriptors, backref=db.backref('albums', lazy='dynamic'))

# --- Catálogos ---
class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Descriptor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)