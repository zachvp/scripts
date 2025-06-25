import mutagen
import logging
import io
from PIL import Image
from typing import Optional, Tuple

import mutagen.flac
import mutagen.id3

class Tags:
    def __init__(self,
                 artist          : Optional[str]=None,
                 album           : Optional[str]=None,
                 title           : Optional[str]=None,
                 genre           : Optional[str]=None,
                 key             : Optional[str]=None,
                 cover_image     : Optional[Image.Image] = None,
                 cover_image_str : Optional[str]=None):
        self.artist = artist
        self.album = album
        self.title = title
        self.genre = genre
        self.key = key
        self.cover_image = cover_image
        self.cover_image_str = cover_image_str
    
    def __str__(self) -> str:
        output = {
            'artist'      : self.artist,
            'album'       : self.album,
            'title'       : self.title,
            'genre'       : self.genre,
            'key'         : self.key,
            'cover_image' : self.cover_image_str
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

def extract_tag_value(track: mutagen.FileType, tag_keys: set[str]) -> Optional[str]:
    key = get_track_key(track, tag_keys)
    value = str(track[key]) if key and key in track else None

    return value

def extract_cover_image(track: mutagen.FileType) -> Tuple[Optional[Image.Image], Optional[str]]:
    image: Optional[Image.Image] = None
    image_type: Optional[str] = None
    data = None
    
    # extract image for files with ID3 tags (MP3, AIFF, WAV)
    for tag in track.tags.values(): # type: ignore
        if isinstance(tag, mutagen.id3.APIC):
            data = tag.data # type: ignore
            image_type = str(tag.type) # type: ignore
    
    # extract image for FLAC files
    if image is None and isinstance(track, mutagen.flac.FLAC): # type: ignore
        if track.pictures:  # type: ignore
            pic = track.pictures[0] # type: ignore
            data = pic.data
            # standardize the type
            image_type = str(mutagen.id3.PictureType(pic.type))
    
    # Load the image data
    if data:     
        try:
            image = Image.open(io.BytesIO(data))
            image.load()
        except Exception as e:
            logging.warning(f"Invalid image data:\n{e}")
    
    return image, image_type

def read_tags(path: str) -> Optional[Tags]:
    # define possible tag keys
    artist_keys    = {'TPE1', 'TPE2', 'TPE4', '©ART', 'Author', 'artist', 'TOPE'}
    album_keys     = {'TALB', 'TOAL', 'album'}
    title_keys     = {'TIT2', '©nam', 'Title', 'title'}
    genre_keys     = {'TCON', 'genre'}
    music_key_keys = {'TKEY', 'initialkey', 'key'}

    # load track tags, check for errors
    try:
        track = mutagen.File(path)
    except mutagen.MutagenError as e:
        logging.error(f"mutagen.MutagenError:\n{e}\npath: '{path}'")
        return None
    if track is None or track.tags is None:
        logging.error(f"unable to read '{path}'")
        return None

    # extract tag values
    title = extract_tag_value(track, title_keys)
    artist = extract_tag_value(track, artist_keys)
    album = extract_tag_value(track, album_keys)
    genre = extract_tag_value(track, genre_keys)
    key = extract_tag_value(track, music_key_keys)
    cover_image, cover_string = extract_cover_image(track)
    
    # failure if title and artist not present
    if title is None and artist is None:
        logging.error(f"unable to find title and artist tags for '{path}'")
        return None
    
    # log warning if critical tags are absent
    if artist is None or title is None:
        logging.warning(f"missing title or artist for '{path}'")

    return Tags(artist, album, title, genre, key, cover_image, cover_string)

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
