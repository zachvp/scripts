from typing import Optional
import mutagen
import logging

class Tags:
    def __init__(self, artist: Optional[str]=None, album: Optional[str]=None, title: Optional[str]=None, genre: Optional[str]=None, key: Optional[str]=None):
        self.artist = artist
        self.album = album
        self.title = title
        self.genre = genre
        self.key = key
    
    def __str__(self) -> str:
        output = {
            'artist': self.artist,
            'album' : self.album,
            'title' : self.title,
            'genre' : self.genre,
            'key'   : self.key
        }
        return str(output)

# DEV - Investigation
relevant_keys = {'genre', 'beatgrid', 'TENC', 'TOAL', 'TCOM', 'TDRC', 'USLT::eng', 'initialkey', 'TIT1', 'TCOP', 'TBPM', 'TOPE', 'cuepoints', 'TDRL', 'TSSE', 'TDEN', 'TPOS', 'WPUB', 'TSRC', 'artist', 'energy', 'TPE1', 'album', 'WOAF', 'TFLT', 'TDTG', 'key', 'metadata_block_picture', 'TCMP', 'TCON', 'PCNT', 'TALB', 'TDOR', 'comment', 'title', 'TPE2', 'TPE4', 'energylevel', 'TPUB', 'tracknumber', 'TLEN', 'TIT2'}

def dev_determine_relevant_keys(track: mutagen.FileType) -> set[str]:
    # -- dev: determine possibly relevant keys
    # print(track.keys())
    # ignore = { 'GEOB', 'COMM', 'UFID', 'APIC', 'metadata_block', 'TCMP', 'TENC' }
    ignore = {}
    relevant_keys: set[str] = set()
    for k in track:
        skip = False
        for nope in ignore:
            if k.startswith(nope) or k == nope:
                skip = True
                break
        if skip or len(k) > 64:
            continue

        relevant_keys.add(k)
    return relevant_keys

def dev_extract_tags(track: mutagen.FileType, relevant_keys: set[str]) -> dict[str, set[str]]:
    output : dict[str, set[str]] = {}
    for k in relevant_keys:
        if track is not None and k in track:
            if len(str(track[k])) < 64:
                # assume garbage otherwise
                line = f"{track[k]}"
                if k not in output:
                    # print_output.append(f"{k} : {track[k]}")
                    output[k] = {line}
                else:
                    output[k].add(line)
    return output

def dev_inspect_tags(path: str) -> None:
    try:
        track = mutagen.File(path)
    except mutagen.MutagenError as e:
        logging.error(f"mutagen.MutagenError:\n{e}\npath: '{path}'")
        return None
    assert track, "track not loaded"
    print(dev_extract_tags(track, dev_determine_relevant_keys(track)))

# Primary functions
def get_track_key(track: mutagen.FileType, options: set[str]) -> Optional[str]:
    '''Tries to find a key present in the given track based on the given options.'''
    try:
        for o in options:
            if o in track:
                return o
    except ValueError as error:
        logging.error(f"unable to find key for track: {error}")
        return None

    return None

