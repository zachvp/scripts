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
    OLDEST: identify oldest year/month directory present in input
    if OLDEST exists in destination
        skip
    copy OLDEST to output
'''

import argparse
import os
import shutil
import sys
import pdb

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help="The top level directory to search.\
        It's expected to be structured in a year/month/audio.file format.")
    parser.add_argument('output', type=str, help="The output directory to populate.")
    parser.add_argument('--interactive', '-i', action='store_true', help="Run the script in interactive mode.")

    args = parser.parse_args()
    args.input = os.path.normpath(args.input)
    args.output = os.path.normpath(args.output)

    return args

def find_oldest_dir(ordered_names: list[str], dirnames: list[str], excluded_dirnames: list[str]) -> str:
    for name in ordered_names:
        if name in dirnames and name not in excluded_dirnames:
            return name
    return ''

def sync_oldest(args: argparse.Namespace, month_order: list[str]) -> None:
    years = sorted(os.listdir(args.input))

    for year in years:
        input_path = os.path.join(args.input, year)
        if not os.path.isdir(input_path):
            print(f"info: skip: ignore non-directory '{input_path}'")
            continue

        output_path = os.path.join(args.output, year)
        if not os.path.exists(output_path):
            print(f"info: {output_path} does not exist, will create")
            os.mkdir(output_path)

        oldest_dir = find_oldest_dir(month_order, os.listdir(input_path), os.listdir(output_path))
        input_path = os.path.join(input_path, oldest_dir)
        output_path = os.path.join(output_path, oldest_dir)
        input_path_top = input_path

        if os.path.exists(output_path):
            print("info: will check for sync within directories")
            for dirname in os.listdir(input_path_top):
                if not os.path.isdir(os.path.join(input_path, dirname)):
                    print(f"info: skip: ignore non-directory '{os.path.join(input_path, dirname)}'")
                    continue
                input_path = os.path.join(input_path, dirname)
                output_path = os.path.join(output_path, dirname)

                sync_paths = set(os.listdir(input_path)).difference(os.listdir(output_path))
                print(f"sync paths: {sync_paths}")
                # breakpoint()
                for path in sync_paths:
                    input_path = os.path.join(input_path, path)
                    output_path = os.path.join(output_path, path)
                    if not os.path.isdir(input_path):
                        print(f"info: skip: ignore non-directory '{input_path}'")
                        continue
                    if os.path.exists(output_path):
                        print(f"error: path exists in ouput but not in input: '{os.path.join(output_path, path)}'")
                        continue

                    if not os.path.exists(output_path):
                        print(f"info: will copy '{input_path} -> {input_path}'")
                        if args.interactive:
                            choice = input("continue? [y/N]")
                            if choice != 'y':
                                print("info: skip: user chose not to copy '{dirname}'")
                                break
                        shutil.copytree(input_path, output_path)
        else:
            print(f"info: will copy '{input_path}' -> '{output_path}'")
            if args.interactive:
                choice = input("continue? [y/N]")
                if choice != 'y':
                    print("info: user quit")
                    break
            shutil.copytree(input_path, output_path)
            break

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
