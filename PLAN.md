# Plan de Implementación: RYM Analysis Web App

## Visión General

Aplicación Flask con 3 secciones principales accesibles desde una landing page.
Toda la data se sirve desde SQLite. Los gráficos se generan con Plotly (interactivos).

```
Landing Page
├── /data          → Visualizador de la Base de Datos
├── /analysis      → Análisis Exploratorio
└── /recommend     → Recomendador de Álbumes
```

### Distribución del equipo (3 personas)

| Persona | Sección | Alcance |
|---------|---------|--------|
| **Persona 1 — Frontend / Visualizador** | Sección 0 + Sección 1 | Landing page, tabla con filtros, página del álbum (portada + radar), página del artista, infraestructura de templates (base.html, navbar, CSS) |
| **Persona 2 — Análisis Exploratorio** | Sección 2 | Queries de análisis, gráficos Plotly (géneros, labels, artistas, temporal, RYM vs Last.fm), tabs/layout del dashboard |
| **Persona 3 — Recomendador** | Sección 3 | PCA/clustering sobre descriptores, scatter de clusters, affinities, heatmaps |

---

## Dependencias a agregar

```
# En requirements.txt, sumar:
plotly             # Gráficos interactivos (radar, scatter, heatmap, bar)
scikit-learn       # TruncatedSVD, KMeans, TSNE, cosine_similarity, MinMaxScaler
```

No hace falta Matplotlib si usamos Plotly para todo. Plotly genera HTML embebible directamente en Jinja2 con `fig.to_html(full_html=False)`.

> **Nota:** Se evitan `prince`, `umap-learn` y `hdbscan` por riesgo de incompatibilidad en Windows (requieren compilación C/LLVM). Todo se resuelve con `scikit-learn`. Si se desea agregar UMAP/HDBSCAN como mejora, se documentan como opcionales.

---

## Sección 0: Landing Page (`/`)

### Contenido
- Título: "RYM Analysis"
- Breve descripción del dataset: "Análisis de los 5,000 álbumes mejor puntuados de Rate Your Music, enriquecidos con datos de Last.fm y MusicBrainz."
- 3 botones/cards de navegación:
  - 📊 Visualizador de Datos → `/data`
  - 📈 Análisis Exploratorio → `/analysis`
  - 🎯 Recomendador → `/recommend`

### Complejidad: Baja
Solo HTML + CSS (Bootstrap). Sin lógica de backend.

---

## Sección 1: Visualizador de la Base de Datos (`/data`)

### 1.1 Tabla principal
- Tabla paginada con todos los álbumes.
- **Columnas visibles:** Posición, Título, Artista, Año, Rating, Nº Ratings, Género(s), Label, Oyentes (Last.fm), Reproducciones (Last.fm).
- Cada fila es clickeable → lleva a `/album/<id>`.

**Filtros disponibles:**

| Filtro | Tipo de input | Query |
|--------|--------------|-------|
| Título | Text input | `WHERE title ILIKE '%X%'` |
| Artista | Text input | `WHERE artist ILIKE '%X%'` (ya existe) |
| Género | Dropdown/select (precargado desde tabla `Genre`) | `JOIN album_genres WHERE genre.name = X` |
| Rango de fecha | Dos inputs numéricos (año desde / año hasta) | `WHERE release_date BETWEEN ...` |
| Rating mínimo | Slider o input numérico | `WHERE avg_rating >= X` |

**Nota de UX:** Con tantas columnas, conviene hacer la tabla horizontalmente scrolleable en mobile o permitir ocultar/mostrar columnas.

**Backend:** El endpoint `/api/albums` ya existe con paginación y filtro por artista. Hay que:
- Agregar filtros por título, género, rango de fecha y rating mínimo.
- Incluir géneros, label, lastfm_listeners y lastfm_playcount en la respuesta.
- Crear una vista HTML que consuma este endpoint (o hacer la query directa en la ruta de Jinja2).

### 1.2 Página individual del álbum (`/album/<id>`)

**Contenido:**
- **Portada del disco** (Cover Art Archive, ver sección "Portadas" abajo).
- Info básica: título, artista, fecha, label, posición en RYM.
- Métricas: avg_rating, rating_count, review_count, lastfm_listeners, lastfm_playcount.
- Lista de géneros y descriptores.
- **Radar chart** con las métricas numéricas normalizadas.

