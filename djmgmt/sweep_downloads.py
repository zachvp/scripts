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

# CONSTANTS
FUNCTION_SWEEP = 'sweep'
FUNCTION_FLATTEN = 'flatten'
FUNCTIONS = {FUNCTION_FLATTEN, FUNCTION_SWEEP}

# todo: move this to main procedure and flesh out more fully
def flatten_zip(zip_path: str, extract_path: str) -> None:
    print(f"output dir: {os.path.join(extract_path, os.path.splitext(os.path.basename(zip_path))[0])}")
    with zipfile.ZipFile(zip_path, 'r') as file:
        file.extractall(os.path.normpath(extract_path))
    unzipped_path = os.path.join(extract_path, os.path.splitext(os.path.basename(zip_path))[0])
    for working_dir, _, filenames in os.walk(unzipped_path):
        for name in filenames:
            print(f"move from {os.path.join(working_dir, name)} to {extract_path}")
            shutil.move(os.path.join(working_dir, name), extract_path)
    shutil.rmtree(unzipped_path)

def flatten_hierarchy(top_path: str, output_path: str) -> None:
    for working_dir, directories, filenames in os.walk(top_path):
        prune(working_dir, directories, filenames)

        for name in filenames:
            input_path = os.path.join(working_dir, name)
            if os.path.splitext(name)[1] == '.zip':
                # flatten_zip(os.path.join(working_dir, name), output_path)
                print(f"flatten zip: {input_path, output_path}")
            elif not os.path.exists(os.path.join(output_path, name)):
                print(f"move file {input_path} to {os.path.join(output_path, name)}")
            else:
                print(f"info: skip: {input_path}")

def prune(working_dir: str, directories: list[str], filenames: list[str]) -> None:
    for index, directory in enumerate(directories):
        if directory.startswith('.') or '.app' in directory:
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

            if name_split[1] in {'.mp3', '.wav', '.aif', '.aiff', 'flac'} or\
            (name_split[1] == '.zip' and (name_split[0].startswith('beatport_tracks') or name.startswith('juno_download'))):
                print(f"info: filter matched file '{os.path.join(working_dir, name)}'")
                choice = input(f"info: will move from '{input_path}' to '{output_path}'. Continue? [y/N]")
                if choice != 'y':
                    print('info: skip: user skipped file')
                    continue
                shutil.move(input_path, output_path)
    print("swept all files")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"The script function to run. One of '{FUNCTIONS}'")
    parser.add_argument('input', type=str, help='The input directory to sweep.')
    parser.add_argument('output', type=str, help='The output directory to place the swept tracks.')
    parser.add_argument('--zip-filter', type=str )
    parser.add_argument('--interactive', '-i', action='store_true')

    args = parser.parse_args()

    if args.function not in FUNCTIONS:
        parser.error(f"invalid function '{args.function}'")

    args.input = os.path.normpath(args.input)
    args.output = os.path.normpath(args.output)

    return args

if __name__ == '__main__':
    script_args = parse_args()

    if script_args.function == 'sweep':
        print('fake sweep')
        # sweep(script_args)
    elif script_args.function == 'flatten':
        print('fake flatten')
        flatten_hierarchy(script_args.input, script_args.output)
        # flatten_zip(script_args.input, script_args.output)
