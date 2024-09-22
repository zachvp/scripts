'''
Script steps
    1. Scans an input directory of date-structured audio files in chronological order.
    2. Transfers each audio file into the output directory, maintaining the
        date and subdirectory structure of the source directory.

Usage:
    `populate_media_server.py -h`

Definitions
    date-structured directory:
        /year/month/day/** (e.g. /2020/january/01/artist/album/audio.file)
    year:       4-digit positive int (e.g. 2023)
    month:      english month name (e.g. january)
    day:        2-digit positive int (e.g 05)
    audio.file: must be an audio file type
'''

import argparse
import os
import shutil
from typing import Callable

# Script modes
SCRIPT_MODE_COPY = 'copy'
SCRIPT_MODE_MOVE = 'move'

SCRIPT_MODES = {SCRIPT_MODE_COPY, SCRIPT_MODE_MOVE}

def parse_args(valid_modes: set[str]) -> argparse.Namespace:
    ''' Returns the parsed command-line arguments.

    Function arguments:
        valid_modes -- defines the supported script modes
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', type=str, help=f"The mode to run the script. One of '{valid_modes}'.")
    parser.add_argument('input', type=str, help="The top level directory to search.\
        It's expected to be structured in a year/month/audio.file format.")
    parser.add_argument('output', type=str, help="The output directory to populate.")

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)
    args.output = os.path.normpath(args.output)

    if args.mode not in valid_modes:
        parser.error(f"Invalid mode: '{args.mode}'")

    return args

def enumerate_paths(top: str) -> list[str]:
    '''Returns a collection with the full paths of all relevant files in the given directory.

    Function arguments:
        top -- The input directory to scan.
    '''
    paths: list[str] = []
    for working_dir, _, filenames in os.walk(top):
        for name in filenames:
            if not name.startswith('.'):
                paths.append(os.path.join(working_dir, name))
    return paths

def normalize_paths(paths: list[str], parent: str) -> list[str]:
    '''Returns a collection with the given paths transformed to be relative to the given parent directory.

    Function arguments:
        paths  -- The full paths to transform.
        parent -- The directory that the full paths should be relative to.

    Example:
        path: /full/path/to/file, parent: /full/path -> to/file
    '''
    normalized: list[str] = []
    for path in paths:
        normalized.append(os.path.relpath(path, start=parent))
    return normalized

def sync(args: argparse.Namespace):
    '''The main script function.

    Function arguments:
        args -- The parsed command-line arguments.
    '''

    # Collect the sorted input paths relative to the input directory.
    input_paths = sorted(normalize_paths(enumerate_paths(args.input), args.input))

    # Define the date context tracker to determine when a new date context is entered.
    previous_date_context = ''

    # Assign the action based on the given mode.
    action: Callable[[str, str], None] = lambda x, y : print(f"dummy: {x}, {y}")
    if args.mode == SCRIPT_MODE_COPY:
        action = shutil.copy
    elif args.mode == SCRIPT_MODE_MOVE:
        action = shutil.move
    else:
        print(f"error: unrecognized mode: {args.mode}. Exiting.")
        return

    for path in input_paths:
        # Skip any existing valid output paths.
        output_path_full = os.path.join(args.output, path)
        if os.path.exists(output_path_full):
            print(f"info: skip: output path exists: '{output_path_full}'")
            continue
        input_path_full = os.path.join(args.input, path)
        print(f"info: {args.mode}: '{input_path_full}' -> {output_path_full}")

        # Notify the user if the current date context is different from the previous date context,
        date_context = '/'.join(os.path.split(path)[:3]) # format: 'year/month/day'
        if len(previous_date_context) > 0 and previous_date_context != date_context:
            choice = input(f"info: date context changed from '{previous_date_context}' to '{date_context}' continue? [y/N]")
            if choice != 'y':
                print('info: user quit')
                return
        previous_date_context = date_context

        # Copy or move the input file to the output path, creating the output directories if needed.
        output_parent_path = os.path.split(output_path_full)[0]
        if not os.path.exists(output_parent_path):
            os.makedirs(output_parent_path)
        action(input_path_full, output_path_full)

if __name__ == '__main__':
    script_args = parse_args(SCRIPT_MODES)
    sync(script_args)
