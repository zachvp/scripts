'''
Uses a combination of audio file metadata to determine duplicates
'''

import os
import argparse
import common_tags
import logging
from typing import Callable

# command support
class Namespace(argparse.Namespace):
    # required
    function: str
    input: str
    
    # optional
    output: str
    comparison: str
    
    # constants
    FUNCTION_LOG_DUPLICATES = 'log_duplicates'
    FUNCTION_WRITE_IDENTIFIERS = 'write_identifiers'
    FUNCTION_WRITE_PATHS = 'write_paths'
    FUNCTION_COMPARE = 'compare'
    FUNCTIONS = {FUNCTION_LOG_DUPLICATES, FUNCTION_WRITE_IDENTIFIERS, FUNCTION_WRITE_PATHS, FUNCTION_COMPARE}

def parse_args(functions: set[str]) -> type[Namespace]:
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"The function to run. One of '{functions}'")
    parser.add_argument('input', type=str, help='The input/source path root.')
    parser.add_argument('--output', '-o', type=str, help='The output file to write to.')
    parser.add_argument('--comparison', '-c', type=str, help='The comparison directory (required for compare).')
    
    args = parser.parse_args(namespace=Namespace)
    args.input = os.path.normpath(args.input)
    if args.output:
        args.output = os.path.normpath(args.output)
    if args.comparison:
        args.comparison = os.path.normpath(args.comparison)
    
    if args.function not in functions:
        parser.error(f"invalid function '{args.function}'; expect one of '{functions}'")
    if args.function == Namespace.FUNCTION_COMPARE and not args.comparison:
        parser.error(f"missing required --comparison argument for '{Namespace.FUNCTION_COMPARE}'")
    
    return args

# primary functions
def log_duplicates(root: str) -> None:
    # script state
    file_set: set[str] = set()

    # script process
    paths = common.collect_paths(root)
    for path in paths:
        # load track tags, check for errors
        tags = common_tags.read_tags(path)
        if not tags:
            continue

        # set item = concatenation of track title & artist
        item = f"{tags.artist}{tags.title}".lower()

        # check for duplicates based on set contents
        # before and after insertion
        count = len(file_set)

        file_set.add(item)
        if len(file_set) == count:
            logging.info(path)

def collect_identifiers(root: str) -> list[str]:
    tracks: list[str] = []

    paths = common.collect_paths(root)
    for path in paths:
        # load track tags, check for errors
        tags = common_tags.read_tags(path)
        if not tags or not tags.artist or not tags.title:
            logging.error(f"incomplete tags: {tags}")
            continue

        # set item = concatenation of track title & artist
        tracks.append(common_tags.basic_identifier(tags.title, tags.artist))
    return tracks

def collect_filenames(root: str) -> list[str]:
    names: list[str] = []

    paths = common.collect_paths(root)
    for path in paths:
        name = os.path.basename(path)
        name = os.path.splitext(name)[0]
        names.append(name)
    return names

# TODO: extend to check for cover art change
def compare_tags(source: str, comparison: str) -> list[str]:
    '''Compares tag metadata between files in source and comparison directories.
    Returns a list of absolute source paths where tags have changed for matching filenames.'''
    # Output data
    changed_paths: list[str] = []
    
    # Use to compare files based on filename, excluding extension
    normalize_filename: Callable[[str], str] = lambda path: os.path.splitext(os.path.basename(path))[0]
    
    # Collect paths and build a mapping for comparison files by normalized filename
    source_paths = common.collect_paths(source)
    comparison_files = {}
    for comp_path in common.collect_paths(comparison):
        base_name = normalize_filename(comp_path)
        comparison_files[base_name] = comp_path
    
    for source_path in source_paths:
        base_name = normalize_filename(source_path)
        if base_name in comparison_files:
            comp_path = comparison_files[base_name]
            
            # Read tags from both files
            source_tags = common_tags.read_tags(source_path)
            comp_tags = common_tags.read_tags(comp_path)
            
            # Skip if tags can't be read from either file
            if not source_tags or not comp_tags:
                logging.info(f"Unable to read tags from '{source_path}' or '{comp_path}'")
                continue
            
            # Compare relevant tags (including genre); add to list if any differ
            if (source_tags.artist != comp_tags.artist or
                source_tags.album != comp_tags.album or
                source_tags.title != comp_tags.title or
                source_tags.genre != comp_tags.genre):
                changed_paths.append(os.path.abspath(source_path))
                logging.info(f"Detected tag difference in '{source_path}'")
                
    return changed_paths

# main
if __name__ == '__main__':
    from . import common
    
    common.configure_log(level=logging.DEBUG, path=__file__)
    args = parse_args(Namespace.FUNCTIONS)
    
    logging.info(f"running function '{args.function}'")
    if args.function == Namespace.FUNCTION_LOG_DUPLICATES:
        log_duplicates(args.input)
    elif args.function == Namespace.FUNCTION_WRITE_IDENTIFIERS:
        identifiers = sorted(collect_identifiers(args.input))
        lines = [f"{id}\n" for id in identifiers]
        with open(args.output, 'w', encoding='utf-8') as file:
            file.writelines(lines)
    elif args.function == Namespace.FUNCTION_WRITE_PATHS:
        paths = collect_filenames(args.input)
        lines = [f"{p}\n" for p in paths]
        lines.sort()
        with open(args.output, 'w', encoding='utf-8') as file:
            file.writelines(lines)
    elif args.function == Namespace.FUNCTION_COMPARE:
        changed = compare_tags(args.input, args.comparison)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as file:
                for path in changed:
                    file.write(f"{path}\n")
        else:
            for path in changed:
                print(path)