# extract info from rekordbox playlist export

'''
Format
    Tab-separated
    Fields depend on rekordbox view settings, here is an example line format
        "#   Track Title BPM Artist  Genre   Date Added  Time    Key DJ Play Count"
'''

import argparse
import os
import csv
import sys

def extract_tsv(path: str, fields: list[int]) -> list[str]:
    output = []

    with open(path, 'r', encoding='utf-8') as file:
        rows = file.readlines()
        for row in rows:
            line = row.split('\t')
            output_line = ''
            for f in fields:
                output_line += f"{line[f]}\t"
            output_line = output_line.strip()
            if len(output_line) > 0:
                output.append(output_line)
    return output

def extract_csv(path: str, fields: list[int]) -> list[str]:
    output = []

    with open(path, 'r', encoding='utf-8') as file:
        rows = csv.reader(file)
        for row in rows:
            output_line = ''
            for f in fields:
                output_line += f"{row[f]}\t"
            output_line = output_line.strip()
            if len(output_line) > 0:
                output.append(output_line)
    return output

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Output each track from a rekordbox-exported playlist.\
        If no options are provided, all fields will exist in the ouptut.")
    parser.add_argument('input', type=str, help="The script input path.")
    parser.add_argument('--number', '-n', action='store_true', help="Include the track number in the output.")
    parser.add_argument('--title', '-t', action='store_true', help="Include the title in the output.")
    parser.add_argument('--artist', '-a', action='store_true', help="Include the artist in the output.")
    parser.add_argument('--genre', '-g', action='store_true', help="Include the genre in the output.")

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)

    return args

def script(args: argparse.Namespace):
    number = 0
    title  = 1
    artist = 2
    genre  = 3

    fields: list[int] = []
    if args.number:
        fields.append(number)
    if args.title:
        fields.append(title)
    if args.artist:
        fields.append(artist)
    if args.genre:
        fields.append(genre)

    # if no options are provided, assume all fields for output
    if len(fields) < 1:
        fields = [number, title, artist, genre]

    extension = os.path.splitext(args.input)[1]

    if extension in {'.tsv', '.txt'}:
        extracted = extract_tsv(args.input, fields)
    elif extension == '.csv':
        extracted = extract_csv(args.input, fields)
    else:
        print(f"error: unsupported extension: {extension}")
        sys.exit(1)

    print('\n'.join(extracted))

# main
if __name__ == '__main__':
    script(parse_args())
