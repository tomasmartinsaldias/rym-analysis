import musicbrainzngs
musicbrainzngs.set_useragent('test', '1.0', 'test@test.com')
albums = [
    ('Radiohead', 'OK Computer'),
    ('Radiohead', 'Kid A'),
    ('Pink Floyd', 'The Dark Side of the Moon'),
    ('My Bloody Valentine', 'Loveless'),
    ('Kanye West', 'My Beautiful Dark Twisted Fantasy'),
    ('Radiohead', 'In Rainbows'),
    ('Pink Floyd', 'Wish You Were Here'),
    ('Neutral Milk Hotel', 'In the Aeroplane Over the Sea'),
    ('Radiohead', 'The Bends'),
    ('Kend Lamar', 'To Pimp a Butterfly')
]
for artist, title in albums:
    res = musicbrainzngs.search_releases(artist=artist, release=title, limit=1)
    if res.get('release-list'):
        print(f'"{title}": "{res["release-list"][0]["id"]}",')
