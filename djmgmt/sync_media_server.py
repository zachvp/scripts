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
import time

import common
import constants

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

def sync_from_path(args: argparse.Namespace):
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

def transform_implied_path(path: str) -> str | None:
    '''Rsync-specific. Transforms the given path into a format that will include the required subdirectories.'''
    # input : /Users/zachvp/developer/test-private/data/tracks-output/2022/04 april/24/1-Gloria_Jones_-_Tainted_Love_(single_version).mp3
    # output: /Users/zachvp/developer/test-private/data/tracks-output/./2022/04 april/24/
    components = path.split(os.sep)[1:]
    if not common.find_date_context(path):
        return None
    transformed = ''
    for i, c in enumerate(components):
        if len(c) == 4 and c.isdecimal() and components[i+1].split()[1] in constants.MAPPING_MONTH.values():
            transformed += f"{os.sep}."
        transformed += f"{os.sep}{c}"
    return transformed

def format_timing(timestamp: float) -> str:
    if timestamp > 60:
        hours, remainder = divmod(timestamp, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds:.3}s"
    return f"{timestamp:.3}s"
    
def transfer_files(source_path: str, dest_address: str, rsync_module: str) -> None:
    import subprocess
    import shlex
    
    options = "--progress -auvziR --exclude '.*'"
    command = shlex.split(f"rsync \"{source_path}\" {dest_address}/{rsync_module} {options}") # todo: use shlex.quote()
    try:
        logging.debug(f'run command: "{shlex.join(command)}"')
        timestamp = time.time()
        process = subprocess.run(command, check=True, capture_output=True, encoding='utf-8')
        timestamp = time.time() - timestamp
        logging.debug(f"total time: {format_timing(timestamp)}\n{process.stdout.strip()}")
    except subprocess.CalledProcessError as error:
        logging.error(f"return code '{error.returncode}':\n{error.stderr.strip()}")

def sync_batch(batch: list[str], date_context: str, source: str, dest: str) -> None:
    '''Transfers all files in the batch to the given destination, then tells the music server to perform a scan.'''
    import subsonic_client
    import encode_tracks
    
    # encode the current batch to MP3 format
    logging.debug(f"encoding batch in date context {date_context}:\n{batch}")
    encode_tracks.encode_lossy(batch, '.mp3')
    
    transfer_path = transform_implied_path(dest)
    if transfer_path:        
        # transfer files to media server
        transfer_files(os.path.dirname(transfer_path), f"{constants.RSYNC_URL}", constants.RSYNC_MODULE_NAVIDROME)
        
        # tell the media server new files are available
        response = subsonic_client.call_endpoint(subsonic_client.API.START_SCAN, {'fullScan': 'true'})
        if response.ok:
            # wait until the server has stopped scanning
            while True:
                response = subsonic_client.call_endpoint(subsonic_client.API.GET_SCAN_STATUS)
                content = subsonic_client.handle_response(response, subsonic_client.API.GET_SCAN_STATUS)
                if not content or content['scanning'] == 'false':
                    break
                logging.debug("scan in progress, waiting...")
                time.sleep(1)

    else:
        logging.error(f"unable to transfer from '{source}' to '{dest}'")

def sync_from_mappings(mappings:list[str]) -> None:
    batch: list[str] = []
    source_previous, dest_previous = mappings[0].split(constants.FILE_OPERATION_DELIMITER)
    date_context, source, dest = '', '', ''
    
    # process the file mappings
    logging.debug(f"mappings:\n{mappings}")
    for mapping in mappings:
        source, dest = mapping.split(constants.FILE_OPERATION_DELIMITER)
        date_context_previous = common.find_date_context(source_previous)
        date_context = common.find_date_context(source)
        
        # validate date contexts
        if not date_context_previous:
            logging.error(f"no previous date context in path '{date_context_previous}'")
            break
        if not date_context:
            logging.error(f"no date context in path '{date_context}'")
            break
        
        # collect each mapping in a given date context
        if date_context_previous == date_context:
            batch.append(mapping)
            logging.debug(f"add to batch: {mapping}")
        else:
            logging.info(f"processing batch in date context '{date_context_previous}'")
            sync_batch(batch, date_context_previous, source_previous, dest_previous)
            batch.clear()
            batch.append(mapping) # add the first mapping of the new context
            logging.debug(f"add to batch: {mapping}")
            logging.info(f"processed batch in date context '{date_context_previous}'")
        source_previous = source
        dest_previous = dest
    
    # process the final batch
    if batch and date_context and source and dest:
        sync_batch(batch, date_context, source, dest)
        logging.info(f"processed batch in date context '{date_context}'")

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
    # setup
    common.configure_log(level=logging.INFO)
    
    # Script modes
    MODE_COPY = 'copy'
    MODE_MOVE = 'move'

    MODES = {MODE_COPY, MODE_MOVE}
    # script_args = parse_args(MODES)
    
    input_path = '/Users/zachvp/developer/test-private/data/tracks'
    output_path = '/Users/zachvp/developer/test-private/data/tracks-output/'
    mappings = common.collect_paths(input_path)
    mappings = common.add_output_path(output_path, mappings, input_path)
    mappings.sort()
    
    timestamp = time.time()
    sync_from_mappings(mappings)
    timestamp = time.time() - timestamp
    logging.info(f"sync time: {format_timing(timestamp)}")
    
    # print(transform_implied_path('/Users/zachvp/developer/test-private/data/tracks-output/2022/04 april/24/1-Gloria_Jones_-_Tainted_Love_(single_version).mp3'))
    # print(date_path_root('/Users/zachvp/developer/test-private/data/tracks-output/2022/04 april/24/1-Gloria_Jones_-_Tainted_Love_(single_version).mp3'))
    # transfer_files(output_path, constants.RSYNC_URL, constants.RSYNC_MODULE_NAVIDROME)
    # sync(script_args)