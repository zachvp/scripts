'''
This script is rekordbox XML specific.
Its assumed that the music library is in a flat directory structure.
    Any tracks in subfolders will be ignored.
Its assumed that the collection XML file paths point to this flat music library.

Given a path to a music library and XML collection, this script will organize all tracks
in the libary so that its folder structure will be consistent with the 'DateAdded' track
attribute in the XML collection.

For example, if the music library file 'TrackA.aiff' has a corresponding 'DateAdded'
attribute of 01/02/23 (Jan 2, 2023), the new path will be
    '/library_root/2023/january/TrackA.aiff'

'''

import sys
import os
import shutil
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from typing import Any
import argparse

class WrapETElement:
    def __init__(self, e: ET.Element | Any | None):
        self.element = e

    def __iter__(self):
        for item in self.element:
            yield item

def date_path(date: str, mapping: dict) -> str:
    year, month, _ = date.split('-')

    return f"{year}/{mapping[int(month)]}"

def full_path(node: ET.Element, pivot: str, mapping: dict) -> str:
    date = node.attrib[ATTR_DATE_ADDED]
    path_components = node.attrib[ATTR_PATH].split(pivot)
    subpath_date = date_path(date, mapping)

    return f"{path_components[0]}{pivot}{subpath_date}/{path_components[1]}"

def collection_path_to_syspath(path: str) -> str:
    path_parts = path.split('/')

    return unquote('/' + '/'.join(path_parts[3:]))

def swap_root(path: str, root: str) -> str:
    if root[-1] != '/':
        root += '/'

    root = path.replace('/Volumes/ZVP-MUSIC/DJing/', root)

    return root

def generate_matching_paths(args: argparse.Namespace) -> list[str]:
    collection = WrapETElement(ET.parse(args.xml_collection_path).getroot().find(XPATH_COLLECTION))
    lines: list[str] = []
    source_lines : dict[str, str] = {}
    dest_lines : dict[str, str] = {}

    for working_dir, _, filenames in os.walk(args.output):
        for filename in filenames:
            source_lines[filename] = os.path.join(working_dir, filename)

    for node in collection:
        dest_line = collection_path_to_syspath(node.attrib[ATTR_PATH])
        dest_line = swap_root(dest_line, args.output)
        filename = os.path.split(dest_line)[1]
        dest_lines[filename] = dest_line

    for key, source_line in source_lines.items():
        if key in dest_lines:
            lines.append(f"{source_line}{DELIMITER}{dest_lines[key]}")

    return lines

def generate_new_paths(args: argparse.Namespace) -> list[str]:
    collection = WrapETElement(ET.parse(args.xml_collection_path).getroot().find(XPATH_COLLECTION))
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

def organize(args: argparse.Namespace, paths: list[str]) -> None:
    for path in paths:
        source, dest = path.split(DELIMITER)

        # interactive session
        if args.interactive:
            choice = input(f"info: will move file from '{source}' to '{dest}', continue? [Y/n]")
            if len(choice) > 0 and choice not in 'Yy':
                print("exit: user quit")
                sys.exit()

        target_dir_path =  '/'.join(dest.split('/')[:-1])

        # validate
        if not os.path.exists(source):
            print(f"warn: source path '{source}' does not exist, skipping")
            continue
        if os.path.exists(dest):
            print(f"warn: destination path '{dest}' exists, skipping")
            continue

        # create dir if it doesn't exist
        if not os.path.exists(target_dir_path):
            os.makedirs(target_dir_path)

        shutil.move(source, dest)

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

def parse_args(valid_functions: set[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"The script function to run. One of: {valid_functions}")
    parser.add_argument('xml_collection_path', type=str, help='The rekordbox library path containing the DateAdded history')
    parser.add_argument('--output', '-o', type=str,\
        help='the root path to use in place of the path defined in the rekordbox xml')
    parser.add_argument('-i', '--interactive', action='store_true', help='run script in interactive mode')

    args = parser.parse_args()

    if args.function not in valid_functions:
        parser.error(f"invalid parameter '{args.function}'")

    return args

# MAIN
if __name__ == '__main__':
    FUNCTION_GENERATE = 'generate'
    FUNCTION_MATCH = 'match'
    script_functions = {FUNCTION_GENERATE, FUNCTION_MATCH}
    script_args = parse_args(script_functions)

    if script_args.output:
        print(f"info: args output root dir: '{script_args.output}'")

    # check switches
    if not script_args.interactive:
        main_choice = input("this is a destructive action, and interactive mode is disabled, continue? [y/N]")
        if main_choice == 'y':
            print(f"verbose: running organize({script_args.xml_collection_path})...")
        else:
            print("exit: user quit")
            sys.exit()

    print('verbose: interactive enabled')
    print(f"verbose: running organize({script_args.xml_collection_path})")
    if script_args.function == FUNCTION_GENERATE:
        organize(script_args, generate_new_paths(script_args))
    elif script_args.function == FUNCTION_MATCH:
        # todo: this function does not seem to work - files end up redundantly nested
        # organize(script_args, generate_matching_paths(script_args))
        print("Error: this function is borked. Ensure that the output directory is flattened and only contains audio files.")
