'''
move files according to directory structure rules
specs
    D: structured directory
        ./year/month/audio.file
    R: rules
        year: 4-digit positive int (e.g. 2023)
        month: english month name (e.g. january)
        audio.file: must be an audio file type
    arguments
        input: D directory path
        output: D directory path

process
    OLDEST: identify oldest year/month directory tree present in input path
    if OLDEST exists in destination
        skip
    copy OLDEST to output path
'''

import argparse
import os
import shutil
import sys

# CONSTANTS
SCRIPT_MODE_COPY = 'copy'
SCRIPT_MODE_MOVE = 'move'

SCRIPT_MODES = {SCRIPT_MODE_COPY, SCRIPT_MODE_MOVE}

def parse_args(valid_modes: set[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', type=str, help=f"The mode to run the script. One of '{valid_modes}'.")
    parser.add_argument('input', type=str, help="The top level directory to search.\
        It's expected to be structured in a year/month/audio.file format.")
    parser.add_argument('output', type=str, help="The output directory to populate.")

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)
    args.output = os.path.normpath(args.output)

    if args.mode not in valid_modes:
        parser.error(f"Invalid mode: '{args.mode}'")

    return args

def enumerate_paths(top: str) -> list[str]:
    paths: list[str] = []
    for working_dir, _, filenames in os.walk(top):
        for name in filenames:
            if not name.startswith('.'):
                paths.append(os.path.join(working_dir, name))
    return paths

def normalize_paths(paths: list[str], parent: str) -> list[str]:
    normalized = []
    for path in paths:
        normalized.append(os.path.relpath(path, start=parent))
    return normalized

def sync(args: argparse.Namespace):
    input_paths = sorted(normalize_paths(enumerate_paths(args.input), args.input))
    output_paths = set(normalize_paths(enumerate_paths(args.output), args.output))
    previous_date_context = ''

    for path in input_paths:
        if path not in output_paths:
            input_path_full = os.path.join(args.input, path)
            output_path_full = os.path.join(args.output, path)

            # todo: implement overwrite logic according to script args
            if os.path.exists(output_path_full):
                print(f"info: skip: output path exists: '{output_path_full}'")

            print(f"info: {args.mode} '{input_path_full}' -> {output_path_full}")
            date_context = '/'.join(path.split('/')[:2]) # format: 'year/month'
            if len(previous_date_context) > 0 and previous_date_context != date_context:
                choice = input(f"info: date context changed from '{previous_date_context}' to '{date_context}' continue? [y/N]")
                if choice != 'y':
                    print('info: user quit')
                    return
            previous_date_context = date_context

            output_parent_path = os.path.split(output_path_full)[0]
            if not os.path.exists(output_parent_path):
                os.makedirs(output_parent_path)
            if args.mode == SCRIPT_MODE_COPY:
                # todo: implement overwrite logic according to script args
                shutil.copy(input_path_full, output_path_full)
            elif args.mode == SCRIPT_MODE_MOVE:
                shutil.move(input_path_full, output_path_full)
            else:
                print(f"error: unrecognized mode: {args.mode}. Exiting")
                sys.exit()

if __name__ == '__main__':
    script_args = parse_args(SCRIPT_MODES)
    sync(script_args)
