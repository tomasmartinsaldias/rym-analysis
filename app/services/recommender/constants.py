"""
app/recommender/constants.py
────────────────────────────
Definición de la jerarquía de clusters (Galaxias) y paleta de colores.
Actualizado según la nueva estructura de 45 clusters (20D).
"""

# Mapeo de Cluster ID -> Nombre de la Galaxia (Mega Cluster)
MEGA_CLUSTER_MAP = {
    # 1. Rock Alternativo e Indie
    13: "Rock Alternativo e Indie", 37: "Rock Alternativo e Indie", 36: "Rock Alternativo e Indie", 
    42: "Rock Alternativo e Indie", 41: "Rock Alternativo e Indie", 16: "Rock Alternativo e Indie",
    
    # 2. Hip Hop y R&B
    5: "Hip Hop y R&B", 6: "Hip Hop y R&B", 7: "Hip Hop y R&B", 8: "Hip Hop y R&B", 
    9: "Hip Hop y R&B", 40: "Hip Hop y R&B", 43: "Hip Hop y R&B",
    
    # 3. Metal y Hardcore
    29: "Metal y Hardcore", 11: "Metal y Hardcore", 3: "Metal y Hardcore", 10: "Metal y Hardcore", 
    15: "Metal y Hardcore", 14: "Metal y Hardcore", 4: "Metal y Hardcore", 12: "Metal y Hardcore",
    
    # 4. Rock Clásico y Progresivo
    28: "Rock Clásico y Progresivo", 20: "Rock Clásico y Progresivo", 21: "Rock Clásico y Progresivo", 
    22: "Rock Clásico y Progresivo", 27: "Rock Clásico y Progresivo", 23: "Rock Clásico y Progresivo",
    
    # 5. Cantautor y Folk
    30: "Cantautor y Folk", 35: "Cantautor y Folk", 34: "Cantautor y Folk",
    
    # 6. Electrónica, Pop y Sintetizadores
    38: "Electrónica, Pop y Sintetizadores", 44: "Electrónica, Pop y Sintetizadores", 
    39: "Electrónica, Pop y Sintetizadores", 31: "Electrónica, Pop y Sintetizadores", 
    32: "Electrónica, Pop y Sintetizadores",
    
    # 7. Jazz y Música Instrumental
    2: "Jazz y Música Instrumental", 1: "Jazz y Música Instrumental", 
    33: "Jazz y Música Instrumental", 26: "Jazz y Música Instrumental",
    
    # 8. Experimental y Post-Punk
    18: "Experimental y Post-Punk", 19: "Experimental y Post-Punk", 0: "Experimental y Post-Punk", 
    17: "Experimental y Post-Punk", 24: "Experimental y Post-Punk", 25: "Experimental y Post-Punk"
}

# Paleta de colores para las Galaxias (Estética Cinematic/Deep Space)
MEGA_CLUSTER_COLORS = {
    "Rock Alternativo e Indie": "#f9ca24",         # Yellow
    "Hip Hop y R&B": "#f0932b",                    # Orange
    "Metal y Hardcore": "#eb4d4b",                 # Red
    "Rock Clásico y Progresivo": "#00cec9",        # Cyan/Teal (Distinct from Orange)
    "Cantautor y Folk": "#6ab04c",                 # Green
    "Electrónica, Pop y Sintetizadores": "#e056fd", # Purple
    "Jazz y Música Instrumental": "#4834d4",       # Deep Blue
    "Experimental y Post-Punk": "#fd79a8",         # Pink/Magenta (Distinct from Blue)
    "Otros": "#535c68"
}

# Nombres descriptivos para los Micro Clusters (se muestran en tooltips)
CLUSTER_NAMES = {
    0: "Post-Rock y Experimental",
    1: "Jazz Fusion y Vanguardia",
    2: "Jazz Clásico (Bop/Modal)",
    3: "Metal Alternativo y Nu Metal",
    4: "Stoner y Metal Industrial",
    5: "Trap y Pop Rap",
    6: "Rap Clásico y Gangsta",
    7: "Jazz Rap y Conscious Hip Hop",
    8: "Rap de Mensaje y West Coast",
    9: "Hip Hop Experimental",
    10: "Black Metal y Metal Melódico",
    11: "Thrash y Groove Metal",
    12: "Punk y Pop Punk",
    13: "Rock Alternativo",
    14: "Metal Progresivo y Técnico",
    15: "Death Metal",
    16: "Post-Hardcore y Math Rock",
    17: "Noise Rock",
    18: "Post-Punk y Art Punk",
    19: "Rock Gótico y Oscuro",
    20: "Rock Progresivo",
    21: "Rock Sinfónico",
    22: "Rock Psicodélico Clásico",
    23: "Pop Rock Clásico",
    24: "Art Rock Experimental",
    25: "Industrial y Avant-Folk",
    26: "Ambient y Música de Cine",
    27: "Blues Rock y Garage",
    28: "Hard Rock y Glam",
    29: "Heavy Metal Clásico",
    30: "Cantautor y Folk Acústico",
    31: "Electrónica de Baile",
    32: "IDM y Trip Hop",
    33: "Soul, Funk y Jazz Vocal",
    34: "Folk Rock y Country Rock",
    35: "Folk Contemporáneo y Americana",
    36: "Indie Pop y Jangle Pop",
    37: "Indie Rock y Lo-Fi",
    38: "Synthpop y New Wave",
    39: "Art Pop",
    40: "Neo-Soul y R&B Moderno",
    41: "Psicodelia Moderna",
    42: "Dream Pop y Shoegaze",
    43: "R&B y Pop Comercial",
    44: "Electropop"
}

import colorsys

def _generate_micro_cluster_colors():
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

    def rgb_to_hex(rgb):
        return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"

    galaxy_to_micros = {}
    for cid, galaxy in MEGA_CLUSTER_MAP.items():
        galaxy_to_micros.setdefault(galaxy, []).append(cid)

    micro_colors = {}
    for galaxy, micros in galaxy_to_micros.items():
        base_hex = MEGA_CLUSTER_COLORS.get(galaxy, "#535c68")
        r, g, b = hex_to_rgb(base_hex)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        
        micros = sorted(micros)
        n = len(micros)
        
        for i, cid in enumerate(micros):
            step = i / max(1, n - 1) if n > 1 else 0.5
            
            # 1. Modificar H (Matiz): Variación tonal más sutil (+/- 0.025) para no convertir amarillo en naranja
            new_h = (h + 0.05 * (step - 0.5)) % 1.0
            
            # 2. Modificar S (Saturación): Variamos desde 0.65 (suave/elegante) hasta 1.0 (puro/vibrante)
            new_s = max(0.65, s * (0.70 + step * 0.30))
            
            # 3. Modificar V (Brillo): Piso muy alto (0.82 a 1.0) porque el amarillo y lima oscuros se ven marrones/sucios
            new_v = 0.82 + step * 0.18
            
            new_rgb = colorsys.hsv_to_rgb(new_h, new_s, new_v)
            micro_colors[cid] = rgb_to_hex(new_rgb)
            
    micro_colors[-1] = "#535c68"
    return micro_colors

MICRO_CLUSTER_COLORS = _generate_micro_cluster_colors()

