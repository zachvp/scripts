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
    parser.add_argument('--interactive', '-i', action='store_true', help='Run the script in interactive mode')

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)

    if args.function not in valid_functions:
        parser.error(f"invalid function: '{args.function}'")

    return args

def clean_dirname(dirname: str) -> str:
    '''cleans according to Fat32 specs
    source: https://stackoverflow.com/questions/4814040/allowed-characters-in-filename
    '''
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

def validate_hierarchy(args: argparse.Namespace, expected_depth: int, prune: bool=False) -> None:
    remove_dirs: list[str] = []
    remove_files: list[str] = []

    for working_dir, _, filenames in os.walk(args.input):
        if len(filenames) < 1:
            if prune:
                remove_dirs.append(working_dir)
            print(f"info: invalid: empty directory: {working_dir}")

        for filename in filenames:
            if filename.startswith('.'):
                print(f"info: invalid: illegal prefix: '{filename}'")
                if prune:
                    remove_files.append(filename)
                continue

            # check file path depth
            filepath = os.path.join(working_dir, filename)
            relpath = os.path.relpath(filepath, start=args.input)
            if len(relpath.split('/')) != expected_depth:
                print(f"info: invalid: filepath depth: {filepath}; depth is: {len(relpath.split('/'))}")
                continue

    if args.interactive:
        print(f"remove_dirs: {remove_dirs}")
        print(f"remove_files: {remove_files}")
        choice = input("about to prune, continue? [y/N]")

        if choice != 'y':
            print("info: user quit")
            return

    # prune if necessary
    for directory in remove_dirs:
        try:
            os.removedirs(directory)
        except OSError as e:
            if e.errno == 39:
                print(f"info: skip: will not remove non-empty dir {directory}")
    for file in remove_files:
        os.remove(file)

if __name__ == '__main__':
    FUNCTION_VALIDATE = 'validate'
    FUNCTION_SORT = 'sort'
    FUNCTION_PRUNE = 'prune'
    EXPECTED_DEPTH = 5
    script_functions = {FUNCTION_VALIDATE, FUNCTION_SORT, FUNCTION_PRUNE}
    script_args = parse_args(script_functions)

    print(f"info: running function '{script_args.function}'")

    if script_args.function == FUNCTION_VALIDATE:
        validate_hierarchy(script_args, EXPECTED_DEPTH)
    elif script_args.function == FUNCTION_SORT:
        sort_hierarchy(script_args)
    elif script_args.function == FUNCTION_PRUNE:
        validate_hierarchy(script_args, EXPECTED_DEPTH, True)
