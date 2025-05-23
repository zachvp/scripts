'''
# Summary
Given an inaccurate Rekordbox collection, constructs a restored collection based on an accurate collection.
The restored collection will contain all tracks from the original inaccurate collection.

The following Track attributes will be corrected:
    - 'DateAdded'
'''

import sys
import xml.etree.ElementTree as ET

# Constants
XPATH_COLLECTION = './/COLLECTION'

ATTR_NAME = 'Name'
ATTR_ARTIST = 'Artist'
ATTR_TOTAL_TIME = 'TotalTime'
ATTR_AVG_BPM = 'AverageBpm'
ATTR_DATE_ADDED = 'DateAdded'

# Helper functions
def generate_id(node: ET.Element) -> str:
    assert node.tag == 'TRACK', f"unexpected element tag: {node.tag}"

    # the id is the concenation of 2 shards
    # shard_0 sources from track name
    # shard_1 sources from track artist, total time, and BPM
    len_0 = min(8, len(node.attrib[ATTR_NAME]))
    len_1 = min(8, len(node.attrib[ATTR_ARTIST]))
    shard_0 = f"{node.attrib[ATTR_NAME][:len_0]}{node.attrib[ATTR_NAME][-len_0:]}"
    shard_1 = f"{node.attrib[ATTR_ARTIST][:len_1]}"
    shard_1 += f"{node.attrib[ATTR_TOTAL_TIME]}{node.attrib[ATTR_AVG_BPM]}"

    # print(f"generated id: {id_str}")
    return f"{shard_0}{shard_1}"

# Primary function
def script(
    path_collection_current: str,
    path_collection_corrected : str,
    path_collection_output: str):

    # data: parsed user input
    tree_incorrect = ET.parse(path_collection_current)
    tree_corrected = ET.parse(path_collection_corrected)

    # data: script state, mutable
    corrected_dates: dict[str, str] = {}

    # associate each track with a unifying 'id' and collect all corrected dates
    collection = tree_corrected.getroot().find(XPATH_COLLECTION)
    assert collection, f"unable to find {XPATH_COLLECTION} for path '{path_collection_corrected}'"
    for node in collection:
        track_id = generate_id(node)

        if track_id in corrected_dates:
            print(f'''\
                WARN: generated duplicate ID for track: {node.attrib[ATTR_NAME]};
                existing: {corrected_dates[track_id]}.
                New entry will overwrite existing entry.''')

        corrected_dates[track_id] = node.attrib[ATTR_DATE_ADDED]

    # find all tracks to correct in the current collection
    collection = tree_corrected.getroot().find(XPATH_COLLECTION)
    assert collection, f"unable to find {XPATH_COLLECTION} for path '{path_collection_current}'"
    for node in collection:
        track_id = generate_id(node)
        if track_id in corrected_dates:
            if node.attrib[ATTR_DATE_ADDED] != corrected_dates[track_id]:
                print(f"correcting track {node.attrib[ATTR_ARTIST]}-{node.attrib[ATTR_NAME]} to use\
                    date {corrected_dates[track_id]}")
                node.attrib[ATTR_DATE_ADDED] = corrected_dates[track_id]

    # write the corrected collection to the specified file
    tree_incorrect.write(
        file_or_filename=path_collection_output,
        encoding='UTF-8',
        xml_declaration=True)

# MAIN
if __name__ == '__main__':
    # user input validation
    if len(sys.argv) != 4:
        ARG_FORMAT =\
        '''
        1: path to incorrectly dated collection
        2: path to the source collection with the correct dates
        3: path to the output location of the corrected collection'''

        print(f"error: incorrect usage, provide exactly 4 arguments with format:{ARG_FORMAT}\n\
            exiting...")
        sys.exit()
    script(sys.argv[1], sys.argv[2], sys.argv[3])