**Radar chart — Detalle técnico:**
- 5 ejes: Rating (normalizado 0-1), Popularidad RYM (rating_count normalizado), Reviews (normalizado), Listeners Last.fm (normalizado), Playcount Last.fm (normalizado).
- Normalización: min-max sobre toda la DB. Se puede pre-calcular al inicio de la app o cachearlo.
- Librería: `plotly.graph_objects.Scatterpolar`.
- Se renderiza como HTML inline con `fig.to_html(full_html=False, include_plotlyjs='cdn')`.

### Portadas — Sin enrichment adicional

El Cover Art Archive permite acceder a portadas **directamente por URL** usando el MBID que ya tenemos en la DB:

```
https://coverartarchive.org/release/{mbid}/front-250
```

- `front-250` = thumbnail de 250px (rápido de cargar).
- `front` = resolución completa.
- Si el MBID no tiene portada, devuelve 404.

**Implementación en el template Jinja2:**
```html
{% if album.mbid %}
  <img src="https://coverartarchive.org/release/{{ album.mbid }}/front-250"
       alt="Portada de {{ album.title }}"
       onerror="this.src='/static/img/placeholder.png'"
       class="album-cover">
{% else %}
  <img src="/static/img/placeholder.png" alt="Sin portada" class="album-cover">
{% endif %}
```

- No requiere ningún request desde el backend.
- El navegador del usuario pide la imagen directamente al CDN del Cover Art Archive.
- Si falla (404), el `onerror` de JS muestra un placeholder local.
- **Cero impacto en el enrichment.**

### 1.3 Página del artista (`/artist/<name>`)

Dos variantes posibles, de menor a mayor esfuerzo:

**Variante A: Filtrado de tabla (mínimo esfuerzo)**
- Click en nombre de artista (en tabla o detalle de álbum) → redirige a `/data?artist=Radiohead`.
- Reutiliza la tabla existente de `/data`, filtrando por artista.
- **Cero templates nuevos.** Solo agregar links `<a>` donde aparezca el nombre del artista.

**Variante B: Página dedicada `/artist/<name>` (esfuerzo medio)**

Página propia con información agregada del artista:

| Elemento | Detalle |
|----------|---------|
| Header | Nombre del artista, cantidad de álbumes en el top |
| Álbumes en el top | Lista/tabla de sus álbumes ordenados por posición |
| Géneros más frecuentes | Bar chart con los géneros que más aparecen en sus álbumes |
| Descriptores más frecuentes | Bar chart o word cloud con los descriptores dominantes |
| Métricas agregadas | Rating promedio, total listeners Last.fm, total playcount |
| Radar chart | Promedios normalizados del artista vs promedios globales |

**Query base:** `Album.query.filter(func.lower(Album.artist) == func.lower(name)).all()`

### Complejidad general de la Sección 1: Media-Alta
Tabla con filtros, página de álbum con radar, página de artista con gráficos.

---

## Sección 2: Análisis Exploratorio (`/analysis`)

Página con múltiples sub-secciones o tabs. Cada análisis genera un gráfico Plotly embebido.

### 2.1 Por Géneros

| Análisis | Gráfico | Query |
|----------|---------|-------|
| Top géneros por cantidad de álbumes | Bar chart horizontal | `COUNT(*) GROUP BY genre.name ORDER BY count DESC LIMIT 20` |
| Géneros con mejor rating promedio | Bar chart horizontal | `AVG(album.avg_rating) GROUP BY genre.name HAVING COUNT > N` |
| Géneros más escuchados (Last.fm) | Bar chart horizontal | `SUM(album.lastfm_listeners) GROUP BY genre.name` |

**Nota:** Filtrar géneros con pocos álbumes (< 5-10) para evitar outliers con promedio inflado.

### 2.2 Por Labels

| Análisis | Gráfico | Query |
|----------|---------|-------|
| Labels con más álbumes en el top | Bar chart (top 20) | `COUNT(*) GROUP BY album.label WHERE label IS NOT NULL` |
| Labels con mejor rating promedio | Bar chart (top 20) | `AVG(avg_rating) GROUP BY label HAVING COUNT > 3` |

