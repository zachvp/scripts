# extract info from rekordbox playlist export

'''
Format
	Tab-separated

#	Track Title	BPM	Artist	Genre	Date Added	Time	Key	DJ Play Count
'''

import sys

NUMBER = 0
TITLE = 1
ARTIST = 2
GENRE = 3

def extract(path, fields):
	output = []

	with open(path, 'r') as file:
		lines = file.readlines()

		for i in range(1, len(lines)):
			output_line = ''
			line = lines[i].split('\t')
			for f in fields:
				output_line += f"{line[f]}\t"
			output.append(output_line.strip())
	return output

# main
path = sys.argv[1]

fields = [TITLE, ARTIST]
extracted = extract(path, fields)
print('\n'.join(extracted))
