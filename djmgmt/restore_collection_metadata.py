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

# helpers
def generate_id(node):
	return f"{node.attrib['Name'][:8]}{node.attrib['Name'][-8:]}{node.attrib['Artist'][:4]}{node.attrib['TotalTime']}{node.attrib['AverageBpm']}"

# data: script input
path_collection_current = sys.argv[1]
path_collection_corrected = sys.argv[2]
# todo: adjust arg idx
path_collection_output = sys.argv[3]

# data: XML script state
tree_output = ET.parse(path_collection_current)
tree_corrected = ET.parse(path_collection_corrected)

# data: mutable script state
corrected_dates = {}

# associate each track with a unifying 'id' and collect all corrected dates
for node in tree_corrected.getroot()[1]:
	# todo: fix iteration to go thru the actual 'collection' Element
	# track_id = f"{node.attrib['TotalTime']}{node.attrib['AverageBpm']}"
	track_id = generate_id(node)
	assert track_id not in corrected_dates, f"duplicate ID generated for track: {node.attrib['Name']}; existing: {corrected_dates[track_id]}"
	corrected_dates[track_id] = f"node.attrib['DateAdded'], {node.attrib['Artist']}-{node.attrib['Name']}"

# find all tracks to correct in the current collection
for node in tree_output.getroot()[1]:
	# todo: fix iteration to go thru the actual 'collection' Element
	track_id = generate_id(node)
	if track_id in corrected_dates:
		if node.attrib['DateAdded'] != corrected_dates[track_id]:
			print(f"correcting track {track_id}: {node.attrib['Artist']}-{node.attrib['Name']}")
			node.attrib['DateAdded'] = corrected_dates[track_id]

tree_output.write(file_or_filename=path_collection_output, encoding='UTF-8', xml_declaration=True)

