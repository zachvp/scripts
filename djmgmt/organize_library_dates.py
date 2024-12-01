'''
# Summary
Given a Rekordbox music collection, moves each file to a directory path that corresponds to the date it was added.

For example, if the music library file 'TrackA.aiff' has a corresponding 'DateAdded'
attribute of '01/02/23 (Jan 2, 2023)', the new path will be
    '/library_root/2023/01 january/02/Artist/Album/TrackA.aiff'

## Assumptions
* The music library source files are in a flat directory structure. Any tracks in subfolders will be ignored.
* The XML collection file paths point to this flat music library.
'''

import sys
import os
import shutil
import xml.etree.ElementTree as ET
from urllib.parse import unquote
import argparse

# GLOBALS
## Read-only
ATTR_DATE_ADDED = 'DateAdded'
ATTR_PATH = 'Location'
PATH_LIBRARY_PIVOT = '/ZVP-MUSIC/DJing/'
XPATH_COLLECTION = './/COLLECTION'
DELIMITER = '->'

MAPPING_MONTH =\
{
    1  : 'january',
    2  : 'february',
    3  : 'march',
    4  : 'april',
    5  : 'may',
    6  : 'june',
    7  : 'july',
    8  : 'august',
    9  : 'september',
    10 : 'october',
    11 : 'november',
    12 : 'december',
}

# Helper functions
def date_path(date: str, mapping: dict) -> str:
    '''Returns a date-formatted directory path string. e.g:
        YYYY/MM MONTH_NAME / DD
        2024/ 01 january / 02
    
    Function parameters:
        date -- The YYYY-MM-DD date string to transform
        mapping -- The human-readable definitions for the months
    '''
    year, month, day = date.split('-')

    return f"{year}/{month} {mapping[int(month)]}/{day}"

def full_path(node: ET.Element, pivot: str, mapping: dict) -> str:
    '''Returns a formatted directory path based on the node's DateAdded field.

    Function arguments:
        node    -- The XML collection track data
        pivot   -- The substring between the collection root and the rest of the track directory path
        mapping -- The human-readable months
    '''
    date = node.attrib[ATTR_DATE_ADDED]
    path_components = node.attrib[ATTR_PATH].split(pivot)
    subpath_date = date_path(date, mapping)

    return f"{path_components[0]}{pivot}{subpath_date}/{path_components[1]}"

def collection_path_to_syspath(path: str) -> str:
    '''Transforms the given XML collection path to a directory path.

    Function arguments:
        path -- The URL-like collection path
    '''
    path_parts = path.split('/')

    return unquote('/' + '/'.join(path_parts[3:]))

def swap_root(path: str, root: str) -> str:
    '''Returns the given path with its root replaced.

    Function arguments:
        path -- The directory path
        root -- The new root to use
    '''
    if not root.endswith('/'):
        root += '/'

    root = path.replace('/Volumes/ZVP-MUSIC/DJing/', root)

    return root

# Dev functions
def dev_debug():
    test_str =\
    '''
        <TRACK TrackID="109970693" Name="花と鳥と山" Artist="haircuts for men" Composer="" Album="京都コネクション" Grouping="" Genre="Lounge/Ambient" Kind="AIFF File" Size="84226278" TotalTime="476" DiscNumber="0" TrackNumber="5" Year="2023" AverageBpm="134.00" DateAdded="2023-04-27" BitRate="1411" SampleRate="44100" Comments="8A - 1" PlayCount="1" Rating="0" Location="file://localhost/Volumes/ZVP-MUSIC/DJing/haircuts%20for%20men%20-%20%e8%8a%b1%e3%81%a8%e9%b3%a5%e3%81%a8%e5%b1%b1.aiff" Remixer="" Tonality="8A" Label="" Mix="">
          <TEMPO Inizio="0.126" Bpm="134.00" Metro="4/4" Battito="1" />
        </TRACK>'''
    t = ET.fromstring(test_str)
    print(t.tag)

    u = full_path(t, '/ZVP-MUSIC/DJing/', MAPPING_MONTH)
    print(u)

