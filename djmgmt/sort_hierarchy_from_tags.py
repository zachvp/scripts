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
from datetime import datetime

def parse_args(valid_functions: set[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"The script function to run. One of: {valid_functions}")
    parser.add_argument('input', type=str, help='The top/root path to scan and organize.')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run the script in interactive mode')
    parser.add_argument('--compatibility', '-c', action='store_true', help='Run the script in compatibility mode -\
        Directory names will be cleaned according to permitted FAT32 path characters.')
    parser.add_argument('--date', '-d', action='store_true', help='Place all files in a date-oriented directory structure.')

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)

    if args.function not in valid_functions:
        parser.error(f"invalid function: '{args.function}'")

    return args

def clean_dirname(dirname: str, replacements: dict[str, str]) -> str:
    output = dirname

    for key, value in replacements.items():
        if key in output:
            output = output.replace(key, value)

    return output.strip()

def clean_dirname_fat32(dirname: str) -> str:
    '''cleans according to Fat32 specs
    source: https://stackoverflow.com/questions/4814040/allowed-characters-in-filename
    '''
    replacements: dict[str,str] = {
        '\\' : '()',
        '/'  : '&',
        ':'  : '()',
        '*'  : '()',
        '?'  : '()',
        '"'  : '()',
        '<'  : '(',
        '>'  : ')',
        '|'  : '()',
    }

    return clean_dirname(dirname, replacements)

def clean_dirname_simple(dirname: str) -> str:
    replacements: dict[str,str] = {
        '/'  : '&',
        ':'  : '()',
    }

    return clean_dirname(dirname, replacements)

def date_path() -> str:
    today = datetime.now()
    return f"{today.year}/{today.month}/{today.day}"

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
                    artist = clean_dirname_simple(artist)
                    if args.compatibility:
                        artist = clean_dirname_fat32(artist)
                    if artist != artist_raw:
                        print(f"info: artist '{artist_raw}' contains at least one illegal character, replacing")
                        print(f"new artist name: '{artist}'")

                    album = tags.album if tags.album else unknown_album
                    album_raw = album
                    album = clean_dirname_simple(album)
                    if args.compatibility:
                        album = clean_dirname_fat32(album)
                    if album != album_raw:
                        print(f"info: album '{album_raw}' contains at least one illegal character, replacing")
                        print(f"new album name: '{album}'")

                    parent_path = os.path.join(working_dir, artist, album)
                    if args.date:
                        parent_path = os.path.join(date_path(), parent_path)
                    output_path = os.path.join(parent_path, filename)

                    if os.path.exists(output_path):
                        print(f"info: skip: output path exists: '{output_path}'")
                        continue
                    if args.interactive:
                        choice = input(f"move {filepath} -> {output_path}? [y/N/q]")
                        if choice == 'q':
                            print("info: user quit")
                            return
                        if choice != 'y':
                            print("info: skip: user skipped")
                            continue

                    if not os.path.exists(parent_path):
                        print(f"info: os.makedirs({parent_path})")
                        os.makedirs(parent_path)
                    print(f"shutil.move{(filepath, output_path)}")
                    shutil.move(filepath, output_path)
            else:
                print(f"info: skip: unsupported file: '{filepath}'")

# todo: add function to write invalid paths to file
def validate_hierarchy(args: argparse.Namespace, expected_depth: int) -> list[str]:
    invalid_paths: list[str] = []
    months = {
        'january',
        'february',
        'march',
        'april',
        'may',
        'june',
        'july',
        'august',
        'september',
        'october',
        'november',
        'december',
    }

    for working_dir, dirs, filenames in os.walk(args.input):
        if len(filenames) < 1 and len(dirs) < 1:
            invalid_paths.append(working_dir)
            print(f"info: invalid: empty directory: {working_dir}")

        for filename in filenames:
            filepath = os.path.join(working_dir, filename)
            if filename.startswith('.'):
                print(f"info: invalid: illegal prefix: '{filename}'")
                invalid_paths.append(filepath)
                continue

            # check file path depth
            relpath = os.path.relpath(filepath, start=args.input)
            relpath_split = relpath.split('/')
            if len(relpath_split) != expected_depth:
                print(f"info: invalid: relative filepath depth: {relpath}; relative depth is: {len(relpath.split('/'))}")
                invalid_paths.append(filepath)
                continue

            # example path:
            #  2023/12 december/05/JIGGY (IT)/None/JIGGY (IT) - CAMINANDO (JIGGY (IT) BOOTLEG).aiff; depth is: 6
            index = 0
            if not relpath_split[index].isdecimal() or len(relpath_split[index]) != 4:
                print(f"info: invalid: year path component: '{relpath_split[index]}': expect '4-digit year' format")
                invalid_paths.append(filepath)
                continue
            index += 1

            parts = relpath_split[index].split()
            if len(parts) != 2 or not parts[0].isdecimal() or parts[1] not in months:
                print(f"info: invalid: month path component: '{relpath_split[index]}': expect '<month_index> <month_name>' format")
                invalid_paths.append(filepath)
                continue
            index += 1

            if len(relpath_split[index]) != 2 or not relpath_split[index].isdecimal():
                print(f"info: invalid: day path component: '{relpath_split[index]}': expect '2-digit day' format")
                invalid_paths.append(filepath)
                continue

    return invalid_paths

if __name__ == '__main__':
    FUNCTION_VALIDATE = 'validate'
    FUNCTION_SORT = 'sort'
    EXPECTED_DEPTH = 6
    script_functions = {FUNCTION_VALIDATE, FUNCTION_SORT}
    script_args = parse_args(script_functions)

    print(f"info: running function '{script_args.function}'")

    if script_args.function == FUNCTION_VALIDATE:
        validate_hierarchy(script_args, EXPECTED_DEPTH)
    elif script_args.function == FUNCTION_SORT:
        sort_hierarchy(script_args)
