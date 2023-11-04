import mutagen
import sys
import os

def get_track_key(track, options):
	for o in options:
		if o in track:
			return o

	return None

# script input
root = sys.argv[1]
artist_keys = ['TPE1', 'TPE2', '©ART', 'Author']
title_keys = ['TIT2', '©nam', 'Title']

# script state
file_set = set()

# script process
for dirpath, dirnames, filenames in os.walk(root):
	for name in filenames:
		# skip hidden files
		if name[0] == '.':
			continue	

		# build full filepath
		path = os.path.join(dirpath, name)

		# load track tags, check for errors
		try:
			track = mutagen.File(path)
		except:
			print(f"error: mutagen exception for {path}")
			continue

		if track is None:
			# print(f"error: unable to read {path}")
			continue

		# pull keys based on what's present in each track
		title_key = get_track_key(track, title_keys)
		artist_key = get_track_key(track, artist_keys)

		# skip 'tracks' that don't contain an
		if title_key not in track or artist_key not in track:
			# print(f'\nskipped: unable to read title for {name}')
			# print(f"track:\n{track}\n")
			continue

		# pull base tag info
		title = track[title_key]
		artist = track[artist_key]

		# some tags are stored as a list
		if type(title) is list:
			title = title[0]
		if type(artist) is list:
			artist = artist[0]

		# set item = concatenation of track title & artist
		item = f"{title}{artist}".lower()

		# check for duplicates based on set contents
		# before and after insertion
		count = len(file_set)

		file_set.add(item)
		if len(file_set) == count:
			print(path)