**Cobertura:** ~4884/5000 álbumes tienen label (97.7%). Suficiente para análisis sólido.

### 2.3 Artistas con más álbumes

| Análisis | Gráfico | Query |
|----------|---------|-------|
| Artistas más presentes en la lista | Bar chart (top 20) | `COUNT(*) GROUP BY artist ORDER BY count DESC` |

### 2.4 Correlaciones temporales

| Análisis | Gráfico | Query |
|----------|---------|-------|
| Rating promedio por año | Line chart | Ya existe en `/api/analysis/trends` |
| Cantidad de álbumes por año | Line/bar chart | `COUNT(*) GROUP BY strftime('%Y', release_date)` |
| Rating promedio por década | Bar chart agrupado | Agrupar años en décadas |

### 2.5 RYM vs Last.fm

| Análisis | Gráfico | Detalle |
|----------|---------|---------|
| Rating RYM vs Listeners Last.fm | Scatter plot | X = `avg_rating`, Y = `lastfm_listeners`. Cada punto = 1 álbum. Color por género principal. |
| Rating RYM vs Playcount Last.fm | Scatter plot | Similar, cambiando Y. |
| Rating count RYM vs Listeners Last.fm | Scatter plot | ¿Más ratings en RYM = más escuchas en Last.fm? |

Esto es el análisis más interesante: **¿la crítica de RYM coincide con la popularidad real?**
Se puede incluir la correlación de Pearson/Spearman como dato numérico junto al gráfico.

### Complejidad: Media-Alta
Muchos gráficos, pero las queries son todas variantes de GROUP BY + JOINs. La parte pesada es el frontend (organizar tantos gráficos de forma limpia).

**Sugerencia de layout:** Usar tabs o un menú lateral dentro de `/analysis` para separar las sub-secciones (Géneros | Labels | Artistas | Temporal | RYM vs Last.fm).

---

## Sección 3: Recomendador de Álbumes (`/recommend`)

Implementación **por capas**: cada capa agrega valor pero si se corta en cualquier punto hay un sistema funcional para presentar.

---

### Capa 0 — Baseline (funciona siempre, ~30 líneas de código)

**Coseno crudo sobre descriptores binarios + KNN por semilla:**
1. Construir matriz binaria álbumes × descriptores desde `album_descriptors`.
   - Filas: ~5000 álbumes.
   - Columnas: ~200-400 descriptores únicos.
   - Valor: 1 si el álbum tiene ese descriptor, 0 si no.
2. El usuario selecciona N semillas.
3. Para **cada semilla**, calcular coseno contra todos los álbumes y obtener sus top-K vecinos.
4. **Fusionar** las listas de vecinos con Reciprocal Rank Fusion (RRF).
5. Devolver los top-20 con mayor score RRF (excluyendo semillas).

```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def recommend_baseline(binary_matrix, seed_indices, top_n=20, k_per_seed=50):
    all_scores = {}  # album_idx -> RRF score
    
    for seed_idx in seed_indices:
        seed_vec = binary_matrix[seed_idx].reshape(1, -1)
        sims = cosine_similarity(seed_vec, binary_matrix)[0]
        # Top-K vecinos de esta semilla (excluyendo semillas)
        ranked = [i for i in sims.argsort()[::-1] if i not in seed_indices][:k_per_seed]
        for rank, album_idx in enumerate(ranked):
            all_scores[album_idx] = all_scores.get(album_idx, 0) + 1 / (rank + 60)
    
    # Ordenar por score RRF descendente
    top = sorted(all_scores, key=all_scores.get, reverse=True)[:top_n]
    return top
```

**¿Por qué KNN por semilla en vez de centroide?**
El centroide de semillas diversas (ej: un álbum ambient + uno punk) cae en un punto intermedio que no representa ninguna vibe real ("problema Kansas"). Con KNN individual, cada semilla busca sus propios vecinos y el RRF los fusiona: álbumes cercanos a MÚLTIPLES semillas suben en el ranking, pero cada semilla aporta recomendaciones relevantes a su propia vibe.

**Costo computacional:** N × 5000 operaciones de coseno (N = semillas, típicamente 3-5). Milisegundos con numpy.

