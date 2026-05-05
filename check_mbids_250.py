import urllib.request

albums = {
    "OK Computer": "Radiohead",
}

def check_cover(mbid):
    try:
        # Check specifically the front-250
        urllib.request.urlopen(f"https://coverartarchive.org/release/{mbid}/front-250")
        return True
    except Exception as e:
        # print(e)
        return False

import musicbrainzngs
musicbrainzngs.set_useragent('test3', '1.0', 'test@test.com')

for title, artist in albums.items():
    print(f"Buscando {title} - {artist}")
    res = musicbrainzngs.search_releases(artist=artist, release=title, limit=20)
    found = False
    for r in res.get('release-list', []):
        mbid = r['id']
        if check_cover(mbid):
            print(f"ENCONTRADO para {title}: {mbid}")
            found = True
            break
    if not found:
        print(f"No se encontró cover para {title}")