# Primary functions
def generate_new_paths(args: argparse.Namespace) -> list[str]:
    '''Generates a list of path mappings.
    Each item maps from the source path in the collection to the structured directory destination.
    '''
    collection = ET.parse(args.xml_collection_path).getroot().find(XPATH_COLLECTION)
    assert collection, f"unable to find {XPATH_COLLECTION} for path '{args.xml_collection_path}'"
    lines: list[str] = []

    for node in collection:
        # check if track is in collection root folder
        node_path_parts = node.attrib[ATTR_PATH].split('/')
        if node_path_parts[-2] == 'DJing' or args.output:
            # build each entry for the old and new path
            track_path_old = collection_path_to_syspath(node.attrib[ATTR_PATH])
            if args.output:
                track_path_old = swap_root(track_path_old, args.output)

            track_path_new = full_path(node, PATH_LIBRARY_PIVOT, MAPPING_MONTH)
            track_path_new = collection_path_to_syspath(track_path_new)
            if args.output:
                track_path_new = swap_root(track_path_new, args.output)

            if DELIMITER in track_path_old or DELIMITER in track_path_new:
                print(f'''
                    fatal: delimeter already exists in either {track_path_old} or {track_path_new}
                    exiting..
                    ''')
                sys.exit()

            lines.append(f"{track_path_old}{DELIMITER}{track_path_new}")
        else:
            print(f"warn: unexpected root {node_path_parts[-2]}, will skip")
    return lines

def move_files(args: argparse.Namespace, path_mappings: list[str]) -> None:
    '''Moves files according to the paths input mapping.'''
    for mapping in path_mappings:
        source, dest = mapping.split(DELIMITER)

        # interactive session
        if args.interactive:
            choice = input(f"info: will move file from '{source}' to '{dest}', continue? [Y/n]")
            if len(choice) > 0 and choice not in 'Yy':
                print("exit: user quit")
                sys.exit()

        # get the destination file's directory
        dest_dir =  '/'.join(dest.split('/')[:-1])

        # validate
        if not os.path.exists(source):
            print(f"info: skip: source path '{source}' does not exist")
            continue
        if os.path.exists(dest):
            print(f"info: skip: destination path '{dest}' exists")
            continue

        # create dir if it doesn't exist
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        shutil.move(source, dest)

def parse_args(valid_functions: set[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"The script function to run. One of: {valid_functions}.")
    parser.add_argument('xml_collection_path', type=str, help='The rekordbox library path containing the DateAdded history.')
    parser.add_argument('--output', '-o', type=str,\
        help='The path to use in place of the root path defined in the rekordbox xml.')
    parser.add_argument('-i', '--interactive', action='store_true', help='Run script in interactive mode.')
    parser.add_argument('--force', action='store_true', help='Skip all interaction safeguards and run the script.')

    args = parser.parse_args()

    if args.function not in valid_functions:
        parser.error(f"invalid parameter '{args.function}'")

    return args

# MAIN
if __name__ == '__main__':
    FUNCTION_GENERATE = 'generate'
    script_functions = {FUNCTION_GENERATE}
    script_args = parse_args(script_functions)

    if script_args.output:
        print(f"info: args output root dir: '{script_args.output}'")

    # check argument switches
    if not script_args.interactive and not script_args.force:
        main_choice = input("this is a destructive action, and interactive mode is disabled, continue? [y/N]")
        if main_choice == 'y':
            print(f"verbose: running organize({script_args.xml_collection_path})...")
        else:
            print("exit: user quit")
            sys.exit()

    print(f"verbose: running organize({script_args.xml_collection_path})")
    if script_args.function == FUNCTION_GENERATE:
        move_files(script_args, generate_new_paths(script_args))
