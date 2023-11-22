'''
This script is rekordbox XML specific.

Given a collection with innaccurate data, this script will construct a restored XML
collection based on another given collection with accurate information.

The following Track attributes will be corrected:
	- 'DateAdded'
'''

import sys
import xml.etree.ElementTree as ET

# HELPERS
def generate_id(node: ET.Element) -> str:
	assert node.tag == 'TRACK', f"unexpected element tag: {node.tag}"

	# the id is the concenation of 2 shards
	# shard_0 sources from track name
	# shard_1 sources from track artist, total time, and BPM
	len_0 = min(8, len(node.attrib[ATTR_NAME]))
	len_1 = min(8, len(node.attrib[ATTR_ARTIST]))
	shard_0 = f"{node.attrib[ATTR_NAME][:len_0]}{node.attrib[ATTR_NAME][-len_0:]}"
	shard_1 = f"{node.attrib[ATTR_ARTIST][:len_1]}{node.attrib[ATTR_TOTAL_TIME]}{node.attrib[ATTR_AVG_BPM]}"

	id_str = f"{shard_0}{shard_1}"
	# print(f"generated id: {id_str}")
	return id_str

# CONSTANTS
XPATH_COLLECTION = './/COLLECTION'

ATTR_NAME = 'Name'
ATTR_ARTIST = 'Artist'
ATTR_TOTAL_TIME = 'TotalTime'
ATTR_AVG_BPM = 'AverageBpm'
ATTR_DATE_ADDED = 'DateAdded'

# MAIN

# user input validation
if len(sys.argv) != 4:
	arg_format =\
	'''
	1: path to incorrectly dated collection
	2: path to the source collection with the correct dates
	3: path to the output location of the corrected collection'''

	print(f"error: incorrect usage, provide exactly 4 arguments with format:{arg_format}\nexiting...")
	exit()

# data: user input
path_collection_current = sys.argv[1]
path_collection_corrected = sys.argv[2]
path_collection_output = sys.argv[3]

# data: parsed user input
tree_incorrect = ET.parse(path_collection_current)
tree_corrected = ET.parse(path_collection_corrected)

# data: script state, mutable
corrected_dates = {}

# associate each track with a unifying 'id' and collect all corrected dates
for node in tree_corrected.getroot().find(XPATH_COLLECTION):
	track_id = generate_id(node)

	if track_id in corrected_dates:
		print(f"WARN: generated duplicate ID for track: {node.attrib[ATTR_NAME]}; existing: {corrected_dates[track_id]}. New entry will overwrite existing entry.")

	corrected_dates[track_id] = node.attrib[ATTR_DATE_ADDED]

# find all tracks to correct in the current collection
for node in tree_incorrect.getroot().find(XPATH_COLLECTION):
	track_id = generate_id(node)
	if track_id in corrected_dates:
		if node.attrib[ATTR_DATE_ADDED] != corrected_dates[track_id]:
			print(f"correcting track {node.attrib[ATTR_ARTIST]}-{node.attrib[ATTR_NAME]} to use date {corrected_dates[track_id]}")
			node.attrib[ATTR_DATE_ADDED] = corrected_dates[track_id]

# write the corrected collection to the specified file
tree_incorrect.write(file_or_filename=path_collection_output, encoding='UTF-8', xml_declaration=True)

