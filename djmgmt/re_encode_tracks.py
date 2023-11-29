'''
re-encode tracks

'''

import subprocess
import argparse
import os
import sys
import shlex

# todo: add docstrings

def process_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=str, help='the root directory to recursively process')
    parser.add_argument('output', type=str, help='the output directory to contain all the files in a flat structure')
    parser.add_argument('extension', type=str, help='the output extension for each file')

    parser.add_argument('--storepath', type=str, help='the script storage path to write to')
    parser.add_argument('--interactive', '-i', action='store_true', help='run the script in interactive mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='run the script with verbose output')

    return parser.parse_args()

def build_command(input_path: str, output_path: str) -> list:
    # core command:
    # ffmpeg -i /path/to/input.foo -ar 44100 -c:a pcm_s16be -write_id3v2 1 path/to/output.bar
    # ffmpeg options: 44100 Hz sample rate, 16-bit PCM big-endian, write ID3V2 tags
    options_str = '-ar 44100 -c:a pcm_s16be -write_id3v2 1 -y'

    return ['ffmpeg', '-i', input_path] + shlex.split(options_str) + [output_path]

def read_ffprobe_value(args: argparse.Namespace, input_path: str, stream: str) -> str:
    command = shlex.split(f"ffprobe -v error -show_entries stream={stream} -of default=noprint_wrappers=1:nokey=1")
    command.append(input_path)

    try:
        if args.verbose:
            print(f"info: read_ffprobe_value: {command}")
        value = subprocess.run(command, check=True, capture_output=True, encoding='utf-8').stdout.strip()
        if args.verbose:
            print(f"info: read_ffprobe_value: {value}")
        return value
    except subprocess.CalledProcessError as error:
        print(f"error: fatal: read_ffprobe_value: CalledProcessError:\n{error.stderr.strip()}")
        print(f"command: {shlex.join(command)}")
        sys.exit()

    return ''

def check_skip_sample_rate(args: argparse.Namespace, input_path: str) -> bool:
    result = read_ffprobe_value(args, input_path, 'sample_rate')
    return False if len(result) < 1 else int(result) <= 44100

def check_skip_bit_depth(args: argparse.Namespace, input_path: str) -> bool:
    result = read_ffprobe_value(args, input_path, 'sample_fmt').lstrip('s')
    return False if len(result) < 1 else int(result) <= 16

def setup_storage(args: argparse.Namespace) -> str:
    # storage directory setup
    storage_dir = f"{args.storepath}/write/tsv/"
    if not os.path.exists(args.storepath):
        os.makedirs(storage_dir)
    script_path_list = os.path.normpath(__file__).split(os.sep)
    store_path = os.path.normpath(f"{storage_dir}/{script_path_list[-1].rstrip('.py')}.tsv")

    # truncate the file to clear storage
    with open(store_path, 'w', encoding='utf-8'):
        pass
    print(f"store path: {store_path}")

    return store_path

def re_encode(args: argparse.Namespace) -> None:
    if not args.extension.startswith('.'):
        print(f"error: fatal: invalid extension {args.extension}, exiting")
        sys.exit()
    size_diff_sum = 0.0

    if args.storepath:
        store_path = setup_storage(args)

    # main processing loop
    for working_dir, dirnames, filenames in os.walk(args.root):
        # prune hidden directories
        for index, directory in enumerate(dirnames):
            if directory.startswith('.'):
                del dirnames[index]

        for name in filenames:
            input_path = os.path.join(working_dir, name)
            name_split = name.split('.')

            if name.startswith('.'):
                print(f"info: skip: hidden file '{input_path}'")
                continue
            if not name_split[-1] in { 'aif', 'aiff', 'wav', }:
                print(f"info: skip: unsupported file: '{input_path}'")
                continue
            if not name.endswith('.wav') and\
            check_skip_sample_rate(args, input_path) and\
            check_skip_bit_depth(args, input_path):
                print(f"info: skip: optimal sample rate and bit depth: '{input_path}'")
                continue

            # -- build the output path
            # swap existing extension with the configured one
            output_filename = name_split.copy()
            output_filename[-1] = args.extension

            output_path = os.path.join(args.output, ''.join(output_filename))

            # interactive mode
            if args.interactive:
                choice = input(f"re-encode '{input_path}'? [y/N]")
                if choice != 'y':
                    print('exit, user quit')
                    break

            # -- build and run the ffmpeg encode command
            command = build_command(input_path, output_path)
            if args.verbose:
                print(f"run cmd:\n\t{command}")
            try:
                subprocess.run(command, check=True, capture_output=True, encoding='utf-8')
                print(f"success: {output_path}")
            except subprocess.CalledProcessError as error:
                print(f"error subprocess:\n{error.stderr.strip()}")

            # compute (input - output) size difference after encoding
            size_diff = os.path.getsize(input_path)/10**6 - os.path.getsize(output_path)/10**6
            size_diff_sum += size_diff
            size_diff = round(size_diff, 2)
            print(f"info: file size diff: {size_diff} MB")

            if args.storepath:
                with open(store_path, 'a', encoding='utf-8') as store_file:
                    store_file.write(f"{input_path}\t{output_path}\t{size_diff}\n")
            # newline to separate entries
            print()
    print("processed all files")
    if args.storepath:
        with open(store_path, 'a', encoding='utf-8') as store_file:
            store_file.write(f"\n=>size diff sum: {round(size_diff_sum, 2)}")

# MAIN
if __name__ == '__main__':
    re_encode(process_args())
