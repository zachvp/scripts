'''
Functions to scan and manipulate a batch of music files.
    sweep:    Moves all music files and archives to another directory.
    flatten:  Flattens all files in a given directory, including subdirectories.
    extract:  Extract files from all archives.
    compress: Zips the contents of a given directory.
    prune:    Removes all empty folders and non-music files from a directory.
    process:  Convenience function to run sweep, extract, flatten in sequence for a directory.
'''

# todo: properly document

import argparse
import os
import shutil
import zipfile
import logging

import common

# constants
EXTENSIONS = {'.mp3', '.wav', '.aif', '.aiff', 'flac'}
PREFIX_HINTS = {'beatport_tracks', 'juno_download'}

# classes
class Namespace(argparse.Namespace):
    # arguments
    function : str
    input: str
    output: str
    interactive: bool
    
    # functions
    FUNCTION_SWEEP = 'sweep'
    FUNCTION_FLATTEN = 'flatten'
    FUNCTION_EXTRACT = 'extract'
    FUNCTION_COMPRESS = 'compress'
    FUNCTION_PRUNE = 'prune'
    FUNCTION_PROCESS = 'process'
    
    FUNCTIONS_SINGLE_ARG = {FUNCTION_COMPRESS, FUNCTION_FLATTEN, FUNCTION_PRUNE}
    FUNCTIONS = {FUNCTION_SWEEP, FUNCTION_EXTRACT, FUNCTION_PROCESS}.union(FUNCTIONS_SINGLE_ARG)

# Helper functions
def parse_args(valid_functions: set[str], single_arg_functions: set[str]) -> type[Namespace]:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('function', type=str, help=f"Which script function to run. One of '{valid_functions}'.\
        The following functions only require a single argument: '{single_arg_functions}'.")
    parser.add_argument('input', type=str, help='The input directory to sweep.')
    parser.add_argument('output', nargs='?', type=str, help='The output directory to place the swept tracks.')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run script in interactive mode')

    args = parser.parse_args(namespace=Namespace)

    if args.function not in valid_functions:
        parser.error(f"invalid function '{args.function}'")
    if not args.output and args.function not in single_arg_functions:
        parser.error(f"the 'output' parameter is required for function '{args.function}'")

    args.input = os.path.normpath(args.input)

    if args.output:
        args.output = os.path.normpath(args.output)
    else:
        args.output = os.path.normpath(args.input)

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

def prune(working_dir: str, directories: list[str], filenames: list[str]) -> None:
    for index, directory in enumerate(directories):
        if is_prefix_match(directory, {'.', '_'}) or '.app' in directory:
            logging.info(f"prune: hidden directory or '.app' archive '{os.path.join(working_dir, directory)}'")
            del directories[index]
    for index, name in enumerate(filenames):
        if name.startswith('.'):
            logging.info(f"prune: hidden file '{name}'")
            del filenames[index]

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
                logging.info(f"filter matched file '{input_path}'")
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
                logging.info(f"skip: {input_path}")

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
                logging.info(f"skip: non-zip file '{input_path}'")

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
    
def process_cli(args: type[Namespace], valid_extensions: set[str], prefix_hints: set[str]) -> None:
    sweep(args.input, args.output, args.interactive, valid_extensions, prefix_hints)
    extract(args.output, args.output, args.interactive)
    flatten_hierarchy(args.output, args.output, args.interactive)
    prune_empty(args.output, args.interactive)

# TODO: add function to remove all non-music files

if __name__ == '__main__':
    common.configure_log(path=__file__)

    # parse arguments
    script_args = parse_args(Namespace.FUNCTIONS, Namespace.FUNCTIONS_SINGLE_ARG)
    logging.info(f"will execute: '{script_args.function}'")

    if script_args.function == Namespace.FUNCTION_SWEEP:
        sweep_cli(script_args, EXTENSIONS, PREFIX_HINTS)
    elif script_args.function == Namespace.FUNCTION_FLATTEN:
        flatten_hierarchy_cli(script_args)
    elif script_args.function == Namespace.FUNCTION_EXTRACT:
        extract_cli(script_args)
    elif script_args.function == Namespace.FUNCTION_COMPRESS:
        compress_all_cli(script_args)
    elif script_args.function == Namespace.FUNCTION_PRUNE:
        prune_empty_cli(script_args)
    elif script_args.function == Namespace.FUNCTION_PROCESS:
        process_cli(script_args, EXTENSIONS, PREFIX_HINTS)
