import sys
import xml.etree.ElementTree as ET

'''
Data: source collection (S)
Data: modify collection (M)
Data: output collection (O)

O = M.Copy()

Reads S
	Collects "Date Added" values (D)
	Associates "TotalTime", "BPM" values (V) with D
	Store (D, V) in list (L)

For each item in L
	find v in M
		o.dateAdded = item.dateAdded


'''

# -- HELPERS
def generate_id(node):
	# name shard is first 8 chars and last 8 chars concatenated
	# shard_name_len = node.attrib
	shard_name = f"{node.attrib[ATTR_NAME][:8]}{node.attrib[ATTR_NAME][-8:]}"
	id_str = f"{shard_name}{node.attrib[ATTR_ARTIST][:4]}{node.attrib[ATTR_TOTAL_TIME]}{node.attrib[ATTR_AVG_BPM]}"
	# print(f"generated id: {id_str}")
	return id_str

# CONSTANTS
XPATH_COLLECTION = './/COLLECTION'

ATTR_NAME = 'Name'
ATTR_ARTIST = 'Artist'
ATTR_TOTAL_TIME = 'TotalTime'
ATTR_AVG_BPM = 'AverageBpm'
ATTR_DATE_ADDED = 'DateAdded'

# -- MAIN

# user input validation
if len(sys.argv) != 4:
	arg_format =\
	'''
	1: path to collection you want to correct
	2: path to the source collection with the correct dates
	3: path to the output location of the corrected collection'''

	print(f"error: incorrect usage, provide exactly 4 arguments with format:{arg_format}\nexiting...")
	exit()

# data: user input
path_collection_current = sys.argv[1]
path_collection_corrected = sys.argv[2]
path_collection_output = sys.argv[3]

# data: parsed user input
tree_output = ET.parse(path_collection_current)
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
for node in tree_output.getroot().find(XPATH_COLLECTION):
	track_id = generate_id(node)
	if track_id in corrected_dates:
		if node.attrib[ATTR_DATE_ADDED] != corrected_dates[track_id]:
			print(f"correcting track {node.attrib[ATTR_ARTIST]}-{node.attrib[ATTR_NAME]} to use date {corrected_dates[track_id]}")
			node.attrib[ATTR_DATE_ADDED] = corrected_dates[track_id]

# write the corrected collection to the specified file
tree_output.write(file_or_filename=path_collection_output, encoding='UTF-8', xml_declaration=True)

