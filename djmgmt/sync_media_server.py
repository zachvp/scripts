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

# Constants
FILE_SYNC = 'state/sync_state.txt'
FILE_SYNC_KEY = 'sync_date'

# Classes
class Namespace(argparse.Namespace):
    # Script Arguments
    ## Required
    function: str
    input: str
    output: str
    
    ## Optional
    path_0: str
    
    # Script modes
    FUNCTION_COPY = 'copy'
    FUNCTION_MOVE = 'move'
    FUNCTION_SYNC = 'sync'

    FUNCTIONS = {FUNCTION_COPY, FUNCTION_MOVE, FUNCTION_SYNC}

def parse_args(valid_modes: set[str]) -> type[Namespace]:
    ''' Returns the parsed command-line arguments.

    Function arguments:
        valid_modes -- defines the supported script modes
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"The mode to apply for the function. One of '{valid_modes}'.")
    parser.add_argument('input', type=str, help="The top level directory to search.\
        It's expected to be structured in a year/month/audio.file format.")
    parser.add_argument('output', type=str, help="The output directory to populate.")
    parser.add_argument('--path-0', '-p0', type=str, help="An optional path. Sync uses this as the music root.")

    args = parser.parse_args(namespace=Namespace)
    args.input = os.path.normpath(args.input)
    args.output = os.path.normpath(args.output)

    if args.function not in valid_modes:
        parser.error(f"Invalid mode: '{args.function}'")

    return args

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

def sync_from_path(args: type[Namespace]):
    '''A primary script function.

    Function arguments:
        args -- The parsed command-line arguments.
    '''

    # Collect the sorted input paths relative to the input directory.
    input_paths = sorted(normalize_paths(common.collect_paths(args.input), args.input))

    # Define the date context tracker to determine when a new date context is entered.
    previous_date_context = ''

    # Assign the action based on the given mode.
    action: Callable[[str, str], None] = lambda x, y : print(f"dummy: {x}, {y}")
    if args.function == Namespace.FUNCTION_COPY:
        action = shutil.copy
    elif args.function == Namespace.FUNCTION_MOVE:
        action = shutil.move
    else:
        print(f"error: unrecognized mode: {args.function}. Exiting.")
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
        print(f"info: {args.function}: '{input_path_full}' -> {output_path_full}")

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
        if common.find_date_context(transformed):
            break
    return transformed

def format_timing(timestamp: float) -> str:
    if timestamp > 60:
        hours, remainder = divmod(timestamp, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds:.3f}s"
    return f"{timestamp:.3f}s"
    
def transfer_files(source_path: str, dest_address: str, rsync_module: str) -> tuple[int, str]:
    '''Uses rsync to transfer files using remote daemon.'''
    import subprocess
    import shlex
    
    logging.info(f"transfer from '{source_path}' to '{dest_address}'")
    
    options = "--progress -auvzitR --exclude '.*'"
    command = shlex.split(f"rsync {shlex.quote(source_path)} {dest_address}/{rsync_module} {options}")
    try:
        logging.debug(f'run command: "{shlex.join(command)}"')
        timestamp = time.time()
        process = subprocess.run(command, check=True, capture_output=True, encoding='utf-8')
        timestamp = time.time() - timestamp
        logging.debug(f"time: {format_timing(timestamp)}\n{process.stdout.strip()}")
        return (process.returncode, process.stdout)
    except subprocess.CalledProcessError as error:
        logging.error(f"return code '{error.returncode}':\n{error.stderr.strip()}")
        return (error.returncode, error.stderr)

def sync_batch(batch: list[tuple[str, str]], date_context: str, source: str, dest: str) -> None:
    '''Transfers all files in the batch to the given destination, then tells the music server to perform a scan.'''
    import subsonic_client
    import encode_tracks
    
    # encode the current batch to MP3 format
    logging.debug(f"encoding batch in date context {date_context}:\n{batch}")
    encode_tracks.encode_lossy(batch, '.mp3', threads=28)
    
    # transfer batch to the media server
    transfer_path = transform_implied_path(dest)
    if transfer_path:
        transfer_files(transfer_path, constants.RSYNC_URL, constants.RSYNC_MODULE_NAVIDROME)
        
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
        logging.error(f"empty transfer path: unable to transfer from '{source}' to '{dest}'")

def is_processed(date_context: str, date_context_previous: str) -> bool:
    date_context_processed = ''
    with open(FILE_SYNC, encoding='utf-8', mode='r') as state: # todo: optimize to only open if recent change
        saved_state = state.readline()
        if saved_state:
            date_context_processed = saved_state.split(':')[1].strip()
    if date_context_processed and date_context_processed == date_context:
        if date_context_processed:
            if date_context < date_context_processed:
                logging.info(f"already processed date context: {date_context}")
                return True
            elif date_context_previous < date_context_processed:
                logging.info(f"already processed date context: {date_context_previous}")
                return True
    return False

def sync_from_mappings(mappings:list[tuple[str, str]]) -> None:
    # core data
    batch: list[tuple[str, str]] = []
    source_previous, dest_previous = mappings[0]
    date_context, source, dest = '', '', ''
    index = 0
    
    # helper
    progressFormat: Callable[[int], str] = lambda i: f"{(i / len(mappings) * 100):.2f}%"
    logging.info(f"sync progress: {progressFormat(index)}")
    
    # process the file mappings
    logging.debug(f"sync '{len(mappings)}' mappings:\n{mappings}")
    
    for index, mapping in enumerate(mappings):
        source, dest = mapping
        date_context_previous = common.find_date_context(dest_previous)
        date_context = common.find_date_context(dest)
        
        # validate date contexts        
        if date_context_previous:
            date_context_previous = date_context_previous[0]
        else:
            logging.error(f"no previous date context in path '{dest_previous}'")
            break
        if date_context:
            date_context = date_context[0]
        else:
            logging.error(f"no date context in path '{dest}'")
            break
        
        # skip processed dates
        if is_processed(date_context, date_context_previous):
            continue
        
        # collect each mapping in a given date context
        if date_context_previous == date_context:
            batch.append(mapping)
            logging.debug(f"add to batch: {mapping}")
        else:
            logging.info(f"processing batch in date context '{date_context_previous}'")
            sync_batch(batch, date_context_previous, source_previous, dest_previous)
            batch.clear()
            batch.append(mapping) # add the first mapping of the new context
            
            # persist the processed date context
            with open(FILE_SYNC, encoding='utf-8', mode='w') as state:
                state.write(f"{FILE_SYNC_KEY}: {date_context_previous}")
            logging.debug(f"add to batch: {mapping}")
            logging.info(f"processed batch in date context '{date_context_previous}'")
            logging.info(f"sync progress: {progressFormat(index + 1)}")
        source_previous = source
        dest_previous = dest
    
    # process the final batch
    if batch and date_context and source and dest:
        if isinstance(date_context, tuple):
            date_context = date_context[0]
        logging.info(f"processing batch in date context '{date_context}'")
        sync_batch(batch, date_context, source, dest)
        with open(FILE_SYNC, encoding='utf-8', mode='w') as state:
            state.write(f"{FILE_SYNC_KEY}: {date_context}")
        logging.info(f"processed batch in date context '{date_context}'")
        logging.info(f"sync progress: {progressFormat(index + 1)}")

def key_date_context(mapping: tuple[str, str]) -> str:
    date_context = common.find_date_context(mapping[1])
    return date_context[0] if date_context else ''

if __name__ == '__main__':
    # setup
    common.configure_log(level=logging.DEBUG, filename=__file__)
    script_args = parse_args(Namespace.FUNCTIONS)
    
    logging.info(f"running function '{script_args.function}'")
    if script_args.function in {Namespace.FUNCTION_COPY, Namespace.FUNCTION_MOVE}:
        sync_from_path(script_args)
    else:
        import organize_library_dates as library
        pruned = library.find_node(script_args.input, constants.XPATH_PRUNED)
        collection = library.find_node(script_args.input, constants.XPATH_COLLECTION)
        
        # collect the playlist IDs
        playlist_ids: set[str] = set()
        for track in pruned:
            playlist_ids.add(track.attrib[constants.ATTR_KEY])
        mappings = library.generate_date_paths(collection,
                                               script_args.output,
                                               playlist_ids=playlist_ids,
                                               metadata_path=True,
                                               swap_root_path=script_args.path_0)
        mappings.sort(key=lambda m: key_date_context(m))
    
        timestamp = time.time()
        sync_from_mappings(mappings)
        timestamp = time.time() - timestamp
        logging.info(f"sync time: {format_timing(timestamp)}")
    
    # print(transform_implied_path('/Users/zachvp/developer/test-private/data/tracks-output/2022/04 april/24/1-Gloria_Jones_-_Tainted_Love_(single_version).mp3'))
    # print(date_path_root('/Users/zachvp/developer/test-private/data/tracks-output/2022/04 april/24/1-Gloria_Jones_-_Tainted_Love_(single_version).mp3'))
    # transfer_files(output_path, constants.RSYNC_URL, constants.RSYNC_MODULE_NAVIDROME)
    