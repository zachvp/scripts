'''
given a top/ dir
    locate each audio file path:
        /top/path/parent/audio.file
    new path:
        /top/path/parent/artist/album/audio.file

'''

import argparse
import os
import find_duplicate_tags

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='The top/root path to scan and organize')

    script_args = parser.parse_args()
    script_args.input = os.path.normpath(script_args.input)

    for working_dir, directories, filenames in os.walk(script_args.input):
        # todo: prune dirs, files
        for filename in filenames:
            filepath = os.path.join(working_dir, filename)

            if os.path.splitext(filename)[1] in {'.aiff', '.aif', '.mp3', '.wav'}:
                tags = find_duplicate_tags.read_tags(filepath)
                if tags:
                    print(f"tags: {tags.artist}\t{tags.album}\t{tags.title}")
            else:
                print(f"info: skip: unsupported file: '{filepath}'")