---

### Capa 1 — Feature Engineering mejorado (mejora calidad)

**TruncatedSVD sobre la matriz de descriptores** (equivalente aproximado a MCA, sin `prince`):
- `sklearn.decomposition.TruncatedSVD` con k=50 componentes sobre la matriz binaria.
- Captura estructura latente: "melancholic + atmospheric + cold" → dimensión latente.
- Se reemplaza la matriz binaria por los componentes SVD para el coseno.

**Vector de Ítem (por cada álbum) — 3 bloques normalizados:**

Cada bloque se normaliza a norma unitaria antes de concatenar, y se aplica un peso por bloque para controlar la importancia relativa:

```python
from sklearn.preprocessing import normalize

# Bloque 1: Descriptores (SVD, k=50 dims) — textura sonora
bloque_desc = normalize(svd_components)           # norma unitaria

# Bloque 2: Géneros (one-hot, ~50-80 dims) — identidad estructural
bloque_genre = normalize(genre_onehot)             # norma unitaria

# Bloque 3: Numéricas (4 dims) — popularidad/prestigio
bloque_num = normalize(minmax_scaled_numerics)     # norma unitaria

# Concatenar CON pesos (tuneables)
vector_final = np.hstack([
    0.5 * bloque_desc,    # textura sonora (peso dominante)
    0.3 * bloque_genre,   # identidad de género
    0.2 * bloque_num      # popularidad/rating
])
```

**¿Por qué incluir géneros?** Los descriptores capturan mood/textura ("melancholic", "atmospheric") pero los géneros capturan identidad estructural ("Post-Punk", "Hip Hop"). Un álbum de Hip Hop melancólico y uno de Shoegaze melancólico comparten descriptores pero son musicalmente muy distintos. El género aporta una señal única.

**¿Por qué normalizar por bloque?** Sin normalización, el bloque con más dimensiones (géneros: ~80 dims) aplasta al más chico (numéricas: 4 dims) en el cálculo de coseno. La normalización + pesos da control explícito sobre la importancia de cada señal.

---

### Capa 2 — Visualización 2D + Clustering (wow factor visual)

**Reducción a 2D para scatter interactivo:**
- **Opción segura:** `sklearn.manifold.TSNE` (2 componentes). Más lento (~15-30 seg con 5000 puntos) pero está en sklearn, cero dependencias extra.
- **Opción avanzada (si instala bien):** `umap-learn` para UMAP. Más rápido y preserva mejor la estructura global.

**Clustering:**
- **Opción segura:** `sklearn.cluster.KMeans` (elegir K con método del codo o silhouette). Funciona siempre.
- **Opción avanzada (si instala bien):** `hdbscan.HDBSCAN` para detectar clusters sin prefijar K, con manejo de ruido.

**Visualización:** Scatter 2D coloreado por cluster, con hover mostrando título + artista + géneros. Plotly `px.scatter`.

> ⚠️ **Nota importante:** El scatter 2D es solo para visualización. Las recomendaciones se calculan en el espacio completo (coseno sobre vectores SVD), NO sobre las coordenadas 2D. Esto significa que álbumes cercanos en el scatter no necesariamente son los recomendados, y viceversa. Documentar esto si aparece en la presentación.

---

### Capa 3 — Re-ranking y Filtros de Comportamiento

**Filtrado simple por popularidad (versión práctica):**

```python
median_listeners = df['lastfm_listeners'].median()

if obscurity == 'underground':
    candidates = candidates[candidates.lastfm_listeners < median_listeners]
elif obscurity == 'mainstream':
    candidates = candidates[candidates.lastfm_listeners > median_listeners]
# 'neutral' = sin filtrar
```

| Filtro | UI | Lógica |
|--------|-------|--------|
| **Obscuridad** | Selector: Mainstream / Neutral / Underground | Filtrar candidatos por encima/debajo de la mediana de `lastfm_listeners` |
| **Rating mínimo** | Checkbox: "Solo bien valorados" | `WHERE avg_rating >= 3.5` (o percentil 50) |

**Output final:** Top-20 álbumes recomendados post-filtro.

> Nota: Si se quiere un approach más sofisticado (decaimiento gaussiano sobre delta logarítmico), se puede implementar como mejora futura. El filtro por mediana produce el 80% del efecto con 3 líneas.

