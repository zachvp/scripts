'''
given a top/ dir
    locate each audio file path:
        /top/path/parent/audio.file
    new path:
        /top/path/parent/artist/album/audio.file

'''

from datetime import datetime
import argparse
import os
import shutil

import find_duplicate_tags
import process_downloads


def parse_args(valid_functions: set[str]) -> argparse.Namespace:
    '''Returns the parsed command-line arguments.

    valid_functions -- defines the supported script functions
    

    Required command-line arguments:
    function -- the function to run
    input -- the input path context

    Optional command-line arguments:
    interactive -- run the script interactively, requiring user input to execute each operation
    compatibility -- Run the script for FAT32 compatibility mode
    '''

    # define the supported arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"The script function to run. One of: {valid_functions}")
    parser.add_argument('input', type=str, help='The top/root path to scan and organize.')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run the script in interactive mode')
    parser.add_argument('--compatibility', '-c', action='store_true', help='Run the script in compatibility mode -\
        Directory names will be cleaned according to permitted FAT32 path characters.')
    parser.add_argument('--date', '-d', action='store_true', help='Place all files in a date-oriented directory structure.')

    # parse the arguments and clean input
    args = parser.parse_args()
    args.input = os.path.normpath(args.input)

    # check for errors
    if args.function not in valid_functions:
        parser.error(f"invalid function: '{args.function}'")

    return args

def clean_dirname(dirname: str, replacements: dict[str, str]) -> str:
    '''Cleans any dirty substrings in `dirname`.

    Arguments
    dirname -- the directory string to clean
    replacements -- key: dirty string, value: clean string
    '''
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
    '''Cleans reserved directory characters'''
    replacements: dict[str,str] = {
        '/'  : '&',
        ':'  : '()',
    }

    return clean_dirname(dirname, replacements)

def date_path(date: datetime, months: dict[int, str]) -> str:
    '''Returns a directory path that corresponds to today's date. 'YYYY-MM-DD' returns 'YYYY/MM/DD'.
    Example: '2024-01-02' returns 2024/01/02
    '''

    month_index = str(date.month).zfill(2)
    month_name = months[date.month]
    month = f"{month_index} {month_name}"
    day = str(date.day).zfill(2)
    return f"{date.year}/{month}/{day}"

def sort_hierarchy(args: argparse.Namespace, months: dict[int, str]) -> None:
    ''' One of the main script functions. Performs an in-place sort of all music files in the args.input directory
    into a standardized 'Artist/Album/Track_File' directory format.

    If the args.date option is passed, today's date is used to construct the start of the modified path.
    So the full path would be 'Year/Month/Day/Artist/Album/Track_File'
    ''
    '''

    # CONSTANTS - placeholders when the corresponding file metadata is missing
    unknown_artist = 'UNKNOWN_ARTIST'
    unknown_album = 'UNKNOWN_ALBUM'

    # scan the input directory
    for working_dir, _, filenames in os.walk(args.input):
        process_downloads.prune(working_dir, [], filenames)

        # scan all filenames
        for filename in filenames:
            filepath = os.path.join(working_dir, filename)

            # filter for music files
            if os.path.splitext(filename)[1] in {'.aiff', '.aif', '.mp3', '.wav'}:
                # read the artist and album
                tags = find_duplicate_tags.read_tags(filepath)
                if tags:
                    # extract and clean up the artist string
                    artist = tags.artist if tags.artist else unknown_artist
                    artist_raw = artist
                    artist = clean_dirname_simple(artist)
                    if args.compatibility:
                        artist = clean_dirname_fat32(artist)
                    if artist != artist_raw:
                        print(f"info: artist '{artist_raw}' contains at least one illegal character, replacing")
                        print(f"new artist name: '{artist}'")

                    # extract and clean up the album string
                    album = tags.album if tags.album else unknown_album
                    album_raw = album
                    album = clean_dirname_simple(album)
                    if args.compatibility:
                        album = clean_dirname_fat32(album)
                    if album != album_raw:
                        print(f"info: album '{album_raw}' contains at least one illegal character, replacing")
                        print(f"new album name: '{album}'")

                    # build the output path
                    output_path = working_dir

                    # apply the date option if present
                    if args.date:
                        print("apply date folder structure")
                        output_path = os.path.join(output_path, date_path(datetime.now(), months))

                    # define the parent path for the music filename and the full output file path
                    parent_path = os.path.join(output_path, artist, album)
                    output_path = os.path.join(output_path, filename)

                    # skip files that are already in the right place
                    if os.path.exists(output_path):
                        print(f"info: skip: output path exists: '{output_path}'")
                        continue

                    # check for the interactive option
                    if args.interactive:
                        choice = input(f"move {filepath} -> {output_path}? [y/N/q]")
                        if choice == 'q':
                            print("info: user quit")
                            return
                        if choice != 'y':
                            print("info: skip: user skipped")
                            continue

                    # create the music file's parent directory if needed
                    if not os.path.exists(parent_path):
                        print(f"info: os.makedirs({parent_path})")
                        os.makedirs(parent_path)

                    # move the current file to the structured path
                    print(f"shutil.move{(filepath, output_path)}")
                    shutil.move(filepath, output_path)
            else:
                # skip non-music files
                print(f"info: skip: unsupported file: '{filepath}'")

