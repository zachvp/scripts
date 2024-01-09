# extract info from rekordbox playlist export

'''
Format
    Tab-separated

#   Track Title BPM Artist  Genre   Date Added  Time    Key DJ Play Count
'''

import argparse
import os

def extract(path, fields) -> list[str]:
    output = []

    with open(path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

        for i in range(1, len(lines)):
            output_line = ''
            line = lines[i].split('\t')
            for f in fields:
                output_line += f"{line[f]}\t"
            output.append(output_line.strip())
    return output

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help="The script input path.")

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)

    return args

def script(args: argparse.Namespace):
    NUMBER = 0
    TITLE = 1
    ARTIST = 2
    GENRE = 3

    fields = [TITLE, ARTIST]
    extracted = extract(args.input, fields)
    print('\n'.join(extracted))

# main
if __name__ == '__main__':
    script(parse_args())