---

### Capa 4 — Affinities estilo RYM

Generadas a partir de los álbumes semilla o del dataset completo.

| Feature | Implementación | Gráfico |
|---------|---------------|---------|
| **Heatmap años × géneros** | Matriz: filas = géneros (top 15-20), columnas = décadas. Valor = count o avg_rating. | `plotly.express.imshow` o `go.Heatmap` |
| **Géneros sobre la media** | Media global de apariciones → filtrar los que la superen. | Bar chart + línea de referencia |
| **Descriptores sobre la media** | Ídem pero sobre `album_descriptors`. | Bar chart + línea de referencia |
| **Géneros sobre la media en rating** | `AVG(rating)` por género vs media global. | Bar chart divergente |

---

### 3.5 Interfaz del Recomendador (`/recommend`)

**Flujo UX:**
1. El usuario busca y selecciona N álbumes semilla (usar Select2 con Bootstrap o `<datalist>` para autocomplete — más simple que un fetch custom con debounce).
2. Ajusta filtros opcionales: selector de obscuridad, checkbox de rating.
3. Click en "Recomendar" → backend calcula retrieval + filtros.
4. Se muestra:
   - Lista de álbumes recomendados (con portada Cover Art Archive, título, artista, score de similitud).
   - Scatter 2D con las semillas resaltadas y las recomendaciones marcadas (si Capa 2 está implementada).
   - Affinities generadas a partir de la selección (si Capa 4 está implementada).

### Edge Cases a manejar
- **Álbumes sin descriptores:** Su vector binario es nulo → coseno indefinido. Excluirlos del pool de candidatos.
- **Menos de 20 candidatos post-filtro:** Relajar filtros automáticamente o mostrar los que haya.
- **Seed único:** KNN funciona igual (solo una lista de vecinos, sin fusión).
- **Semillas de vibes distintas:** Resuelto por KNN individual + RRF (cada semilla aporta sus propios vecinos).

### Caching
- **Vectores + SVD + coordenadas 2D + labels de cluster:** Pre-calcular con un script offline (`build_recommender.py`) y guardar con `joblib.dump()` a un archivo `.pkl`.
- **Al iniciar la app:** Cargar con `joblib.load()` en una variable global del módulo Flask.
- **Retrieval:** On-demand por cada request (rápido: coseno sobre vectores pre-computados, ~milisegundos).

### Complejidad por capa

| Capa | Dependencias nuevas | Esfuerzo | Funciona sin las siguientes |
|------|--------------------|-----------|--------------------------|
| 0 - Baseline coseno | `scikit-learn` (ya incluido) | Bajo | ✅ Sí, es el núcleo mínimo |
| 1 - SVD + vector ponderado | `scikit-learn` | Medio | ✅ Mejora calidad |
| 2 - Scatter 2D + clusters | `scikit-learn` (t-SNE + KMeans) | Medio | ✅ Solo visual |
| 3 - Re-ranking | Ninguna | Bajo | ✅ Solo filtrado |
| 4 - Affinities | `plotly` (ya incluido) | Medio | ✅ Solo visualización |

> **Mejoras opcionales** (solo si todo lo anterior funciona e instala bien): reemplazar t-SNE por `umap-learn` y KMeans por `hdbscan`. Documentar como "trabajo futuro" en la presentación si no se implementa.

---

## Arquitectura de Gráficos

### Enfoque elegido: Plotly embebido en Jinja2

```python
# En la ruta de Flask:
import plotly.express as px

@main_bp.route('/analysis')
def analysis():
    # ... hacer queries ...
    fig = px.bar(df_genres, x='count', y='genre', orientation='h', title='Top Géneros')
    chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    return render_template('analysis.html', chart=chart_html)
```

```html
<!-- En el template Jinja2: -->
<div class="chart-container">
    {{ chart | safe }}
</div>
```

**Ventajas:**
- Gráficos interactivos (zoom, hover, pan) sin JavaScript custom.
- `include_plotlyjs='cdn'` carga Plotly.js desde CDN (no hay que instalar nada en el front).
- No necesitás generar imágenes PNG ni guardarlas en disco.

---

