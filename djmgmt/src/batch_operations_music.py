'''
Functions to scan and manipulate a batch of music files.
    sweep:           Moves all music files and archives to another directory.
    flatten:         Flattens all files in a given directory, including subdirectories.
    extract:         Extract files from all archives.
    compress:        Zips the contents of a given directory.
    prune:           Removes all empty folders and non-music files from a directory.
    prune_non_music  Removes all non-music files from a directory.
    process:         Convenience function to run sweep, extract, flatten, and all prune functions in sequence for a directory.
    update_library   Processes a directory containing music files into a local library folder, then syncs the updated library.
'''

import argparse
import os
import shutil
import zipfile
import logging

import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote
from typing import cast

from . import constants
from . import common
from . import encode_tracks
from .common_tags import read_tags

# constants
PREFIX_HINTS = {'beatport_tracks', 'juno_download'}
COLLECTION_PATH = os.path.join(constants.PROJECT_ROOT, 'state', 'processed-collection.xml')

# classes
class Namespace(argparse.Namespace):
    # arguments
    ## required
    function : str
    input: str
    output: str
    
    ## optional
    interactive: bool    
    client_mirror_path: str
    
    # primary functions
    FUNCTION_SWEEP = 'sweep'
    FUNCTION_FLATTEN = 'flatten'
    FUNCTION_EXTRACT = 'extract'
    FUNCTION_COMPRESS = 'compress'
    FUNCTION_PRUNE = 'prune'
    FUNCTION_PROCESS = 'process'
    FUNCTION_PRUNE_NON_MUSIC = 'prune_non_music'
    FUNCTION_UPDATE_LIBRARY = 'update_library'
    
    FUNCTIONS_SINGLE_ARG = {FUNCTION_COMPRESS, FUNCTION_FLATTEN, FUNCTION_PRUNE, FUNCTION_PRUNE_NON_MUSIC}
    FUNCTIONS = {FUNCTION_SWEEP, FUNCTION_EXTRACT, FUNCTION_PROCESS, FUNCTION_UPDATE_LIBRARY}.union(FUNCTIONS_SINGLE_ARG)

# Helper functions
# TODO: include function docstring in help summary (-h)
def parse_args(valid_functions: set[str], single_arg_functions: set[str]) -> type[Namespace]:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('function', type=str, help=f"Which script function to run. One of '{valid_functions}'.\
        The following functions only require a single argument: '{single_arg_functions}'.")
    parser.add_argument('input', type=str, help='The input directory to sweep.')
    parser.add_argument('output', nargs='?', type=str, help='The output directory to place the swept tracks.')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run script in interactive mode.')
    parser.add_argument('--client-mirror-path', '-m', type=str, help='The client mirror path to pass to media sync.')

    args = parser.parse_args(namespace=Namespace)

    if args.function not in valid_functions:
        parser.error(f"invalid function '{args.function}'")
    if not args.output and args.function not in single_arg_functions:
        parser.error(f"the 'output' argument is required for function '{args.function}'")
    if args.function == Namespace.FUNCTION_UPDATE_LIBRARY and not args.client_mirror_path:
        parser.error(f"the '--client-mirror-path argument' is required for {Namespace.FUNCTION_UPDATE_LIBRARY}")

    # Normalize path arguments
    args.input = os.path.normpath(args.input)
    if args.client_mirror_path:
        args.client_mirror_path = os.path.normpath(args.client_mirror_path)

    # Handle input and output for single vs. multiple arg functions
    if args.output:
        args.output = os.path.normpath(args.output)
    else:
        args.output = args.input

    return args

