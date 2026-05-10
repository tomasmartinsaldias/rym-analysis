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