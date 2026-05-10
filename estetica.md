Dirección Estética: "Vinyl in the Void"
El concepto central es un observatorio musical. La landing page es literal y metafóricamente un espacio oscuro donde los álbumes flotan como constelaciones — y el UMAP hace que eso sea completamente natural. No es una base de datos, es un universo sonoro que explorás.

🎨 Paleta & Atmósfera
Fondo: Negro profundo casi azulado (#080a12), no negro puro. Con un ruido de grano sutil (CSS noise texture) para que no se sienta vacío.
Acentos: Dos colores clave:

Ámbar/dorado cálido (#e8a430) — las estrellas del UMAP, ratings, detalles del álbum. Evoca vinilo y calor analógico.
Cian frío (#4dc9e6) — elementos interactivos, hover states, clusters de géneros. Tensión visual con el ámbar.

Texto: Off-white (#f0ece0) con jerarquía clara. Nunca blanco puro.

🔤 Tipografía

Display/títulos: Playfair Display en italic — tiene personalidad editorial, evoca crítica musical clásica, Pitchfork meets Criterion Collection.
UI/cuerpo: DM Mono — monoespaciada pero elegante, da sensación de datos técnicos sin verse como terminal barata.
Números/stats: DM Mono más grande, tratados como elementos visuales.


📐 Layout por Página
/ (Landing / UMAP Explorer)
El UMAP ocupa el 85% del viewport, casi full-screen. La navbar es una barra fina semi-transparente arriba. Un pequeño panel colapsable a la izquierda con filtros de género/cluster. Al hover sobre un punto → tooltip flotante con portada del álbum (si la hay), artista, rating. Al click → navega a /album/<id>. El fondo tiene partículas muy sutiles que dan profundidad.
/album/<id> (Álbum Individual)
Layout asimétrico: portada grande a la izquierda (si no hay imagen, un arte generativo basado en los géneros), y a la derecha la info en capas. Stats (rating, plays, listeners) como números grandes estilo editorial. Los géneros como chips con colores por cluster. Los descriptores como texto corrido pequeño, tipo reseña. Abajo: sección "Álbumes cercanos" (los vecinos en el espacio UMAP).
/data (Tabla)
Tabla estilo terminal-editorial: fondo oscuro, filas con separadores finos, sorting con íconos ámbar. Searchbar minimalista arriba. Paginación discreta. Cada fila tiene el nombre del álbum como link a su página individual.
/analysis (Gráficos)
Diseño de data zine — secciones que se leen como artículos visuales. Cada gráfico tiene un título editorial grande y un párrafo de insight debajo. Los gráficos de Plotly con tema oscuro custom que matchea la paleta.
/recommend (Recomendador)
Interfaz de "búsqueda por similitud". Input grande centrado (estilo buscador) con autocompletado. Al buscar un álbum → aparecen las recomendaciones como cards en grid con una mini-visualización del cluster.

✨ Detalles que lo hacen memorable

El cursor se reemplaza por un pequeño círculo que sigue al mouse en el UMAP
Los clusters tienen nombres "curados" (ej: "Avant-garde frío", "Folk íntimo") mostrados en el hover.
Transiciones entre páginas con fade muy suave
Los números de rating usan una tipografía un poco más grande que el contexto, tratados como display elements
Hover en cards de álbum → una sombra de color basada en el color dominante del cluster

Nombre: "Needle Drop" en vez de "RYM Analysis" — mucho más memorable, evoca el ritual de poner un disco. Cambialo si querés mantener el tuyo, pero considéralo.
Tipografía: Playfair Display italic para el logo y títulos grandes, DM Mono para todo lo demás. La tensión entre lo editorial y lo técnico es intencional.
Color: Ámbar (#e8a430) para el logo, ratings, y elementos principales. Cian (#4dc9e6) para géneros, elementos interactivos y datos secundarios. El fondo tiene un grain CSS sutil que evita que el negro se vea plano.
UMAP: Los puntos son pequeños, con opacidad variable, agrupados orgánicamente. El tooltip aparece flotante con borde ámbar. El punto seleccionado tiene un glow sutil. Sin leyenda de colores — el color codifica el cluster pero no necesita etiqueta.
Stats bar: Números grandes en Playfair, labels en mono uppercase tiny. Trata los datos como display elements, no como texto.

Sección 1 (100vh, snap): UMAP full-viewport con título overlay arriba-izquierda y hint de scroll abajo-centro
Sección 2 (100vh, snap): Stats globales simples (conteos, promedios, top albums, top generos, distribucion de ratings, distribucion de escuchas de lastfm)