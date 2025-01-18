from typing import Optional
import mutagen

class Tags:
    def __init__(self, artist: Optional[str]=None, album: Optional[str]=None, title: Optional[str]=None):
        self.artist = artist
        self.album = album
        self.title = title

# DEV - Investigation
# relevant_keys = {'genre', 'beatgrid', 'TENC', 'TOAL', 'TCOM', 'TDRC', 'USLT::eng', 'initialkey', 'TIT1', 'TCOP', 'TBPM', 'TOPE', 'cuepoints', 'TDRL', 'TSSE', 'TDEN', 'TPOS', 'WPUB', 'TSRC', 'artist', 'energy', 'TPE1', 'album', 'WOAF', 'TFLT', 'TDTG', 'key', 'metadata_block_picture', 'TCMP', 'TCON', 'PCNT', 'TALB', 'TDOR', 'comment', 'title', 'TPE2', 'TPE4', 'energylevel', 'TPUB', 'tracknumber', 'TLEN', 'TIT2'}

def dev_determine_relevant_keys(track: mutagen.FileType) -> set[str]:
    # -- dev: determine possibly relevant keys
    # print(track.keys())
    ignore = { 'GEOB', 'TXXX', 'TRCK', 'COMM', 'TKEY', 'UFID', 'APIC', 'metadata_block', 'TCMP', 'TBPM', 'TENC', 'TPE1' }
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

def dev_print_relevant_values(track: mutagen.FileType, relevant_keys: set[str]) -> dict[str, set[str]]:
    printed : dict[str, set[str]] = {}
    for k in relevant_keys:
        if track is not None and k in track:
            if len(str(track[k])) < 64:
                # assume garbage otherwise
                line = f"{track[k]}"
                if k not in printed:
                    # print_output.append(f"{k} : {track[k]}")
                    printed[k] = {line}
                else:
                    printed[k].add(line)
    return printed

def get_track_key(track: mutagen.FileType, options: set[str]) -> Optional[str]:
    '''Tries to find a key present in the given track based on the given options.'''
    try:
        for o in options:
            if o in track:
                return o
    except ValueError as error:
        print(f"error: unable to find key for track: {error}")
        return None

    return None

def read_tags(path: str) -> Optional[Tags]:
    artist_keys = {'TPE1', 'TPE2', 'TPE4', '©ART', 'Author', 'artist', 'TOPE'}
    album_keys = {'TALB', 'TOAL', 'album'}
    title_keys = {'TIT2', '©nam', 'Title', 'title'}

    # load track tags, check for errors
    try:
        track = mutagen.File(path)
    except mutagen.MutagenError as e:
        print(f"mutagen.MutagenError:\n{e}\npath: '{path}'")
        return None

    if track is None or track.tags is None:
        print(f"error: unable to read '{path}'")
        return None

    # pull keys based on what's present in each track
    title_key = get_track_key(track, title_keys)
    artist_key = get_track_key(track, artist_keys)
    album_key = get_track_key(track, album_keys)

    if title_key is None and artist_key is None and album_key is None:
        print(f"error: unable to find any valid tags for '{path}'")
        return None

    # skip 'tracks' that don't contain both an artist and title
    if title_key not in track and artist_key not in track and album_key not in track:
        print(f"error: unable to read any valid tags for '{path}'")
        return None

    # pull base tag info
    title = track[title_key] if title_key in track else None
    artist = track[artist_key] if artist_key in track else None
    album = track[album_key] if album_key in track else None

    # some tags are stored as a list
    if isinstance(title, list):
        title = title[0]
    if isinstance(artist, list):
        artist = artist[0]
    if isinstance(album, list):
        album = album[0]

    return Tags(str(artist), str(album), str(title))