'''
Uses a combination of audio file metadata to determine duplicates
'''

import os
import argparse
import common_tags
import logging

# command support
class Namespace(argparse.Namespace):
    # required
    function: str
    input: str
    
    # optional
    output: str
    
    # constants
    FUNCTION_LOG_DUPLICATES = 'log_duplicates'
    FUNCTION_WRITE_IDENTIFIERS = 'write_identifiers'
    FUNCTION_WRITE_PATHS = 'write_paths'
    FUNCTIONS = {FUNCTION_LOG_DUPLICATES, FUNCTION_WRITE_IDENTIFIERS, FUNCTION_WRITE_PATHS}

def parse_args(functions: set[str]) -> type[Namespace]:
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"The function to run. One of '{functions}'")
    parser.add_argument('input', type=str, help='The path to the search directory root.')
    parser.add_argument('--output', '-o', type=str, help='The output file to write to.')

    args = parser.parse_args(namespace=Namespace)
    args.input = os.path.normpath(args.input)
    if args.output:
        args.output = os.path.normpath(args.output)
    
    if args.function not in functions:
        parser.error(f"invalid function '{args.function}'; expect one of '{functions}'")
    
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

# main
if __name__ == '__main__':
    import common
    
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
