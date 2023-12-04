'''
goal: sweep downloads folder for music files

procedure
    F: filter source directory for eligible files, directories, or archives
    C: copy F.contents into destination directory
bonus
    + flatten C in destination directory
'''

import argparse
import os
import shutil
import zipfile

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

def flatten_hierarchy(args: argparse.Namespace) -> None:
    for working_dir, directories, filenames in os.walk(args.input):
        prune(working_dir, directories, filenames)

        for name in filenames:
            input_path = os.path.join(working_dir, name)
            output_path = os.path.join(args.output, name)
            if os.path.splitext(name)[1] == '.zip':
                print(f"flatten zip: {input_path, args.output}")
                if args.interactive:
                    choice = input('Continue? [y/N/q]')
                    if choice == 'q':
                        print('info: user quit')
                        return
                    if choice != 'y' or choice in 'nN':
                        print(f"info: skip: {input_path}")
                        continue
                flatten_zip(os.path.join(working_dir, name), args.output)
            elif not os.path.exists(output_path):
                print(f"move '{input_path}' to '{output_path}'")
                if args.interactive:
                    choice = input('Continue? [y/N/q]')
                    if choice == 'q':
                        print('info: user quit')
                        return
                    if choice != 'y' or choice in 'nN':
                        print(f"info: skip: {input_path}")
                        continue
                shutil.move(input_path, output_path)
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

def sweep(args: argparse.Namespace) -> None:
    for working_dir, directories, filenames in os.walk(args.input):
        prune(working_dir, directories, filenames)

        for name in filenames:
            input_path = os.path.join(working_dir, name)
            output_path = os.path.join(args.output, name)
            name_split = os.path.splitext(name)

            is_valid_archive = name_split[1] == '.zip' and is_prefix_match(name, {'beatport_tracks', 'juno_download'})
            if name_split[1] in {'.mp3', '.wav', '.aif', '.aiff', 'flac'} or is_valid_archive:
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

def parse_args(valid_functions: set[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"The script function to run. One of '{valid_functions}'")
    parser.add_argument('input', type=str, help='The input directory to sweep.')
    parser.add_argument('output', type=str, help='The output directory to place the swept tracks.')
    parser.add_argument('--zip-filter', type=str )
    parser.add_argument('--interactive', '-i', action='store_true')

    args = parser.parse_args()

    if args.function not in valid_functions:
        parser.error(f"invalid function '{args.function}'")

    args.input = os.path.normpath(args.input)
    args.output = os.path.normpath(args.output)

    return args

if __name__ == '__main__':
    # CONSTANTS
    FUNCTION_SWEEP = 'sweep'
    FUNCTION_FLATTEN = 'flatten'
    FUNCTIONS = {FUNCTION_FLATTEN, FUNCTION_SWEEP}

    script_args = parse_args(FUNCTIONS)

    if script_args.function == 'sweep':
        print(f"user chose function {script_args.function}")
        sweep(script_args)
    elif script_args.function == 'flatten':
        print(f"user chose function {script_args.function}")
        flatten_hierarchy(script_args)
        # flatten_zip(script_args.input, script_args.output)