def read_tags(path: str) -> Optional[Tags]:
    artist_keys = {'TPE1', 'TPE2', 'TPE4', '©ART', 'Author', 'artist', 'TOPE'}
    album_keys = {'TALB', 'TOAL', 'album'}
    title_keys = {'TIT2', '©nam', 'Title', 'title'}
    genre_keys = {'TCON', 'genre'}
    key_keys = {'TKEY', 'initialkey', 'key'}

    # load track tags, check for errors
    try:
        track = mutagen.File(path)
    except mutagen.MutagenError as e:
        logging.error(f"mutagen.MutagenError:\n{e}\npath: '{path}'")
        return None

    if track is None or track.tags is None:
        logging.error(f"unable to read '{path}'")
        return None

    # pull keys based on what's present in each track
    title_key = get_track_key(track, title_keys)
    artist_key = get_track_key(track, artist_keys)
    album_key = get_track_key(track, album_keys)
    genre_key = get_track_key(track, genre_keys)
    key_key = get_track_key(track, key_keys)

    if title_key is None and artist_key is None:
        logging.error(f"unable to find any valid tags for '{path}'")
        return None

    # skip 'tracks' that don't contain both an artist and title
    if title_key not in track and artist_key not in track:
        logging.error(f"unable to read any valid tags for '{path}'")
        return None

    # pull base tag info
    title = track[title_key] if title_key in track else None
    artist = track[artist_key] if artist_key in track else None
    album = track[album_key] if album_key in track else None
    genre = track[genre_key] if genre_key in track else None
    key = track[key_key] if key_key in track else None

    # some tags are stored as a list
    if isinstance(title, list):
        title = title[0]
    if isinstance(artist, list):
        artist = artist[0]
    if isinstance(album, list):
        album = album[0]
    if isinstance(genre, list):
        genre = genre[0]
    if isinstance(key, list):
        key = key[0]
    
    # convert to string or leave as None
    if title is not None:
        title = str(title)
    if artist is not None:
        artist = str(artist)
    if album is not None:
        album = str(album)
    if genre is not None:
        genre = str(genre)
    if key is not None:
        key = str(key)
    
    # log warning if critical tags are absent
    if artist is None or title is None:
        logging.warning(f"missing title or artist for '{path}'")

    return Tags(artist, album, title, genre, key)

def basic_identifier(title: str, artist: str) -> str:
    if not title:
        title = 'none'
    if not artist:
        artist = 'none'
    
    return f"{artist} - {title}".strip().lower()

if __name__ == '__main__':
    # dev testing
    paths = [
        "/Users/user/Music/DJ/02 In All You See A Woman.aif",
        "/Users/user/developer/test-private/tracks/03 - 暴風一族 (Remix).mp3",
        "/Users/user/Music/DJ/Ferra Black - Vibra (Sera de Villalta Remix).wav"
    ]
    for p in paths:
        dev_inspect_tags(p)
        print()
        
    '''
    Output:
        {'TXXX:EnergyLevel': {'4'},
        'TBPM': {'102'},
        'TCON': {'zzz'},
        'TDRC': {'2006'},
        'TIT2': {'In All You See A Woman'},
        'TPE1': {'Kathy Diamond'},
        'TXXX:SERATO_PLAYCOUNT': {'0'},
        'TALB': {'Miss Diamond To You'},
        'COMM:iTunes_CDDB_TrackNumber:eng': {'2'},
        'TRCK': {'2/14'},
        'TPOS': {'1/1'},
        'TKEY': {'1A'},
        'RVA2:SeratoGain': {'Master volume: +0.0000 dB/0.0000'},
        'COMM::eng': {'1A - 4'},
        'COMM:iTunPGAP:eng': {'0'}}

        {'TXXX:EnergyLevel': {'7'},
        'COMM::eng': {'5A - Energy 7'},
        'TCON': {'House/Tech/Indie/Disco'},
        'TPE2': {'張國榮'},
        'TDRC': {'2006'},
        'TIT2': {'暴風一族 [Bao Feng Yi Zu] (Remix)'},
        'TPE1': {'張國榮'},
        'COMM:ID3v1 Comment:eng': {'5A - Energy 7'},
        'TALB': {'Leslie Remix'},
        'TRCK': {'3/4'},
        'TPOS': {'1/1'},
        'TKEY': {'5A'},
        'TCOP': {'© 2006 Cinepoly Records Co. Ltd.'}}

        {'TIT2': {'Vibra (Sera de Villalta Remix)'},
        'TXXX:EnergyLevel': {'5'},
        'TPE1': {'Ferra Black'},
        'TCON': {'House/Deep/Tech/'},
        'TKEY': {'4A'},
        'COMM::eng': {'4A - 5'}}
    '''
