'''
goal: sweep downloads folder for music files

procedure
    F: filter source directory for eligible files, directories, or archives
    C: copy F.contents into destination directory
bonus
    + flatten C in destination directory
'''

# -- TODO
#   Store processed files in DB
#   Peek into zip: confirm contains music file; check against processed files

import argparse
import os
import shutil
import zipfile

# todo: record each function's processing list (e.g. list of files extracted or swept)

def compress_dir(input_path: str, output_path: str):
    with zipfile.ZipFile(output_path + '.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for working_dir, _, names in os.walk(input_path):
            for name in names:
                archive.write(os.path.join(working_dir, name), arcname=name)

def compress_all(args: argparse.Namespace) -> None:
    for working_dir, directories, _ in os.walk(args.input):
        for directory in directories:
            # print(f"dbg: {os.path.join(working_dir, directory), os.path.join(args.output, directory)}")
            compress_dir(os.path.join(working_dir, directory), os.path.join(args.output, directory))

def flatten_zip(zip_path: str, extract_path: str) -> None:
    print(f"output dir: {os.path.join(extract_path, os.path.splitext(os.path.basename(zip_path))[0])}")
    with zipfile.ZipFile(zip_path, 'r') as file:
        file.extractall(os.path.normpath(extract_path))

    unzipped_path = os.path.join(extract_path, os.path.splitext(os.path.basename(zip_path))[0])
    for working_dir, _, filenames in os.walk(unzipped_path):
        for name in filenames:
            print(f"move from {os.path.join(working_dir, name)} to {extract_path}")
            shutil.move(os.path.join(working_dir, name), extract_path)
    if os.path.exists(unzipped_path) and len(os.listdir(unzipped_path)) < 1:
        print(f"info: remove empty unzipped path {unzipped_path}")
        shutil.rmtree(unzipped_path)

def extract(args: argparse.Namespace) -> None:
    for working_dir, directories, filenames in os.walk(args.input):
        prune(working_dir, directories, filenames)

        for name in filenames:
            input_path = os.path.join(working_dir, name)
            name_split = os.path.splitext(name)
            if name_split[1] == '.zip':
                zip_input_path = os.path.join(working_dir, name)
                zip_output_path = os.path.join(args.output, name_split[0])

                if os.path.exists(zip_output_path) and os.path.isdir(zip_output_path):
                    print(f"info: skip: existing ouput path '{zip_output_path}'")
                    continue

                print(f"info: extract {zip_input_path} to {args.output}")
                if args.interactive:
                    choice = input('Continue? [y/N/q]')
                    if choice == 'q':
                        print('info: user quit')
                        return
                    if choice != 'y' or choice in 'nN':
                        print(f"info: skip: {input_path}")
                        continue
                # flatten_zip(os.path.join(working_dir, name), args.output)
                with zipfile.ZipFile(zip_input_path, 'r') as file:
                    file.extractall(os.path.normpath(args.output))
            else:
                print(f"info: skip: non-zip file '{input_path}'")

def flatten_hierarchy(args: argparse.Namespace) -> None:
    for working_dir, directories, filenames in os.walk(args.input):
        prune(working_dir, directories, filenames)

        for name in filenames:
            input_path = os.path.join(working_dir, name)
            output_path = os.path.join(args.output, name)

            if not os.path.exists(output_path):
                print(f"move '{input_path}' to '{output_path}'")
                if args.interactive:
                    choice = input('Continue? [y/N/q]')
                    if choice == 'q':
                        print('info: user quit')
                        return
                    if choice != 'y' or choice in 'nN':
                        print(f"info: skip: {input_path}")
                        continue
                try:
                    shutil.move(input_path, output_path)
                except FileNotFoundError as error:
                    if error.filename == input_path:
                        print(f"info: skip: encountered ghost file: '{input_path}'")
                        continue

            else:
                print(f"info: skip: {input_path}")

def is_prefix_match(value: str, prefixes: set[str]) -> bool:
    for prefix in prefixes:
        if value.startswith(prefix):
            return True
    return False

def prune(working_dir: str, directories: list[str], filenames: list[str]) -> None:
    for index, directory in enumerate(directories):
        if is_prefix_match(directory, {'.', '_'}) or '.app' in directory:
            print(f"info: skip: hidden directory or '.app' archive '{os.path.join(working_dir, directory)}'")
            del directories[index]
    for index, name in enumerate(filenames):
        if name.startswith('.'):
            print(f"info: skip: hidden file '{name}'")
            del filenames[index]

def sweep(args: argparse.Namespace, valid_extensions: set[str], prefix_hints: set[str]) -> None:
    for working_dir, directories, filenames in os.walk(args.input):
        prune(working_dir, directories, filenames)

        for name in filenames:
            input_path = os.path.join(working_dir, name)
            output_path = os.path.join(args.output, name)
            name_split = os.path.splitext(name)

            if os.path.exists(output_path):
                print(f"info: skip: path '{output_path}' exists in destination")
                continue

            is_valid_archive = False
            if name_split[1] == '.zip':
                if is_prefix_match(name, prefix_hints):
                    is_valid_archive = True
                else:
                    with zipfile.ZipFile(input_path) as archive:
                        for archive_file in archive.namelist():
                            is_valid_archive |= os.path.splitext(archive_file)[1] in valid_extensions
                            if is_valid_archive:
                                break

            if name_split[1] in valid_extensions or is_valid_archive:
                print(f"info: filter matched file '{input_path}'")
                if args.interactive:
                    print(f"info: move from '{input_path}' to '{output_path}'")
                    choice = input('Continue? [y/N/q]')
                    if choice == 'q':
                        print('info: user quit')
                        return
                    if choice != 'y' or choice in 'nN':
                        print('info: skip: user skipped file')
                        continue
                shutil.move(input_path, output_path)
    print("swept all files")

def find_root_year(path: str) -> str:
    parts : list[str] = path.split('/')
    for i, part in enumerate(parts):
        if part.isdecimal():
            return '/'.join(parts[:i+1])
    return ''

def is_empty_dir(top: str) -> bool:
    if not os.path.isdir(top):
        return False

    paths = os.listdir(top)
    files = 0
    for path in paths:
        print(f"listed path: {path}")
        if path.startswith('.') or os.path.isdir(os.path.join(top, path)):
            files += 1

    print(f"{files} == {len(paths)}")
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


def prune_empty(args: argparse.Namespace) -> None:
    pruned : set[str] = set()

    for working_dir, dirnames, _ in os.walk(args.input):
        for dirname in dirnames:
            path = os.path.join(working_dir, dirname)
            print(f"os.path.join({working_dir}, {dirname})")
            path_root = find_root_year(path)
            if path_root not in pruned and is_empty_dir(path) and len(path_root.strip()) > 0:
                pruned.add(path_root)

    print(f"pruned: {pruned}")
    for path in pruned:
        print(f"info: will remove: '{path}'")
        if args.interactive:
            choice = input("continue? [y/N]")
            if choice != 'y':
                print('info: skip: user skipped')
                continue
        try:
            shutil.rmtree(path)
        except OSError as e:
            if e.errno == 39: # error: directory not empty
                print(f"info: skip: non-empty dir {path}")

def parse_args(valid_functions: set[str], single_arg_functions: set[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"Which script function to run. One of '{valid_functions}'.\
        The following functions only require a single argument: '{single_arg_functions}'.")
    parser.add_argument('input', type=str, help='The input directory to sweep.')
    parser.add_argument('output', nargs='?', type=str, help='The output directory to place the swept tracks.')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run script in interactive mode')

    args = parser.parse_args()

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

if __name__ == '__main__':
    # CONSTANTS
    FUNCTION_SWEEP = 'sweep'
    FUNCTION_FLATTEN = 'flatten'
    FUNCTION_EXTRACT = 'extract'
    FUNCTION_COMPRESS = 'compress'
    FUNCTION_PRUNE = 'prune'
    FUNCTIONS_SINGLE_ARG = {FUNCTION_COMPRESS, FUNCTION_FLATTEN, FUNCTION_PRUNE}
    FUNCTIONS = {FUNCTION_FLATTEN, FUNCTION_SWEEP, FUNCTION_EXTRACT}.union((FUNCTIONS_SINGLE_ARG))
    EXTENSIONS = {'.mp3', '.wav', '.aif', '.aiff', 'flac'}
    PREFIX_HINTS = {'beatport_tracks', 'juno_download'}

    script_args = parse_args(FUNCTIONS, FUNCTIONS_SINGLE_ARG)
    print(f"user chose function '{script_args.function}'")

    if script_args.function == FUNCTION_SWEEP:
        sweep(script_args, EXTENSIONS, PREFIX_HINTS)
    elif script_args.function == FUNCTION_FLATTEN:
        flatten_hierarchy(script_args)
    elif script_args.function == FUNCTION_EXTRACT:
        extract(script_args)
    elif script_args.function == FUNCTION_COMPRESS:
        # compress_dir(script_args.input, script_args.output)
        compress_all(script_args)
    elif script_args.function == FUNCTION_PRUNE:
        prune_empty(script_args)
