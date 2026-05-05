import urllib.request
import json

albums = {
    "OK Computer": "Radiohead",
    "Loveless": "My Bloody Valentine",
    "To Pimp a Butterfly": "Kendrick Lamar"
}

def check_cover(mbid):
    try:
        urllib.request.urlopen(f"https://coverartarchive.org/release/{mbid}")
        return True
    except Exception:
        return False

import musicbrainzngs
musicbrainzngs.set_useragent('test2', '1.0', 'test@test.com')

for title, artist in albums.items():
    print(f"Buscando {title} - {artist}")
    res = musicbrainzngs.search_releases(artist=artist, release=title, limit=10)
    found = False
    for r in res.get('release-list', []):
        mbid = r['id']
        if check_cover(mbid):
            print(f"ENCONTRADO para {title}: {mbid}")
            found = True
            break
    if not found:
        print(f"No se encontró cover para {title}")
