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
SOUND_TYPES = {'.mp3', '.wav', '.aif', '.aiff', 'flac'}

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

def sweep(args: argparse.Namespace) -> None:
    for working_dir, directories, filenames in os.walk(args.input):
        # prune hidden directories
        for index, directory in enumerate(directories):
            if directory.startswith('.') or '.app' in directory:
                print(f"info: skip: hidden directory or '.app' archive '{os.path.join(working_dir, directory)}'")
                del directories[index]
        for index, filename in enumerate(filenames):
            if filename.startswith('.'):
                print(f"info: skip: hidden file '{filename}'")
                del filenames[index]

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
    parser.add_argument('input', type=str, help='The input directory to sweep.')
    parser.add_argument('output', type=str, help='The output directory to place the swept tracks.')
    parser.add_argument('--zip-filter', type=str )
    parser.add_argument('--interactive', '-i', action='store_true')

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)
    args.output = os.path.normpath(args.output)

    return args

if __name__ == '__main__':
    script_args = parse_args()

    flatten_zip(script_args.input, script_args.output)
    # sweep(script_args)
