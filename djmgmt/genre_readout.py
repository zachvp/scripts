'''
Outputs genres according to the given rekordbox XML collection file.
'''

import os
import argparse
from collections import defaultdict
import xml.etree.ElementTree as ET
import organize_library_dates as ORG

# print the tracks present in collection, but not the given playlist
def output_missing_tracks(playlist_ids: set[str], collection: ORG.WrapETElement) -> list[str]:
    readout = []

    for track in collection:
        if track.attrib['TrackID'] not in playlist_ids:
            item = f"{track.attrib['Name']}\t{track.attrib['Artist']}\t{track.attrib['Genre']}\t{track.attrib['DateAdded']}"
            readout.append(item)

    for item in readout:
        print(f"{item}")
    return readout

# print the genre and count for all tracks in the given file
def output_genres_verbose(playlist_ids: set[str], collection: ORG.WrapETElement) -> list[str]:
    readout: dict[str, int] = defaultdict(int)
    lines: list[str] = []

    # search collection for the file tracks,
    # and gather the relevant data
    for track in collection:
        if track.attrib['TrackID'] in playlist_ids:
            key = track.attrib['Genre']
            readout[key] += 1

    for genre, count in readout.items():
        line = f"{genre}\t{count}"
        lines.append(line)
        print(line)
    return lines

def output_genres_short(playlist_ids: set[str], collection: ORG.WrapETElement) -> list[str]:
    readout : dict[str, int] = defaultdict(int)
    lines : list[str] = []

    # search collection for the file tracks,
    # and gather the relevant data
    for track in collection:
        if track.attrib['TrackID'] in playlist_ids:
            shortened = track.attrib['Genre'].split('/')

            # for longer genres, remove the last 2 subgenres
            if len(shortened) > 2:
                difference = len(shortened) - 2
                shortened = shortened[:-difference]
            shortened = '/'.join(shortened)

            key = shortened
            readout[key] += 1

    for genre, count in readout.items():
        line = f"{genre}\t{count}"
        lines.append(line)
        print(line)
    return lines

def output_genre_category(playlist_ids: set[str], collection: ORG.WrapETElement) -> set[str]:
    categories: set[str] = set()

    for track in collection:
        if track.attrib['TrackID'] in playlist_ids:
            genre_elements = track.attrib['Genre'].split('/')
            for e in genre_elements:
                categories.add(e)

    for c in categories:
        print(c)
    return categories

def output_renamed_genres(playlist_ids: set[str], collection) -> set[str]:
    map_data = create_genre_map('data/read/genre-shorthand-mapping.txt')
    genres: set[str] = set()

    for track in collection:
        if track.attrib['TrackID'] in playlist_ids:
            genre_elements = track.attrib['Genre'].split('/')
            if '' in genre_elements:
                genre_elements.remove('')
            renamed : list[str] = ['' for _ in range(len(genre_elements))]

            for i, e in enumerate(genre_elements):
                renamed[i] = map_data[e]
                # print(f"{i}: {map_data[e]}")
            genres.add('.'.join(renamed))
    for g in genres:
        print(g)
    return genres

def create_genre_map(path: str) -> dict[str, str]:
    map_data: dict[str, str] = {}
    validation: set[str] = set()

    with open(path, 'r', encoding='utf-8') as genre_map:
        lines = genre_map.readlines()
        for line in lines:
            components = line.strip().split('\t')
            if components[0] in map_data:
                print(f'warn: duplicate genre element: {components[0]}')
            assert len(components) == 2, f"Invalid components: {components}"
            map_data[components[0]] = components[1]
    for _, item in map_data.items():
        if item in validation:
            print(f'warn: duplicate shorthand: {item}')
        validation.add(item)

    return map_data

def output_collection_filter(root: ORG.WrapETElement, genre: str) -> list[str]:
    output : list[str] = []
    for track in root:
        if track.attrib['Genre'] == genre:
            output.append(ORG.collection_path_to_syspath(track.attrib['Location']))
    for line in output:
        print(line)
    return output

def parse_args(valid_modes: set[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=str, help="The input path to the XML collection.")
    parser.add_argument('mode', type=str, help=f"The script output mode. One of '{valid_modes}'.")
    parser.add_argument('--parameters', '-p', type=str, help="The paramaters for the given mode.")

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)

    if args.mode not in valid_modes:
        parser.error(f"Invalid function: {args.mode}. Expect one of '{valid_modes}'.")

    return args

def script(args: argparse.Namespace) -> None:
    # data: input document
    tree = ET.parse(args.input).getroot()

    collection = ORG.WrapETElement(tree.find('.//COLLECTION'))
    assert collection and collection.element, "invalid node search for 'COLLECTION'"

    pruned = ORG.WrapETElement(tree.find('.//NODE[@Name="_pruned"]'))
    assert pruned and pruned.element, "invalid node search for '_pruned'"

    # data: script
    playlist_ids : set[str] = set()

    # collect the playlist IDs
    for track in pruned:
        playlist_ids.add(track.attrib['Key'])

    # call requested script mode
    if args.mode == MODE_SHORT:
        output_genres_short(playlist_ids, collection)
    elif args.mode == MODE_VERBOSE:
        output_genres_verbose(playlist_ids, collection)
    elif args.mode == MODE_MISSING:
        output_missing_tracks(playlist_ids, collection)
    elif args.mode == MODE_CATEGORY:
        output_genre_category(playlist_ids, collection)
    elif args.mode == MODE_RENAMED:
        output_renamed_genres(playlist_ids, collection)
    elif args.mode == MODE_FILTER:
        output_collection_filter(collection, args.parameters)

# constants
MODE_SHORT = 'short'
MODE_VERBOSE = 'verbose'
MODE_MISSING = 'missing'
MODE_CATEGORY = 'category'
MODE_RENAMED = 'renamed'
MODE_FILTER = 'filter'

if __name__ == '__main__':
    MODES: set[str] = {
        MODE_SHORT,
        MODE_VERBOSE,
        MODE_MISSING,
        MODE_CATEGORY,
        MODE_RENAMED,
        MODE_FILTER
    }
    script(parse_args(MODES))
