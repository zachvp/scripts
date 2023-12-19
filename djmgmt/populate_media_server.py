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

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help="The top level directory to search.\
        It's expected to be structured in a year/month/audio.file format.")
    parser.add_argument('output', type=str, help="The output directory to populate.")

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)
    args.output = os.path.normpath(args.output)

    return args

def find_oldest_dir(ordered_names: list[str], dirnames: list[str], excluded_dirnames: list[str]) -> str:
    for name in ordered_names:
        if name in dirnames and name not in excluded_dirnames:
            return name
    return ''

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
            print(f"info: sync '{input_path_full}' -> {output_path_full}")
            date_context = '/'.join(path.split('/')[:2])
            if len(previous_date_context) > 0 and previous_date_context != date_context:
                choice = input(f"info: date context changed from '{previous_date_context}' to '{date_context}' continue? [y/N]")
                if choice != 'y':
                    print('info: user quit')
                    return
            previous_date_context = date_context

            output_parent_path = os.path.split(output_path_full)[0]
            if not os.path.exists(output_parent_path):
                os.makedirs(output_parent_path)
            shutil.copy(input_path_full, output_path_full)

if __name__ == '__main__':
    script_args = parse_args()
    sync(script_args)
