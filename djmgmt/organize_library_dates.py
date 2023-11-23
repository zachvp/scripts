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

def find_track(path_collection: str, filename: str) -> ET.Element | None:
    collection = WrapETElement(ET.parse(path_collection).getroot().find(XPATH_COLLECTION))

    for node in collection:
        node_filename = node.attrib[ATTR_PATH].split('/')[-1]
        # print(f"node_filename: {node_filename}")
        # print(f"{unquote(filename)} == {unquote(node_filename)}?")
        if unquote(filename) == unquote(node_filename):
            # print(f"search for file '{filename}' matches node {node_filename}")
            return node
    return None

def collection_path_to_syspath(path: str) -> str:
    path_parts = path.split('/')

    return unquote('/' + '/'.join(path_parts[3:]))

def swap_root(path: str, root: str) -> str:
    if root[-1] != '/':
        root += '/'

    root = path.replace('/Volumes/ZVP-MUSIC/DJing/', root)

    return root

def generate_new_paths(path_collection: str) -> list:
    collection = WrapETElement(ET.parse(path_collection).getroot().find(XPATH_COLLECTION))
    lines = []

    for node in collection:
        # check if track is in collection root folder
        node_path_parts = node.attrib[ATTR_PATH].split('/')
        if node_path_parts[-2] == 'DJing':
            # build each entry for the old and new path
            track_path_old = collection_path_to_syspath(node.attrib[ATTR_PATH])
            track_path_old = swap_root(track_path_old, SPOOF_ROOT)

            track_path_new = full_path(node, PATH_LIBRARY_PIVOT, MAPPING_MONTH)
            track_path_new = collection_path_to_syspath(track_path_new)
            track_path_new = swap_root(track_path_new, SPOOF_ROOT)

            if DELIMITER in track_path_old or DELIMITER in track_path_new:
                print(f'''
                    fatal: delimeter already exists in either {track_path_old} or {track_path_new}
                    exiting..
                    ''')
                sys.exit()

            lines.append(f"{track_path_old}->{track_path_new}")
        else:
            print(f"warn: track {unquote(node.attrib[ATTR_PATH])} is not in root, will skip")
    return lines

def organize(path_collection: str) -> None:
    new_paths = generate_new_paths(path_collection)

    for path in new_paths:
        source, dest = path.split('->')
        # print(f"debug: {path.split('->')}")

        # interactive session
        if INTERACTIVE:
            choice = input(f"info: will move file from '{source}' to '{dest}', continue? [Y/n]")
            if len(choice) > 0 and choice not in 'Yy':
                print("exit: user quit")
                sys.exit()

        target_dir_path =  '/'.join(dest.split('/')[:-1])
        print(target_dir_path)

        # validate
        if not os.path.exists(source):
            print(f"warn: source path '{source}' does not exist, skipping")
            continue

        # create dir if it doesn't exist
        if not os.path.exists(target_dir_path):
            # /Users/zachvp/backups/DJing/2021/march/02 Can't Resist (Bimbo Jones Full Mix).aiff
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

    # print(unquote("Planetary%20Assault%20Systems%20-%20Desert%20Races%20(Or.aiff"))
    # print(*generate_new_paths(sys.argv[1], spoof_root=sys.argv[2]))

# DEV - TESTING
SPOOF_ROOT = sys.argv[2]

# GLOBALS
## Mutable
VERBOSE = False
INTERACTIVE = False

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


# MAIN
if __name__ == '__main__':
    if len(sys.argv) > 3:
        if sys.argv[3] == '-v':
            VERBOSE = True
            print('verbose: verbose enabled')
        elif sys.argv[3] == '-i':
            print('verbose: interactive enabled')
            INTERACTIVE = True
            print(INTERACTIVE)
            organize(sys.argv[1])
        elif sys.argv[3] == '--force':
            organize(sys.argv[1])
        else:
            print('error: unrecognized argument: {sys.argv[3]}')
    else:
        main_choice = input("this is a destructive action, and interactive mode is disabled, continue? [y/N]")
        if main_choice == 'y':
            organize(sys.argv[1])
        else:
            print("exit: user quit")