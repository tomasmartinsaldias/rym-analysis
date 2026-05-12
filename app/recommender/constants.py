"""
app/recommender/constants.py
────────────────────────────
Definición de la jerarquía de clusters (Galaxias) y paleta de colores.
"""

# Mapeo de Cluster ID -> Nombre de la Galaxia (Mega Cluster)
MEGA_CLUSTER_MAP = {
    # 1. Hip Hop & Beats
    8: "Hip Hop & Beats", 13: "Hip Hop & Beats", 14: "Hip Hop & Beats", 19: "Hip Hop & Beats",
    
    # 2. Jazz, Soul & Grooves
    1: "Jazz, Soul & Grooves", 2: "Jazz, Soul & Grooves", 27: "Jazz, Soul & Grooves",
    
    # 3. Metal & Hardcore
    4: "Metal & Hardcore", 12: "Metal & Hardcore", 15: "Metal & Hardcore", 
    16: "Metal & Hardcore", 22: "Metal & Hardcore", 23: "Metal & Hardcore", 25: "Metal & Hardcore",
    
    # 4. Indie & Folk
    32: "Indie & Folk", 33: "Indie & Folk", 34: "Indie & Folk", 35: "Indie & Folk", 36: "Indie & Folk",
    
    # 5. Dreamy & Psychedelic
    5: "Dreamy & Psychedelic", 9: "Dreamy & Psychedelic", 37: "Dreamy & Psychedelic", 38: "Dreamy & Psychedelic",
    
    # 6. Post-Punk & Alternative
    0: "Post-Punk & Alternative", 11: "Post-Punk & Alternative", 17: "Post-Punk & Alternative", 
    18: "Post-Punk & Alternative", 28: "Post-Punk & Alternative", 29: "Post-Punk & Alternative",
    
    # 7. Pop & Art Pop
    26: "Pop & Art Pop", 30: "Pop & Art Pop", 31: "Pop & Art Pop",
    
    # 8. Classic & Prog Rock
    3: "Classic & Prog Rock", 6: "Classic & Prog Rock", 7: "Classic & Prog Rock", 
    21: "Classic & Prog Rock", 24: "Classic & Prog Rock",
    
    # 9. Ambient & IDM
    10: "Ambient & IDM", 20: "Ambient & IDM"
}

# Paleta de colores para las Galaxias (Estética Cinematic/Deep Space)
MEGA_CLUSTER_COLORS = {
    "Hip Hop & Beats": "#f0932b",          # Spiced Orange
    "Jazz, Soul & Grooves": "#6ab04c",     # Fresh Green
    "Metal & Hardcore": "#eb4d4b",         # Carmine Red
    "Indie & Folk": "#f9ca24",             # Bee Keeper Yellow
    "Dreamy & Psychedelic": "#7ed6df",     # Middle Blue
    "Post-Punk & Alternative": "#686de0",  # Exodus Blue/Purple
    "Pop & Art Pop": "#e056fd",            # Heliotrope Purple
    "Classic & Prog Rock": "#ffbe76",      # Topaz
    "Ambient & IDM": "#4834d4",            # Deep Deep Blue
    "Otros": "#535c68"                     # Wizard Grey (más saturado)
}

# Nombres descriptivos para los Micro Clusters (se muestran en tooltips)
CLUSTER_NAMES = {
    0: "Punk & Pop Punk",
    1: "Jazz Fusion",
    2: "Hard Bop & Post-Bop",
    3: "Progressive Rock",
    4: "Thrash & Groove Metal",
    5: "Post-Rock",
    6: "Pop Rock",
    7: "Art & Experimental Rock",
    8: "Pop Rap & Trap",
    9: "Psychedelic Rock",
    10: "Ambient & Drone",
    11: "Post-Hardcore & Noise Rock",
    12: "Black & Post-Metal",
    13: "Abstract & West Coast Hip Hop",
    14: "East Coast Hip Hop",
    15: "Progressive Metal",
    16: "Death Metal",
    17: "Post-Punk & Gothic",
    18: "Art Punk & Post-Punk",
    19: "Beats & Plunderphonics",
    20: "IDM & Trip Hop",
    21: "Blues Rock & Garage",
    22: "Stoner & Sludge Metal",
    23: "Alternative & Nu Metal",
    24: "Hard Rock & Glam",
    25: "Heavy Metal",
    26: "Art Pop & Avant-Pop",
    27: "Soul, Funk & Reggae",
    28: "Alternative Rock",
    29: "Alt-Pop & Power Pop",
    30: "Electropop & R&B",
    31: "Synthpop & New Wave",
    32: "Indie Folk & Singer-Songwriter",
    33: "Folk Rock & Americana",
    34: "Contemporary Folk & Slowcore",
    35: "Indie Rock & Lo-Fi",
    36: "Indie Pop & Jangle Pop",
    37: "Neo-Psychedelia & Psych Pop",
    38: "Dream Pop & Shoegaze"
}
