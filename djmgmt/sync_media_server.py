'''
# Summary
    1. Scans an input directory of date-structured audio files in chronological order.
    2. Transfers each audio file into the output directory, maintaining the
        date and subdirectory structure of the source directory.
      2a. Suspends process when scan switches from one day to another.

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
import logging
from typing import Callable
import subprocess

import common
import constants
import encode_tracks
import subsonic_client

# module setup
common.configure_log(__file__)

# Helper functions
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
    input_paths = sorted(normalize_paths(common.collect_paths(args.input), args.input))

    # Define the date context tracker to determine when a new date context is entered.
    previous_date_context = ''

    # Assign the action based on the given mode.
    action: Callable[[str, str], None] = lambda x, y : print(f"dummy: {x}, {y}")
    if args.mode == MODE_COPY:
        action = shutil.copy
    elif args.mode == MODE_MOVE:
        action = shutil.move
    else:
        print(f"error: unrecognized mode: {args.mode}. Exiting.")
        return

    # Performs the configured action for each input and output path
    # Waits for user input when input path date context changes
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

def sync_from_collection(mappings:list[str]) -> None: # , mapping_action: Callable[[str, str], None], context_action: Callable[[str], Any]
    # process path mapping list
    # perform action for each mapping
    # when path date context changes, call other function, wait for it to finish
    batch: list[str] = []
    previous_source = mappings[0].split(constants.FILE_OPERATION_DELIMITER)[0]
    for mapping in mappings:
        source = mapping.split(constants.FILE_OPERATION_DELIMITER)[0]
        date_context_previous = common.find_date_context(previous_source)
        if date_context_previous == common.find_date_context(source):
            batch.append(mapping)
        else:
            logging.info(f"encoding batch in date context {date_context_previous}:\n{batch}")
            encode_tracks.encode_lossy(batch, '.mp3')
            # todo: upload tracks in output path to server
            subsonic_client.call_endpoint(subsonic_client.API.START_SCAN)
        previous_source = source
    
def parse_args(valid_modes: set[str]) -> argparse.Namespace:
    ''' Returns the parsed command-line arguments.

    Function arguments:
        valid_modes -- defines the supported script modes
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', type=str, help=f"The mode to apply for the function. One of '{valid_modes}'.")
    parser.add_argument('input', type=str, help="The top level directory to search.\
        It's expected to be structured in a year/month/audio.file format.")
    parser.add_argument('output', type=str, help="The output directory to populate.")

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)
    args.output = os.path.normpath(args.output)

    if args.mode not in valid_modes:
        parser.error(f"Invalid mode: '{args.mode}'")

    return args

if __name__ == '__main__':
    # Script modes
    MODE_COPY = 'copy'
    MODE_MOVE = 'move'

    MODES = {MODE_COPY, MODE_MOVE}
    script_args = parse_args(MODES)
    
    input_path = '/Users/zachvp/developer/test-private/data/tracks'
    mappings = common.collect_paths(input_path)
    mappings = common.add_output_path('/Users/zachvp/developer/test-private/data/tracks-output', mappings, input_path)
    sync_from_collection(mappings)
    # sync(script_args)