# todo: add function to write invalid paths to file
def validate_hierarchy(args: argparse.Namespace, expected_depth: int, months: set[str]) -> list[str]:
    '''
    One of the main script functions. Validates that all files in the args.input directory
    conform to the expected format.

    Valid path format (relative to music root): '/Year/Month_Index Month_Name/Day/Artist/Album/Music_File'
    '''

    # define the output
    invalid_paths: list[str] = []

    # scan all files in the input directory
    for working_dir, dirs, filenames in os.walk(args.input):
        if len(filenames) < 1 and len(dirs) < 1:
            # empty directories are invalid
            invalid_paths.append(working_dir)
            print(f"info: invalid: empty directory: {working_dir}")

        # scan all files
        for filename in filenames:
            # define full path
            filepath = os.path.join(working_dir, filename)

            # check for invalid hidden files
            if filename.startswith('.'):
                print(f"info: invalid: illegal prefix: '{filename}'")
                invalid_paths.append(filepath)
                continue

            # validate file path depth
            relpath = os.path.relpath(filepath, start=args.input)
            relpath_split = relpath.split('/')
            if len(relpath_split) != expected_depth:
                print(f"info: invalid: relative filepath depth: {relpath}; relative depth is: {len(relpath.split('/'))}")
                invalid_paths.append(filepath)
                continue

            # validate the path's year format
            index = 0
            if not relpath_split[index].isdecimal() or len(relpath_split[index]) != 4:
                print(f"info: invalid: year path component: '{relpath_split[index]}': expect '4-digit year' format")
                invalid_paths.append(filepath)
                continue
            index = 1

            # validate the path's month format
            parts = relpath_split[index].split()
            if len(parts) != 2 or not parts[0].isdecimal() or parts[1] not in months:
                print(f"info: invalid: month path component: '{relpath_split[index]}': expect '<month_index> <month_name>' format")
                invalid_paths.append(filepath)
                continue
            index = 2

            # validate the path's day format
            if len(relpath_split[index]) != 2 or not relpath_split[index].isdecimal():
                print(f"info: invalid: day path component: '{relpath_split[index]}': expect '2-digit day' format")
                invalid_paths.append(filepath)
                continue

    return invalid_paths

if __name__ == '__main__':
    # constants
    FUNCTION_VALIDATE = 'validate'
    FUNCTION_SORT = 'sort'
    EXPECTED_DEPTH = 6

    MAPPING_MONTH = {
        1  : 'january',
        2  : 'february',
        3  : 'march',
        4  : 'april',
        5  : 'may',
        6  : 'june',
        7  : 'july',
        8  : 'august',
        9  : 'september',
        10 : 'october',
        11 : 'november',
        12 : 'december',
    }

    # script arguments
    script_functions = {FUNCTION_VALIDATE, FUNCTION_SORT}
    script_args = parse_args(script_functions)

    print(f"info: running function '{script_args.function}'")

    # run the given script function
    if script_args.function == FUNCTION_VALIDATE:
        validate_hierarchy(script_args, EXPECTED_DEPTH, set(MAPPING_MONTH.values()))
    elif script_args.function == FUNCTION_SORT:
        sort_hierarchy(script_args, set(MAPPING_MONTH.values()))
