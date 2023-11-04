import xml.etree.ElementTree as ET
import sys
from collections import defaultdict

#-- function definitions

# print the tracks present in collection, but not the given playlist
def output_missing_tracks(playlist_ids):
	readout = []

	for track in collection:
		if track.attrib['TrackID'] not in playlist_ids:
			item = f"{track.attrib['Name']}\t{track.attrib['Artist']}"
			readout.append(item)

	for item in readout:
		print(f"{item}")

# print the genre and count for all tracks in the given file
def output_genres_verbose(playlist_ids):
	readout = defaultdict(int)

	# search collection for the file tracks,
	# and gather the relevant data
	for track in collection:
		if track.attrib['TrackID'] in playlist_ids:
			key = track.attrib['Genre']
			readout[key] += 1

	for genre, count in readout.items():
		line = '{}\t{}'.format(genre, count)
		print(line)

def output_genres_short(playlist_ids):
	readout = defaultdict(int)

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
		line = '{}\t{}'.format(genre, count)
		print(line)

def output_genre_category(playlist_ids):
	categories = set()

	for track in collection:
		if track.attrib['TrackID'] in playlist_ids:
			genre_elements = track.attrib['Genre'].split('/')
			for e in genre_elements:
				categories.add(e)

	for c in categories:
		print(c)

def output_renamed_genres(playlist_ids):
	map_data = create_genre_map('data/read/genre-shorthand-mapping.txt')
	genres = set()

	for track in collection:
		if track.attrib['TrackID'] in playlist_ids:
			genre_elements = track.attrib['Genre'].split('/')
			if '' in genre_elements:
				genre_elements.remove('')
			renamed = ['' for __ in range(len(genre_elements))]

			for i, e in enumerate(genre_elements):
				renamed[i] = map_data[e]
				# print(f"{i}: {map_data[e]}")
			genres.add('.'.join(renamed))

	print(genres)

def create_genre_map(path):
	map_data = {}
	validation = set()

	with open(path, 'r') as genre_map:
		lines = genre_map.readlines()
		for line in lines:
			components = line.strip().split('\t')
			if components[0] in map_data:
				print(f'error: duplicate genre element: {components[0]}')
				return None
			# if components[1] in map_data.values:
				# print(f'error: duplicate shorthand: {components[1]}')
			# todo: check for dupes in genre_map values
			map_data[components[0]] = components[1]
			# print(components)
			# print(line)
	# print(map_data)
	for k in map_data:
		if map_data[k] in validation:
			print(f'error: dupe shorthand: {map_data[k]}')
			# return None
		validation.add(map_data[k])

	return map_data

#-- Main
assert len(sys.argv) > 2, 'expected at least 2 args; arg 2: -s, -v, -m, -c, -r'

# user input
path = sys.argv[1]
mode = sys.argv[2]

#-- data: input document
tree = ET.parse(path)
root = tree.getroot()
# todo: fix hard-coding
collection = root[1]
playlists = root[2]
pruned = playlists[0][0][0]

assert pruned.attrib['Name'] == '_pruned', f"unexpected playlist: {pruned.attrib['Name']}"

#-- data: script
playlist_ids = set()

# collect the playlist IDs
for track in pruned:
	playlist_ids.add(track.attrib['Key'])

# call desired function
if mode == '-s':
	output_genres_short(playlist_ids)
elif mode == '-v':
	output_genres_verbose(playlist_ids)
elif mode == '-m':
	output_missing_tracks(playlist_ids)
elif mode == '-c':
	output_genre_category(playlist_ids)
elif mode == '-r':
	output_renamed_genres(playlist_ids)
else:
	print(f"unrecognized mode: {mode}")


