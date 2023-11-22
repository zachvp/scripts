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
from urllib.parse import quote

def date_path(date: str, mapping: dict) -> str:
    year, month, _ = date.split('-')

    return f"{year}/{mapping[int(month)]}"

def full_path(node: ET.Element, pivot: str, mapping: dict) -> str:
    date = node.attrib[ATTR_DATE_ADDED]
    path_components = node.attrib[ATTR_PATH].split(pivot)
    subpath_date = date_path(date, mapping)

    return f"{path_components[0]}{pivot}{subpath_date}/{path_components[1]}"

def collect_track_paths(path_root: str) -> list:
    tracks = []

    for (root, _, files) in os.walk(path_root):
        for f in files:
            tracks.append(f)

        # only care about the files in the root, so bail out
        break

    return tracks


def find_track(path_collection: str, filename: str) -> ET.Element:
    collection = ET.parse(path_collection).getroot().find(XPATH_COLLECTION)

    for node in collection:
        node_filename = node.attrib[ATTR_PATH].split('/')[-1]
        # print(f"node_filename: {node_filename}")
        print(f"{quote(filename)} == {quote(node_filename)}?")
        if quote(filename) == quote(node_filename):
            print(f"search for file '{filename}' matches node {node_filename}")
            return node


def script(path_root: str, path_collection: str) -> None:
    

    for filename in collect_track_paths(path_root)[:2]:
        # find track in collection
        # extract DateAdded attribute
        # construct new full path using helpers
        # move file to the new full path
        print(f"finding track {filename}")
        node = find_track(path_collection, filename)

        if node is None:
            print(f"error: unable to find '{filename}' in collection")
            exit()

# CONSTANTS
ATTR_DATE_ADDED = 'DateAdded'
ATTR_PATH = 'Location'

PATH_LIBRARY_PIVOT = '/ZVP-MUSIC/DJing/'

XPATH_COLLECTION = './/COLLECTION'

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
test_str =\
'''
    <TRACK TrackID="109970693" Name="花と鳥と山" Artist="haircuts for men" Composer="" Album="京都コネクション" Grouping="" Genre="Lounge/Ambient" Kind="AIFF File" Size="84226278" TotalTime="476" DiscNumber="0" TrackNumber="5" Year="2023" AverageBpm="134.00" DateAdded="2023-04-27" BitRate="1411" SampleRate="44100" Comments="8A - 1" PlayCount="1" Rating="0" Location="file://localhost/Volumes/ZVP-MUSIC/DJing/haircuts%20for%20men%20-%20%e8%8a%b1%e3%81%a8%e9%b3%a5%e3%81%a8%e5%b1%b1.aiff" Remixer="" Tonality="8A" Label="" Mix="">
      <TEMPO Inizio="0.126" Bpm="134.00" Metro="4/4" Battito="1" />
    </TRACK>'''
t = ET.fromstring(test_str)
print(t.tag)

t = full_path(t, '/ZVP-MUSIC/DJing/', MAPPING_MONTH)

# print(collect_track_paths(sys.argv[1])[0])
print(quote("Planetary%20Assault%20Systems%20-%20Desert%20Races%20(Or.aiff"))
# print(script(sys.argv[1], sys.argv[2]))