def compress_dir(input_path: str, output_path: str):
    with zipfile.ZipFile(output_path + '.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for working_dir, _, names in os.walk(input_path):
            for name in names:
                archive.write(os.path.join(working_dir, name), arcname=name)

def is_prefix_match(value: str, prefixes: set[str]) -> bool:
    for prefix in prefixes:
        if value.startswith(prefix):
            return True
    return False

def prune(working_dir: str, directories: list[str], filenames: list[str]) -> None:
    for index, directory in enumerate(directories):
        if is_prefix_match(directory, {'.', '_'}) or '.app' in directory:
            logging.info(f"prune: hidden directory or '.app' archive '{os.path.join(working_dir, directory)}'")
            del directories[index]
    for index, name in enumerate(filenames):
        if name.startswith('.'):
            logging.info(f"prune: hidden file '{name}'")
            del filenames[index]

def flatten_zip(zip_path: str, extract_path: str) -> None:
    output_directory = os.path.splitext(os.path.basename(zip_path))[0]
    logging.debug(f"output dir: {os.path.join(extract_path, output_directory)}")
    with zipfile.ZipFile(zip_path, 'r') as file:
        file.extractall(os.path.normpath(extract_path))

    unzipped_path = os.path.join(extract_path, output_directory)
    for working_dir, _, filenames in os.walk(unzipped_path):
        for name in filenames:
            logging.debug(f"move from {os.path.join(working_dir, name)} to {extract_path}")
            shutil.move(os.path.join(working_dir, name), extract_path)
    if os.path.exists(unzipped_path) and len(os.listdir(unzipped_path)) < 1:
        logging.info(f"remove empty unzipped path {unzipped_path}")
        shutil.rmtree(unzipped_path)

def is_empty_dir(top: str) -> bool:
    if not os.path.isdir(top):
        return False

    paths = os.listdir(top)
    files = 0
    for path in paths:
        check_path = os.path.join(top, path)
        logging.debug(f"check path: {check_path}")
        if path.startswith('.') or os.path.isdir(check_path):
            files += 1

    logging.debug(f"{files} == {len(paths)}?")
    return files == len(paths)

def get_dirs(top: str) -> list[str]:
    if not os.path.isdir(top):
        return []

    dirs = []
    dir_list = os.listdir(top)
    for item in dir_list:
        path = os.path.join(top, item)
        if os.path.isdir(path):
            dirs.append(path)
    return dirs

def standardize_lossless(source: str, valid_extensions: set[str], prefix_hints: set[str], interactive: bool) -> None:
    from tempfile import TemporaryDirectory
    
    # Create a temporary directory to place the encoded files.
    with TemporaryDirectory() as temp_dir:
        result = encode_tracks.encode_lossless(source, temp_dir, '.aiff', interactive=interactive)
        # Remove all of the original non-standard files that have been encoded.
        for input_path, _ in result:
            os.remove(input_path)
        # Sweep all the encoded files from the temporary directory to the original source directory
        sweep(temp_dir, source, False, valid_extensions, prefix_hints)

# TODO: refactor to use template file as foundation for new file
# TODO: extend to save backup of previous X versions
def record_collection(source: str, collection_path: str) -> ET.ElementTree:
    TAG_TRACK     = 'TRACK'
    TAG_NODE      = 'NODE'
    TAG_PLAYLISTS = 'PLAYLISTS'
    TAG_ROOT      = 'DJ_PLAYLISTS'
    
    NAME_PLAYLIST_ROOT = 'ROOT'
    
    # Create or read the collection path
    if os.path.exists(collection_path):
        try:
            tree = ET.parse(collection_path)
            root = tree.getroot()
            collection = root.find(constants.XPATH_COLLECTION)
            if collection is None:
                raise ValueError('Invalid collection file format: missing COLLECTION element')
        except Exception as e:
            logging.error(f"Error loading collection file: {e}")
            raise
    else:
        # Create a new collection file with the basic structure
        root = ET.Element(TAG_ROOT, {'Version': '1.0.0'})
        product_attrs = {'Name': 'rekordbox', 'Version': '6.8.5', 'Company': 'AlphaTheta'}
        ET.SubElement(root, 'PRODUCT', product_attrs)
        collection = ET.SubElement(root, 'COLLECTION', {'Entries': '0'})
    
    # Ensure PLAYLISTS structure exists with ROOT node child
    playlists = root.find(TAG_PLAYLISTS)
    if playlists is None:
        playlists = ET.SubElement(root, TAG_PLAYLISTS)
    
    # Find or create the ROOT node under PLAYLISTS
    root_node = playlists.find(f"./{TAG_NODE}[@Name=\"{NAME_PLAYLIST_ROOT}\"]")
    
    if root_node is None:
        root_node = ET.SubElement(playlists, TAG_NODE, {
            'Type' : '0',
            'Name' : NAME_PLAYLIST_ROOT,
            'Count': '0'  # Init to 0, update later
        })
    
    # Ensure a default 'CUE Analysis Playlist' exists
    cue_playlist = root_node.find(f"./{TAG_NODE}[@Name=\"CUE Analysis Playlist\"]")
    if cue_playlist is None:
        ET.SubElement(root_node, TAG_NODE, {
            'Name'   : 'CUE Analysis Playlist',
            'Type'   : '1',
            'KeyType': '0',
            'Entries': '0'
        })
    
    # Ensure _pruned playlist exists under ROOT
    pruned_node = root_node.find(f"./{TAG_NODE}[@Name=\"_pruned\"]")
    if pruned_node is None:
        pruned_attrs = {'Name': '_pruned', 'Type': '1', 'KeyType': '0', 'Entries': '0'}
        pruned_node = ET.SubElement(root_node, TAG_NODE, pruned_attrs)
    
    # Count existing tracks
    existing_tracks = len(collection.findall(TAG_TRACK))
    new_tracks = 0
    updated_tracks = 0
    
    # Process all music files in the source directory
    # TODO: refactor to use common.collect_paths
    for working_dir, _, filenames in os.walk(source):
        for name in filenames:
            file_path = os.path.join(working_dir, name)
            name_split = os.path.splitext(name)
            
            # Only process music files
            if name_split[1] in constants.EXTENSIONS:
                file_url = f"file://localhost{quote(file_path, safe='()/')}"
                
                # Check if track already exists
                existing_track = collection.find(f"./{TAG_TRACK}[@Location=\"{file_url}\"]")
                
                tags = read_tags(file_path)
                if not tags:
                    continue
                
                today = datetime.now().strftime('%Y-%m-%d')
                fallback_value = ''
                
                track_attrs = {
                    constants.ATTR_TITLE      : tags.title or fallback_value,
                    constants.ATTR_ARTIST     : tags.artist or fallback_value,
                    constants.ATTR_ALBUM      : tags.album or fallback_value,
                    constants.ATTR_GENRE      : tags.genre or fallback_value,
                    constants.ATTR_KEY        : tags.key or fallback_value,
                    constants.ATTR_PATH       : file_url
                }
                
                if existing_track is not None:
                    # Update existing track with latest metadata
                    track_id = cast(str, existing_track.get(constants.ATTR_TRACK_ID)) 
                    track_attrs[constants.ATTR_TRACK_ID] = track_id
                    # Keep original date added if it exists
                    original_date = existing_track.get(constants.ATTR_DATE_ADDED)
                    if original_date:
                        track_attrs[constants.ATTR_DATE_ADDED] = original_date
                    else:
                        track_attrs[constants.ATTR_DATE_ADDED] = today
                        logging.warning(f"No date present for existing track: '{file_path}', using '{today}'")
                    
                    # Update all attributes
                    for attr_name, attr_value in track_attrs.items():
                        existing_track.set(attr_name, attr_value)
                    
                    updated_tracks += 1
                    logging.debug(f"Updated existing track: '{file_path}'")
                else:
                    # Create new track
                    track_id = str(uuid.uuid4().int)[:9]
                    track_attrs[constants.ATTR_TRACK_ID] = track_id
                    track_attrs[constants.ATTR_DATE_ADDED] = today
                    
                    ET.SubElement(collection, TAG_TRACK, track_attrs)
                    new_tracks += 1
                    logging.debug(f"Added new track: '{file_path}'")
                    
                    # Add to pruned playlist
                    ET.SubElement(pruned_node, TAG_TRACK, {'Key': track_id})
    
    # Update the 'Entries' attributes
    collection.set('Entries', str(existing_tracks + new_tracks))
    pruned_node.set('Entries', str(len(pruned_node.findall(TAG_TRACK))))
    
    # Update ROOT node's Count based on its child nodes
    root_node_children = len(root_node.findall(TAG_NODE))
    root_node.set('Count', str(root_node_children))
    
    # Write the tree to the XML file
    tree = ET.ElementTree(root)
    tree.write(collection_path, encoding='UTF-8', xml_declaration=True)
    logging.info(f"Collection updated: {new_tracks} new tracks, {updated_tracks} updated tracks at {collection_path}")
    
    return tree

# Primary functions
def sweep(source: str, output: str, interactive: bool, valid_extensions: set[str], prefix_hints: set[str]) -> None:
    for working_dir, _, filenames in os.walk(source):
        for name in filenames:
            # loop state
            input_path = os.path.join(working_dir, name)
            output_path = os.path.join(output, name)
            name_split = os.path.splitext(name)

            if os.path.exists(output_path):
                logging.info(f"skip: path '{output_path}' exists in destination")
                continue

            # handle zip archive
            # TODO: refactor so that is_music_archive is its own function
            is_valid_archive = False
            if name_split[1] == '.zip':
                is_valid_archive = True
                
                # inspect zip archive to determine if this is likely a music container
                if not is_prefix_match(name, prefix_hints):
                    valid_files = 0
                    with zipfile.ZipFile(input_path, 'r') as archive:
                        for archive_file in archive.namelist():
                            if not is_valid_archive:
                                logging.debug(f"invalid archive: '{input_path}''")
                                break

                            # ignore archive that contains an app
                            filepath_split = os.path.split(archive_file)
                            for f in filepath_split:
                                if '.app' in os.path.splitext(f)[1]:
                                    logging.info(f"app {archive_file} detected, skipping")
                                    is_valid_archive = False
                                    break
                            
                            # only the given valid extensions and images are allowed
                            file_ext = os.path.splitext(archive_file)[1]
                            if file_ext in valid_extensions:
                                valid_files += 1
                            else:
                                is_valid_archive &= file_ext in {'.jpg', '.png', '.jpeg'}
                    is_valid_archive &= valid_files > 0
                    logging.debug(f"archive '{input_path}' valid = '{is_valid_archive}'")

            # move input file if it has a supported extension or is a valid archive
            if name_split[1] in valid_extensions or is_valid_archive:
                logging.debug(f"filter matched file '{input_path}'")
                if interactive:
                    logging.info(f"move from '{input_path}' to '{output_path}'")
                    choice = input('Continue? [y/N/q]')
                    if choice == 'q':
                        logging.info('user quit')
                        return
                    if choice != 'y' or choice in 'nN':
                        logging.info('skip: user skipped file')
                        continue
                shutil.move(input_path, output_path)
    logging.info("swept all files")
    
def sweep_cli(args: type[Namespace], valid_extensions: set[str], prefix_hints: set[str]) -> None:
    sweep(args.input, args.output, args.interactive, valid_extensions, prefix_hints)

def flatten_hierarchy(source: str, output: str, interactive: bool) -> None:
    for working_dir, _, filenames in os.walk(source):
        for name in filenames:
            input_path = os.path.join(working_dir, name)
            output_path = os.path.join(output, name)
            name_split = os.path.splitext(name)

            # Handle zip files
            if name_split[1] == '.zip':
                logging.info(f"extracting and flattening zip: '{input_path}'")
                if interactive:
                    choice = input('Extract and flatten zip? [y/N/q]')
                    if choice == 'q':
                        logging.info('info: user quit')
                        return
                    if choice != 'y' or choice in 'nN':
                        logging.info(f"skip: {input_path}")
                        continue
                try:
                    flatten_zip(input_path, output)
                except Exception as e:
                    logging.error(f"Error extracting zip '{input_path}': {str(e)}")
                continue

            # Handle regular files
            if not os.path.exists(output_path):
                logging.info(f"move '{input_path}' to '{output_path}'")
                if interactive:
                    choice = input('Continue? [y/N/q]')
                    if choice == 'q':
                        logging.info('info: user quit')
                        return
                    if choice != 'y' or choice in 'nN':
                        logging.info(f"skip: {input_path}")
                        continue
                try:
                    shutil.move(input_path, output_path)
                except FileNotFoundError as error:
                    if error.filename == input_path:
                        logging.info(f"skip: encountered ghost file: '{input_path}'")
                        continue
            else:
                logging.debug(f"skip: {input_path}")

def flatten_hierarchy_cli(args: type[Namespace]) -> None:
    flatten_hierarchy(args.input, args.output, args.interactive)

def extract(source: str, output: str, interactive: bool) -> None:
    for working_dir, _, filenames in os.walk(source):
        for name in filenames:
            input_path = os.path.join(working_dir, name)
            name_split = os.path.splitext(name)
            if name_split[1] == '.zip':
                zip_input_path = os.path.join(working_dir, name)
                zip_output_path = os.path.join(output, name_split[0])

                if os.path.exists(zip_output_path) and os.path.isdir(zip_output_path):
                    logging.info(f"skip: existing ouput path '{zip_output_path}'")
                    continue

                logging.info(f"extract {zip_input_path} to {output}")
                if interactive:
                    choice = input('Continue? [y/N/q]')
                    if choice == 'q':
                        logging.info('user quit')
                        return
                    if choice != 'y' or choice in 'nN':
                        logging.info(f"skip: {input_path}")
                        continue
                with zipfile.ZipFile(zip_input_path, 'r') as file:
                    file.extractall(os.path.normpath(output))
            else:
                logging.debug(f"skip: non-zip file '{input_path}'")

def extract_cli(args: type[Namespace]) -> None:
    extract(args.input, args.output, args.interactive)

def compress_all_cli(args: type[Namespace]) -> None:
    for working_dir, directories, _ in os.walk(args.input):
        for directory in directories:
            compress_dir(os.path.join(working_dir, directory), os.path.join(args.output, directory))

def prune_empty(source: str, interactive: bool) -> None:
    search_dirs : list[str] = []
    pruned : set[str] = set()

    dir_list = get_dirs(source)
    search_dirs.append(source)

    logging.debug(f"prune search_dirs source: '{search_dirs}'")

    while len(search_dirs) > 0:
        search_dir = search_dirs.pop(0)
        if is_empty_dir(search_dir) and search_dir != source:
            pruned.add(search_dir)
        else:
            logging.info(f"search_dir: {search_dir}")

            dir_list = get_dirs(search_dir)
            for d in dir_list:
                search_dirs.append(os.path.join(search_dir, d))

    for path in pruned:
        logging.info(f"will remove: '{path}'")
        if interactive:
            choice = input("continue? [y/N]")
            if choice != 'y':
                logging.info('skip: user skipped')
                continue
        try:
            shutil.rmtree(path)
        except OSError as e:
            if e.errno == 39: # directory not empty
                logging.info(f"skip: non-empty dir {path}")

    logging.info(f"search_dirs, end: {search_dirs}")

def prune_empty_cli(args: type[Namespace]) -> None:
    prune_empty(args.input, args.interactive)
    
def prune_non_music(source: str, valid_extensions: set[str], interactive: bool) -> None:
    '''Removes all files that don't have a valid music extension from the given directory.'''
    for working_dir, _, filenames in os.walk(source):
        for name in filenames:
            input_path = os.path.join(working_dir, name)
            name_split = os.path.splitext(name)
            
            # Check extension
            if name_split[1] not in valid_extensions:
                logging.info(f"non-music file found: '{input_path}'")
                if interactive:
                    choice = input("continue? [y/N]")
                    if choice != 'y':
                        logging.info('skip: user skipped')
                        continue
                try:
                    if name_split[1] == '.app':
                        shutil.rmtree(input_path)
                    else:
                        os.remove(input_path)
                    logging.info(f"removed: '{input_path}'")
                except OSError as e:
                    logging.error(f"Error removing file '{input_path}': {str(e)}")

def prune_non_music_cli(args: type[Namespace], valid_extensions: set[str]) -> None:
    prune_non_music(args.input, valid_extensions, args.interactive)

# TODO: check for missing art
def process(source: str, output: str, interactive: bool, valid_extensions: set[str], prefix_hints: set[str]) -> None:
    '''Performs the following, in sequence:
        1. Sweeps all music files and archives from a source directory into a target directory.
        2. Flattens the files within the target directory.
        3. Standardizes lossless encodings.
        4. Removes all non-music files, archives, and folders in the target directory.
        5. Records the processed files to a Rekordbox-like XML file.
        
        The source and target directories may be the same for effectively in-place processing.
    '''
    sweep(source, output, interactive, valid_extensions, prefix_hints)
    extract(output, output, interactive)
    flatten_hierarchy(output, output, interactive)
    standardize_lossless(output, valid_extensions, prefix_hints, interactive)
    prune_non_music(output, valid_extensions, interactive)
    prune_empty(output, interactive)

def process_cli(args: type[Namespace], valid_extensions: set[str], prefix_hints: set[str]) -> None:
    process(args.input, args.output, args.interactive, valid_extensions, prefix_hints)

def update_library(source: str,
                   library: str,
                   client_mirror_path: str,
                   interactive: bool,
                   valid_extensions: set[str],
                   prefix_hints: set[str]) -> None:
    '''Performs the following, in sequence:
        1. Processes files from source -> temp
        2. Sweeps files from temp -> library
        3. Records the updated library to the XML collection
        4. Syncs files based on the updated XML collection to the given client mirror path
        
        The source, library, and client_mirror_path parameters should all be distinct directories.
    '''
    from . import sync_media_server
    from tempfile import TemporaryDirectory
    
    # Create a temporary directory to process the files from 'source'
    with TemporaryDirectory() as temp_dir:
        process(source, temp_dir, interactive, valid_extensions, prefix_hints)
        sweep(temp_dir, library, interactive, valid_extensions, prefix_hints)
        collection = record_collection(library, COLLECTION_PATH)

        sync_media_server.run_sync_mappings(collection, client_mirror_path, True)

if __name__ == '__main__':
    common.configure_log(path=__file__)

    # parse arguments
    script_args = parse_args(Namespace.FUNCTIONS, Namespace.FUNCTIONS_SINGLE_ARG)
    logging.info(f"will execute: '{script_args.function}'")

    if script_args.function == Namespace.FUNCTION_SWEEP:
        sweep_cli(script_args, constants.EXTENSIONS, PREFIX_HINTS)
    elif script_args.function == Namespace.FUNCTION_FLATTEN:
        flatten_hierarchy_cli(script_args)
    elif script_args.function == Namespace.FUNCTION_EXTRACT:
        extract_cli(script_args)
    elif script_args.function == Namespace.FUNCTION_COMPRESS:
        compress_all_cli(script_args)
    elif script_args.function == Namespace.FUNCTION_PRUNE:
        prune_empty_cli(script_args)
    elif script_args.function == Namespace.FUNCTION_PRUNE_NON_MUSIC:
        prune_non_music_cli(script_args, constants.EXTENSIONS)
    elif script_args.function == Namespace.FUNCTION_PROCESS:
        process_cli(script_args, constants.EXTENSIONS, PREFIX_HINTS)
    elif script_args.function == Namespace.FUNCTION_UPDATE_LIBRARY:
        update_library(script_args.input,
                       script_args.output,
                       script_args.client_mirror_path,
                       script_args.interactive,
                       constants.EXTENSIONS,
                       PREFIX_HINTS)
