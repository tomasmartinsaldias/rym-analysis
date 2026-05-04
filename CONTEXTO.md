# Contexto del Proyecto: RYM Analysis

## 1. Resumen General
Aplicación web desarrollada en **Flask** para la visualización y análisis de un dataset de ~5,000 álbumes de música scrapeados de **Rate Your Music (RYM)**. Los datos del CSV se enriquecen con metadata de **Last.fm** (listeners, playcount) y **MusicBrainz** (MBID, label) mediante un script offline. Todo se almacena en una base de datos SQLite normalizada.

**Entrega:** 11/06 — **Presentación oral:** 13/06 (15 min, grupos de 3).

## 2. Stack Tecnológico
- **Backend:** Flask 3.1.3 (estructura modular con Blueprints).
- **ORM / Base de Datos:** Flask-SQLAlchemy 3.1.1 + SQLite.
- **Procesamiento de Datos:** Pandas 3.0.2.
- **APIs Externas:** Last.fm (vía pylast 7.0.2) + MusicBrainz (vía musicbrainzngs 0.7.1).
- **Frontend:** Jinja2, HTML5, CSS3 (Bootstrap recomendado por la consigna).
- **Gráficos:** Pendiente — Matplotlib/Seaborn/Plotly (según consigna).
- **Config:** python-dotenv para variables de entorno (.env).

## 3. Estructura del Proyecto
```
/rym-analysis
│── app.py                    # Punto de entrada (create_app + run)
│── config.py                 # Config: SECRET_KEY, DB URI, Last.fm keys
│── enrich_data.py            # Script offline: enriquece DB con Last.fm y MusicBrainz
│── init_db.py                # Inicialización de la base de datos
│── rym_clean1.csv            # Dataset original (~1.1 MB, ~5000 álbumes)
│── requirements.txt          # Dependencias del proyecto
│── .env                      # Variables de entorno (API keys)
│
│── /app
│   │── __init__.py           # Factory: create_app(), init SQLAlchemy, registra blueprints
│   │── models.py             # Modelos: Album, Genre, Descriptor + tablas M2M
│   │── utils.py              # process_csv_to_db(): ETL con lógica merge (get or create)
│   │── /routes
│   │   │── main.py           # Blueprint 'main': /, /data, /analysis, /upload (POST)
│   │   └── api.py            # Blueprint 'api' (/api): /status, /albums, /analysis/basic, /analysis/trends
│   │── /templates            # Templates Jinja2 (dentro de app/)
│   └── /static               # Archivos estáticos (CSS, JS, imágenes)
│
│── /templates                 # Templates adicionales (index.html actualmente aquí)
│── /instance
│   └── database.db           # Base de datos SQLite (~835 KB, ya contiene datos)
```

## 4. Modelo de Datos (Esquema Relacional)
Estructura normalizada para soportar análisis multidimensional:

- **Album:** Entidad principal.
  - *Datos RYM (del CSV):* `position`, `title`, `artist`, `release_date`, `avg_rating`, `rating_count`, `review_count`.
  - *Datos MusicBrainz:* `mbid` (UUID), `label`.
  - *Datos Last.fm:* `lastfm_listeners`, `lastfm_playcount`.
- **Genre:** Catálogo de géneros únicos (normalizado).
- **Descriptor:** Catálogo de etiquetas descriptivas (ej: "melancholic", "atmospheric").
- **Tablas de Asociación (M2M):**
  - `album_genres`: Relación Many-to-Many con flag `is_primary`.
  - `album_descriptors`: Relación Many-to-Many.

## 5. Flujo de Datos

```
                                    ┌─────────────────────┐
  rym_clean1.csv ──────────────────►│                     │
  (formulario HTML o directo)       │   SQLite database   │──► Flask App ──► Tablas, Gráficos, Análisis
                                    │   (source of truth) │
  Last.fm + MusicBrainz APIs ──────►│                     │
  (enrich_data.py, offline)         └─────────────────────┘
```

1. **Enriquecimiento (offline):** `enrich_data.py` lee el CSV para obtener la lista de álbumes, consulta MusicBrainz (MBID, label) y Last.fm (listeners, playcount), y guarda todo en SQLite. Incluye retry logic (3 intentos) y respeta rate limits (1 req/seg para MB). Guarda progreso cada 20 álbumes.
2. **Carga del CSV (BONUS):** Formulario HTML en `/upload` → `process_csv_to_db()` hace merge inteligente: si el álbum ya existe en DB (por título+artista), actualiza los campos RYM; si no, lo crea. También procesa géneros y descriptores con lógica "get or create".
3. **Consulta y visualización:** La app Flask lee todo desde SQLite para servir endpoints API y vistas HTML.

## 6. Endpoints Implementados

### Blueprint `main` (rutas de usuario)
| Ruta | Método | Estado | Descripción |
|------|--------|--------|-------------|
| `/` | GET | ✅ Funcional | Página principal (index.html) |
| `/data` | GET | 🔲 Placeholder | Tabla de datos |
| `/analysis` | GET | 🔲 Placeholder | Gráficos y análisis |
| `/upload` | POST | ✅ Funcional | Subida de CSV y merge con DB |

### Blueprint `api` (prefijo `/api`)
| Ruta | Método | Estado | Descripción |
|------|--------|--------|-------------|
| `/api/status` | GET | ✅ Funcional | Health check |
| `/api/albums` | GET | ✅ Funcional | Lista paginada con filtro por artista |
| `/api/analysis/basic` | GET | ✅ Funcional | Promedios, máximos, top álbum |
| `/api/analysis/trends` | GET | ✅ Funcional | Rating promedio por año |

## 7. Estado Actual
- ✅ Modelos definidos con relaciones M2M (Album, Genre, Descriptor).
- ✅ Lógica ETL con merge implementada en `utils.py`.
- ✅ Script de enriquecimiento con Last.fm + MusicBrainz (casi terminado de ejecutar).
- ✅ Endpoints API de análisis básico y tendencias.
- ✅ Formulario de carga de CSV funcional.
- ✅ Base de datos SQLite con datos (~835 KB).
- 🔲 Frontend: solo `index.html` básico. Falta diseño con Bootstrap, tablas interactivas, gráficos.
- 🔲 Gráficos: no implementados aún (Matplotlib/Plotly pendiente).
- 🔲 Análisis avanzado: MCA sobre descriptores y predicciones pendientes.
- 🔲 Templates de `/data` y `/analysis` sin implementar.