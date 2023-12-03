'''
general purpose script to perform some bulk operation on a list of files

read paths containing list of files, perform one of
    rm
    mv
'''

import os
import shutil
import argparse

def format_message(message: str) -> str:
    message_lines = message.split('\n')
    output = ''
    for line in message_lines:
        output += f"{line.lstrip()}\n"

    return output.rstrip()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help="The type of function to perform. One of: 'mv', 'rm'")
    parser.add_argument('input_path', type=str, help='The input path to the file containing the list of paths.\
        Expects TSV format.')
    parser.add_argument('output_path', type=str, help='The output path that all files will be written to.')
    parser.add_argument('--column', '-c', type=int, help='The column to process in the input file.')

    args = parser.parse_args()

    # validate arguments
    functions = {'mv'}
    if args.function not in functions:
        parser.error(f"Invalid parameter '{args.function}' for positional argument 'function'. Expect one of: {functions}.")

    # normalize arguments
    args.input_path = os.path.normpath(args.input_path)
    args.output_path = os.path.normpath(args.output_path)
    if not args.column:
        args.column = 0

    if os.path.splitext(args.input_path)[1] != '.tsv':
        parser.error(f"Invalid parameter {args.input_path} for positional argument 'input_path'. Expect '*.tsv' file.")

    # main processing loop
    with open(args.input_path, 'r', encoding='utf-8') as input_file:
        lines : list[str] = input_file.readlines()
        for line in lines:
            # os.path.normpath(input_path.strip())
            input_path = os.path.normpath(line.split()[args.column])
            if args.function == 'mv':
                if not os.path.exists(os.path.normpath(args.output_path)):
                    os.makedirs(os.path.normpath(args.output_path))

                new_path = os.path.normpath(f"{args.output_path}/{os.path.basename(input_path)}")
                if os.path.exists(new_path):
                    print(f"info: skip: path '{os.path.normpath(args.output_path)}' exists")
                    continue

                choice = input(format_message(f"""input: move
                    '{os.path.normpath(input_path)}' to '{os.path.normpath(args.output_path)}'
                    continue? [y/N]"""))
                if choice != 'y':
                    print("info: exit: user quit")
                    break

                shutil.move(os.path.normpath(input_path), os.path.normpath(args.output_path))
