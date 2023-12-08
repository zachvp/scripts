'''
given a top/ dir
    locate each audio file path:
        /top/path/parent/audio.file
    new path:
        /top/path/parent/artist/album/audio.file

'''

import argparse
import os
import shutil
import find_duplicate_tags

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='The top/root path to scan and organize')

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)

    return args

def clean_dirname(dirname: str) -> str:
    output = dirname

    return output.replace('/', '&').replace(':', '')

def sort_hierarchy(args: argparse.Namespace) -> None:
    # CONSTANTS
    unknown_artist = 'UNKNOWN_ARTIST'
    unknown_album = 'UNKNOWN_ALBUM'

    for working_dir, _, filenames in os.walk(args.input):
        for filename in filenames:
            filepath = os.path.join(working_dir, filename)

            if os.path.splitext(filename)[1] in {'.aiff', '.aif', '.mp3', '.wav'}:
                tags = find_duplicate_tags.read_tags(filepath)
                if tags:
                    print(f"tags: {tags.artist}\t{tags.album}\t{tags.title}")
                    artist = tags.artist if tags.artist else unknown_artist
                    artist_raw = artist
                    artist = clean_dirname(artist)
                    if artist != artist_raw:
                        print(f"info: artist '{artist}' contains at least one illegal character, replacing")
                        artist = clean_dirname(artist)
                        print(f"new artist name: {artist}")

                    album = tags.album if tags.album else unknown_album
                    album_raw = album
                    album = clean_dirname(album)

                    if album != album_raw:
                        print(f"info: album '{album}' contains at least one illegal character, replacing")
                        print(f"new album name: {album}")

                    parent_path = os.path.join(working_dir, artist, album)
                    output_path = os.path.join(parent_path, filename)

                    if os.path.exists(output_path):
                        print(f"info: skip: output path exists: '{output_path}'")
                        continue
                    if not os.path.exists(parent_path):
                        # print(f"info: os.makedirs({parent_path})")
                        os.makedirs(parent_path)
                    # print(f"shutil.move{(filepath, output_path)}")
                    shutil.move(filepath, output_path)
            else:
                print(f"info: skip: unsupported file: '{filepath}'")

def validate_hierarchy(args: argparse.Namespace) -> None:
    # todo: confirm no empty dirs
    for working_dir, _, filenames in os.walk(args.input):
        for filename in filenames:
            filepath = os.path.join(working_dir, filename)
            print(filepath)
            relpath = os.path.relpath(filepath, start=args.input)
            print(filepath)
            print()
            if len(relpath.split('/')) != 5:
                print(f"info: invalid filepath: {filepath}; depth is: {len(relpath.split('/'))}")

if __name__ == '__main__':
    script_args = parse_args()

    # sort_hierarchy(script_args)
    validate_hierarchy(script_args)
