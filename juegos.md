Juego: Geoguessr Musical
Suena una canción. Te pregunta por sus diferentes características (quizas dandote opciones). El objetivo es dar el resultado correcto o dar un intervalo para poder eliminar los albumes que no cumplen el filtro. Al final de las preguntads deberá ubicar al album en el mapa. Quizas puede arrancar con una ronda de calentamiento, solo con un par de preguntas sin tener que ubicarlo. La dificultad va aumentando, con cada vez menos oyentes.

La Estructura de la Partida

El juego podría dividirse en etapas progresivas, simulando cómo un telescopio (u observatorio) enfoca un objeto en el espacio:

1. Fase de Calibración (El Calentamiento)

    Mecánica: Suena la preview de la canción (efectivamente, la API de Deezer te da un .mp3 de 30 segundos gratis buscando por artista y track).

    Acción: Se hacen 2 o 3 preguntas de opción múltiple rápidas sobre la canción (¿Década? ¿Género principal?).

    Visualización: El mapa principal no interactúa todavía, sirve para que el usuario "entre en calor" auditivamente.

2. Fase de Reducción (El Core del Juego)

    Mecánica: Suena una canción del álbum objetivo. Se presentan preguntas estratégicas diseñadas para dividir el dataset.

    Acción: En lugar de buscar la respuesta exacta, el usuario usa rangos o categorías. Por ejemplo: "¿Este álbum tiene más o menos de 500,000 oyentes en Last.fm?" o "¿El rating en RYM es mayor a 3.8?".

    Visualización: Con cada respuesta, los puntos del UMAP que no cumplen la condición reducen su opacidad (se vuelven grises y casi transparentes), dejando "encendidos" solo los álbumes candidatos.

3. Fase de Triangulación (La Ubicación)

    Mecánica: Una vez que el mapa se filtró (quedan, digamos, 50-100 álbumes iluminados), el usuario debe hacer clic en la zona donde cree que está el álbum correcto.

    Puntuación: Recibe puntos por la cantidad de filtros correctos y un bonus inversamente proporcional a la distancia euclidiana entre su clic y el punto real.

¿Cómo integrar el "Intruso" y la "Ruta de Navegación"?

Para que el juego no se vuelva monótono, estas mecánicas pueden ser "Tipos de Filtro" especiales o Rondas de Jefe (Boss rounds).

    El Filtro del Intruso (Validación de HDBSCAN):
    En medio de la Fase de Reducción, el juego te dice: "Cual de los siguientes 4 albumes no pertenecen al cluster del album objetivo?" Si respoden bien, se revela que cluster es.

    La Ronda de Navegación (Transición): Esto sería un bonus. Supongamos que el usuario adivinó el Álbum A y el Álbum B. En lugar de simplemente pasar de nivel, el juego te reta: "Para desbloquear el siguiente nivel, encuentra un camino desde de el Álbum A hasta el Álbum B usando. Menor la cantidad d saltos, mayores los ountos. Te da opciones 3 opciones: Un vecino muy cercano al álbum actual. (No avanza hacia el destino, pero es auditivamente idéntico). Un álbum que se aleja un poco del origen pero acorta la distancia hacia el destino. El Salto Puente: Un álbum que representa la transición perfecta entre el punto actual y el destino. Se utiliza interpolación vectorial y la fórmula de un punto intermedio M.

La Curva de Dificultad (El Diseño Socrático)

La dificultad no solo debe ser "álbumes menos conocidos", sino que además puede ser restricción espacial.

    Nivel Principiante (Espacio Global): El mapa muestra los 5000 álbumes. Las diferencias son obvias (Jazz vs. Metal). Los filtros eliminan grandes porciones del mapa.

    Nivel Avanzado (Zoom Local): El juego restringe la vista a un solo cluster muy denso (por ejemplo, Indie Rock de los 2000s). Aquí, un filtro de "género" no sirve porque todos son Indie Rock. Las preguntas deben ser hiper-específicas: "¿Este álbum fue lanzado antes o después del año 2005?" o "¿Tiene el descriptor 'Melancholic' o 'Uplifting'?".