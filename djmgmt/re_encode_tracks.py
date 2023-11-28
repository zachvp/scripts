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

    parser.add_argument('--interactive', '-i', action='store_true', help='run the script in interactive mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='run the script with verbose output')

    return parser.parse_args()

def build_command(input_path: str, output_path: str) -> list:
    # core command:
    # ffmpeg -i /path/to/input.foo -ar 44100 -c:a pcm_s16be -write_id3v2 1 path/to/output.bar
    # ffmpeg options: 44100 Hz sample rate, 16-bit PCM big-endian, write ID3V2 tags

    options_str = '-ar 44100 -c:a pcm_s16be -write_id3v2 1 -y'

    return ['ffmpeg', '-i', input_path] + shlex.split(options_str) + [output_path]

# todo: add common method for sample rate and bit depth

def check_skip_sample_rate(args: argparse.Namespace, input_path: str):
    # core command:
    # ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate\
    #   -of default=noprint_wrappers=1:nokey=1 "path/to/input.foo"
    # ffprobe options: only log errors, show value in a minimally printed format
    command = shlex.split('ffprobe -v error -show_entries stream=sample_rate -of default=noprint_wrappers=1:nokey=1')
    command.append(input_path)

    try:
        if args.verbose:
            print(f"info: check sample rate: {command}")
        sample_rate = int(subprocess.run(command, check=True, capture_output=True, encoding='utf-8').stdout.strip())
        if args.verbose:
            print(f"info: sample rate: {sample_rate}")
        return sample_rate <= 44100
    except subprocess.CalledProcessError as error:
        print(f"error: fatal: could not read sample rate: subprocess:\n{error.stderr.strip()}")
        sys.exit()

    return False

def check_skip_bit_depth(args: argparse.Namespace, input_path: str):
    # core command:
    # ffprobe -v error -select_streams a:0 -show_entries stream=sample_fmt\
    #   -of default=noprint_wrappers=1:nokey=1 "path/to/input.foo"
    # ffprobe options: only log errors, show value in a minimally printed format
    command_format = shlex.split('-of default=noprint_wrappers=1:nokey=1')
    command = shlex.split('ffprobe -v error -select_streams a:0 -show_entries stream=sample_fmt')
    command += command_format
    command.append(input_path)

    try:
        if args.verbose:
            print(f"info: check bit depth: {command}")
        bit_depth = int(subprocess.run(command, check=True, capture_output=True, encoding='utf-8')\
            .stdout.strip().lstrip('s'))
        if args.verbose:
            print(f"info: bit depth: {bit_depth}")
        return bit_depth == 16
    except subprocess.CalledProcessError as error:
        print(f"error: fatal: could not read sample rate: subprocess:\n{error.stderr.strip()}")
        print(f"command: {shlex.join(command)}")
        sys.exit()

def re_encode(args: argparse.Namespace) -> None:
    if not args.extension.startswith('.'):
        print(f"error: invalid extension {args.extension}, exiting")
        sys.exit()

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
            if not name.endswith('.wav'):
                if check_skip_sample_rate(args, input_path) and check_skip_bit_depth(args, input_path):
                    print(f"info: skip: optimal sample rate and bit depth: '{input_path}'")
                    continue

            # build the output path

            # swap existing extension with the configured one
            output_filename = name_split.copy()
            output_filename[-1] = args.extension

            output_path = os.path.join(args.output, ''.join(output_filename))

            # build ffmpeg command
            command = build_command(input_path, output_path)
            if args.verbose:
                print(f"run cmd:\n\t{command}")

            # interactive mode
            if args.interactive:
                choice = input(f"re-encode '{input_path}'? [y/N]")
                if choice != 'y':
                    print('exit, user quit')
                    sys.exit()

            # run the ffmpeg command
            try:
                subprocess.run(command, check=True, capture_output=True, encoding='utf-8')
                print(f"success: {output_path}")
            except subprocess.CalledProcessError as error:
                print(f"error subprocess:\n{error.stderr.strip()}")

            # compute input - output size difference after encoding
            # todo: write each size diff to file: '{input_path, output_path : size_diff}'
            size_diff = os.path.getsize(input_path) / 10**6 - os.path.getsize(output_path) / 10**6
            size_diff = round(size_diff, 2)
            print(f"info: file size diff: {size_diff} MB")
            print()

    print('processed all files')

# MAIN
if __name__ == '__main__':
    re_encode(process_args())