## Rutas nuevas necesarias

| Ruta | Método | Blueprint | Descripción |
|------|--------|-----------|-------------|
| `/` | GET | main | Landing page (ya existe, actualizar template) |
| `/data` | GET | main | Tabla con buscador + filtros (ya existe como placeholder) |
| `/album/<int:id>` | GET | main | **NUEVA.** Página individual del álbum con portada + radar |
| `/analysis` | GET | main | Dashboard de análisis exploratorio (ya existe como placeholder) |
| `/recommend` | GET | main | **NUEVA.** Recomendador con scatter de clusters + affinities |
| `/artist/<name>` | GET | main | **OPCIONAL.** Página del artista (solo si se elige Variante B) |
| `/api/albums` | GET | api | Lista paginada (ya existe, agregar filtros y datos de API) |

---

## Archivos a crear/modificar

### Nuevos
- `app/templates/base.html` — Layout base con navbar Bootstrap (hereda todo).
- `app/templates/landing.html` — Landing page.
- `app/templates/data.html` — Tabla con buscador y filtros avanzados.
- `app/templates/album_detail.html` — Detalle del álbum + radar + portada.
- `app/templates/analysis.html` — Dashboard de análisis con tabs.
- `app/templates/recommend.html` — Recomendador + clusters + affinities.
- `app/templates/artist.html` — *(Opcional, solo Variante B)* Página del artista.
- `app/static/img/placeholder.png` — Placeholder para álbumes sin portada.
- `app/analysis.py` (o similar) — Funciones de análisis que devuelven figuras Plotly.

### Modificar
- `app/routes/main.py` — Implementar rutas placeholder + `/album/<id>`, `/recommend`, y opcionalmente `/artist/<name>`.
- `app/routes/api.py` — Agregar filtros (título, género, fecha, rating) en `/api/albums`, incluir datos de API en respuesta.
- `requirements.txt` — Agregar `plotly`, `scikit-learn`. Opcionalmente `umap-learn`, `hdbscan` si se implementan las mejoras avanzadas.
- `app/recommender.py` — **NUEVO.** Pipeline de recomendación (SVD, coseno, filtros).
- `build_recommender.py` — **NUEVO.** Script offline para pre-calcular vectores, SVD, t-SNE/UMAP, clusters. Guarda en `.pkl`.

---

## Orden sugerido de implementación

### Fase 1: Infraestructura (primero)
1. Agregar dependencias (`plotly`, `scikit-learn`).
2. Crear `base.html` con navbar Bootstrap y estructura común.
3. Actualizar landing page con los 3 botones.

### Fase 2: Visualizador — Persona 1 (`/data` + `/album/<id>` + `/artist/<name>`)
4. Implementar tabla paginada con filtros avanzados (título, artista, género, fecha, rating) en `/data`.
5. Incluir columnas de datos de API (label, oyentes, reproducciones) en la tabla.
6. Crear ruta `/album/<id>` con detalle + portada Cover Art Archive.
7. Agregar radar chart a la página del álbum.
8. Implementar página de artista (Variante A como mínimo, Variante B si da el tiempo).

### Fase 3: Análisis Exploratorio — Persona 2 (`/analysis`)
9. Implementar queries de análisis (géneros, labels, artistas, temporal).
10. Generar gráficos Plotly y embeberlos en el template.
11. Implementar scatter RYM vs Last.fm con correlación.

### Fase 4: Recomendador — Persona 3 (`/recommend`)
12. **Capa 0:** Baseline — coseno sobre matriz binaria de descriptores. Verificar que funciona end-to-end.
13. **Capa 1:** SVD + vector ponderado (descriptores + numéricas). Comparar calidad vs baseline.
14. **Capa 2:** Scatter 2D (t-SNE) + clustering (KMeans). Script `build_recommender.py` + cache `.pkl`.
15. **Capa 3:** Re-ranking con filtros de obscuridad y rating.
16. **Capa 4:** Affinities (heatmaps, bar charts divergentes).
17. **UI:** Buscador de semillas (Select2/datalist), selector de filtros, visualización de resultados.

### Fase 5: Polish (todos)
15. Estilos CSS / Bootstrap para todo.
16. Responsive design.
17. Testeo general y preparación de presentación.
