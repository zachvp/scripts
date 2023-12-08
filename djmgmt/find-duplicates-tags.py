'''
Uses a combination of audio file metadata to determine duplicates
'''

import os
import argparse
import mutagen

# debug
printed : dict[str, set[str]] = {}
relevant_keys: set[str] = set()
relevant_keys = {'genre', 'beatgrid', 'TENC', 'TOAL', 'TCOM', 'TDRC', 'USLT::eng', 'initialkey', 'TIT1', 'TCOP', 'TBPM', 'TOPE', 'cuepoints', 'TDRL', 'TSSE', 'TDEN', 'TPOS', 'WPUB', 'TSRC', 'artist', 'energy', 'TPE1', 'album', 'WOAF', 'TFLT', 'TDTG', 'key', 'metadata_block_picture', 'TCMP', 'TCON', 'PCNT', 'TALB', 'TDOR', 'comment', 'title', 'TPE2', 'TPE4', 'energylevel', 'TPUB', 'tracknumber', 'TLEN', 'TIT2'}

def get_track_key(track: mutagen.FileType, options: list[str]) -> str | None:
    try:
        for o in options:
            if o in track:
                return o
    except ValueError:
        return None

    return None

def dev_determine_relevant_keys(track: mutagen.FileType) -> None:
    # -- dev: determine possibly relevant keys
    # print(track.keys())
    ignore = { 'GEOB', 'TXXX', 'TRCK', 'COMM', 'TKEY', 'UFID', 'APIC', 'metadata_block', 'TCMP', 'TBPM', 'TENC', 'TPE1' }
    for k in track:
        skip = False
        for nope in ignore:
            if k.startswith(nope) or k == nope:
                skip = True
                break
        if skip or len(k) > 64:
            continue

        relevant_keys.add(k)

def dev_print_relevant_values(track: mutagen.FileType) -> None:
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

# script input
def script(root: str, artist_keys: list, title_keys: list) -> None:
    # script state
    file_set: set[str] = set()

    # script process
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            # skip hidden files
            if name[0] == '.':
                continue

            # build full filepath
            path = os.path.join(dirpath, name)

            # load track tags, check for errors
            try:
                track = mutagen.File(path)
                # track = ID3(path)
            except mutagen.MutagenError as e:
                print(f"error: {e}")
                continue

            if track is None or track.tags is None:
                print(f"error: unable to read '{path}'")
                continue

            # pull keys based on what's present in each track
            title_key = get_track_key(track, title_keys)
            artist_key = get_track_key(track, artist_keys)

            if title_key is None or artist_key is None:
                print(f"error: unable to find artist or title for '{path}'")
                continue

            # skip 'tracks' that don't contain both an artist and title
            if title_key not in track or artist_key not in track:
                print(f"WARN: unable to read title or artist for '{path}', skipping")
                continue

            # pull base tag info
            title = track[title_key]
            artist = track[artist_key]

            # some tags are stored as a list
            if isinstance(title, list):
                title = title[0]
            if isinstance(artist, list):
                artist = artist[0]

            # set item = concatenation of track title & artist
            item = f"{title}{artist}".lower()

            # check for duplicates based on set contents
            # before and after insertion
            count = len(file_set)

            file_set.add(item)
            if len(file_set) == count:
                print(path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='The path to the search directory root.')

    script_args = parser.parse_args()
    script_args.input = os.path.normpath(script_args.input)

    ARTIST_KEYS = ['TPE1', 'TPE2', 'TPE4', '©ART', 'Author', 'artist', 'TOPE']
    TITLE_KEYS = ['TIT2', '©nam', 'Title', 'title']

    script(script_args.input, ARTIST_KEYS, TITLE_KEYS)

    sorted_dict = dict(sorted(printed.items(), key=lambda item: item[0]))
    for p in sorted_dict:
        print(f"{p} -> {', '.join(sorted(printed[p]))}")
