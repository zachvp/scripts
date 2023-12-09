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
import process_downloads

def parse_args(valid_functions: set[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"The script function to run. One of: {valid_functions}")
    parser.add_argument('input', type=str, help='The top/root path to scan and organize.')

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)

    if args.function not in valid_functions:
        parser.error(f"invalid function: '{args.function}'")

    return args

def clean_dirname(dirname: str) -> str:
    output = dirname
    replacements: dict[str,str] = {\
    '\\' : '',
     '/' : '&',
     ':' : '',
     '*' : ' ',
     '?' : '',
     '"' : '',
     '<' : '(',
     '>' : ')',
     '|' : ' '
    }

    for key, value in replacements.items():
        if key in output:
            output = output.replace(key, value)

    return output.strip()

def sort_hierarchy(args: argparse.Namespace) -> None:
    # CONSTANTS
    unknown_artist = 'UNKNOWN_ARTIST'
    unknown_album = 'UNKNOWN_ALBUM'

    for working_dir, _, filenames in os.walk(args.input):
        process_downloads.prune(working_dir, [], filenames)

        for filename in filenames:
            filepath = os.path.join(working_dir, filename)

            if os.path.splitext(filename)[1] in {'.aiff', '.aif', '.mp3', '.wav'}:
                tags = find_duplicate_tags.read_tags(filepath)
                if tags:
                    artist = tags.artist if tags.artist else unknown_artist
                    artist_raw = artist
                    artist = clean_dirname(artist)
                    if artist != artist_raw:
                        print(f"info: artist '{artist_raw}' contains at least one illegal character, replacing")
                        artist = clean_dirname(artist)
                        print(f"new artist name: '{artist}'")

                    album = tags.album if tags.album else unknown_album
                    album_raw = album
                    album = clean_dirname(album)

                    if album != album_raw:
                        print(f"info: album '{album}' contains at least one illegal character, replacing")
                        print(f"new album name: '{album}'")

                    parent_path = os.path.join(working_dir, artist, album)
                    output_path = os.path.join(parent_path, filename)

                    if os.path.exists(output_path):
                        print(f"info: skip: output path exists: '{output_path}'")
                        continue
                    if not os.path.exists(parent_path):
                        print(f"info: os.makedirs({parent_path})")
                        os.makedirs(parent_path)
                    print(f"shutil.move{(filepath, output_path)}")
                    shutil.move(filepath, output_path)
            else:
                print(f"info: skip: unsupported file: '{filepath}'")

def validate_hierarchy(args: argparse.Namespace, expected_depth: int) -> None:
    for working_dir, _, filenames in os.walk(args.input):
        for filename in filenames:
            filepath = os.path.join(working_dir, filename)
            print(filepath)
            relpath = os.path.relpath(filepath, start=args.input)
            print(filepath)
            print()
            if len(relpath.split('/')) != expected_depth:
                print(f"info: invalid filepath: {filepath}; depth is: {len(relpath.split('/'))}")
            # if len(os.scandir(working_dir)) todo: finish this check

if __name__ == '__main__':
    FUNCTION_VALIDATE = 'validate'
    FUNCTION_SORT = 'sort'
    script_functions = {FUNCTION_VALIDATE, FUNCTION_SORT}
    script_args = parse_args(script_functions)

    if script_args.function == FUNCTION_VALIDATE:
        validate_hierarchy(script_args, 5)
    elif script_args.function == FUNCTION_SORT:
        sort_hierarchy(script_args)
