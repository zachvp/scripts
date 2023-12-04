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

# todo: move this to main procedure and flesh out more fully
def flatten_zip(zip_path: str, extract_path: str) -> None:
    with zipfile.ZipFile(zip_path, 'r') as file:
        file.extractall(os.path.normpath(extract_path))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='The input directory to sweep.')
    parser.add_argument('output', type=str, help='The output directory to place the swept tracks.')
    parser.add_argument('--zip-filter', type=str )

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)
    args.output = os.path.normpath(args.output)

    flatten_zip(args.input, args.output)
    exit()

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
                print(f"info: will move from '{input_path}' to '{output_path}'")
                shutil.move(input_path, output_path)
    print("swept all files")
