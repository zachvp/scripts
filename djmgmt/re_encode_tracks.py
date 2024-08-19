'''
re-encode tracks
'''

import subprocess
import argparse
import os
import sys
import shlex

def process_args() -> argparse.Namespace:
    '''Process the script's command line aruments.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='the input directory to recursively process')
    parser.add_argument('output', type=str, help='the output directory to contain all the files in a flat structure')
    parser.add_argument('extension', type=str, help='the output extension for each file')

    parser.add_argument('--store-path', type=str, help='the script storage path to write to')
    parser.add_argument('--store-skipped', action='store_true', help='store the skipped files in store path')
    parser.add_argument('--interactive', '-i', action='store_true', help='run the script in interactive mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='run the script with verbose output')

    args = parser.parse_args()

    if args.store_skipped and not args.store_path:
        parser.error("if option '--store-skipped' is set, option '--store-path' is required")

    return args

def build_ffmpeg_command(input_path: str, output_path: str) -> list:
    '''Returns a list of ffmpeg command line arguments that will encode the `input_path` to the `output_path`.
    Core command:
        ffmpeg -i /path/to/input.foo -ar 44100 -c:a pcm_s16be -write_id3v2 1 -y path/to/output.bar
        ffmpeg options: 44100 Hz sample rate, 16-bit PCM big-endian, write ID3V2 tags
    '''
    options_str = '-ar 44100 -c:a pcm_s16be -write_id3v2 1 -y'

    return ['ffmpeg', '-i', input_path] + shlex.split(options_str) + [output_path]

def read_ffprobe_value(args: argparse.Namespace, input_path: str, stream: str) -> str:
    '''Uses ffprobe command line tool. Reads the ffprobe value for a particular stream entry.

    Args:
    `args`        : The script's arguments.
    `input_path`  : Path to the file to probe.
    `stream`      : The stream label according to 'ffprobe' documentation.

    Returns:
    Stripped stdout of the ffprobe command or empty string.
    '''
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

def check_skip_sample_rate(args: argparse.Namespace, input_path: str) -> bool:
    '''Returns `True` if sample rate for `input_path` is at or below the standardized value.
    '''
    result = read_ffprobe_value(args, input_path, 'sample_rate')
    return False if len(result) < 1 else int(result) <= 44100

def check_skip_bit_depth(args: argparse.Namespace, input_path: str) -> bool:
    '''Returns `True` if bit depth (aka 'sample format') is at or below the standardized value.
    '''
    result = read_ffprobe_value(args, input_path, 'sample_fmt').lstrip('s')
    return False if len(result) < 1 else int(result) <= 16

def setup_storage(args: argparse.Namespace, filename: str) -> str:
    '''Create or clear a storage file called `filename` at the path specified in `args`.

    Returns:
    The absolute path to the storage file.
    '''
    script_path_list = os.path.normpath(__file__).split(os.sep)
    storage_dir = os.path.normpath(f"{args.store_path}/{script_path_list[-1].rstrip('.py')}/")
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)

    # create the file or clear any existing storage
    store_path = os.path.join(storage_dir, filename)
    with open(store_path, 'w', encoding='utf-8'):
        pass
    print(f"set up store path: {store_path}")

    return store_path

def re_encode(args: argparse.Namespace) -> None:
    '''Primary script function. Recursively walks the input path specified in `args` to re-encode each eligible file.
    A file is eligible if:
        1) It is an uncompressed `aiff` or `wav` type.
        2) It has a sample rate exceeding 44100 Hz or bit depth exceeding 16 bits.

    All other files are skipped. If `args` is configured properly, the user can store each skipped path in a file.

    If `args` is configured properly, the script can also store each difference in file size before and after re-encoding.
    '''

    if not args.extension.startswith('.'):
        print(f"error: fatal: invalid extension {args.extension}, exiting")
        sys.exit()
    size_diff_sum = 0.0

    # set up storage
    if args.store_path:
        store_path_size_diff = setup_storage(args, 'size-diff.tsv')
    if args.store_skipped:
        store_path_skipped = setup_storage(args, 'skipped.tsv')
        skipped_files : list[str] = []

    # confirm storage with user
    if args.interactive and args.store_path:
        choice = input("storage set up, does everything look okay? [y/N]")
        if choice != 'y':
            print("user quit")
            return

    # main processing loop
    for working_dir, dirnames, filenames in os.walk(args.input):
        # prune hidden directories
        for index, directory in enumerate(dirnames):
            if directory.startswith('.'):
                print(f"info: skip: hidden directory '{os.path.join(working_dir, directory)}'")
                del dirnames[index]

        for name in filenames:
            input_path = os.path.join(working_dir, name)
            name_split = os.path.splitext(name)

            if name.startswith('.'):
                print(f"info: skip: hidden file '{input_path}'")
                print(f"info: skip: hidden files are not written to skip storage '{input_path}'")
                continue
            if name_split[1] not in { '.aif', '.aiff', '.wav', }:
                print(f"info: skip: unsupported file: '{input_path}'")
                skipped_files.append(f"{input_path}\n")
                continue
            if not name.endswith('.wav') and\
            check_skip_sample_rate(args, input_path) and\
            check_skip_bit_depth(args, input_path):
                print(f"info: skip: optimal sample rate and bit depth: '{input_path}'")
                skipped_files.append(f"{input_path}\n")
                continue

            # -- build the output path
            # swap existing extension with the configured one
            output_filename = name_split[0] + args.extension
            output_path = os.path.join(args.output, ''.join(output_filename))

            if os.path.splitext(os.path.basename(input_path))[0] != os.path.splitext(os.path.basename(output_path))[0]:
                choice = input(f"warn: mismatched file names for '{input_path}' and '{output_path}'. Continue? [y/N]")
                if choice != 'y' or choice.lower() == 'n':
                    print('exit, user quit')
                    break

            # interactive mode
            if args.interactive:
                choice = input(f"re-encode '{input_path}'? [y/N]")
                if choice != 'y':
                    print('exit, user quit')
                    break

            # -- build and run the ffmpeg encode command
            command = build_ffmpeg_command(input_path, output_path)
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

            if args.store_path:
                with open(store_path_size_diff, 'a', encoding='utf-8') as store_file:
                    store_file.write(f"{input_path}\t{output_path}\t{size_diff}\n")
            # newline to separate entries
            print()

    if args.store_path:
        with open(store_path_size_diff, 'a', encoding='utf-8') as store_file:
            store_file.write(f"\n=> size diff sum: {round(size_diff_sum, 2)} MB")
            print(f"info: wrote cumulative size difference to '{store_path_size_diff}'")
    if args.store_skipped:
        with open(store_path_skipped, 'a', encoding='utf-8') as store_file:
            store_file.writelines(skipped_files)
            print(f"info: wrote skipped files to '{store_path_skipped}'")

# MAIN
if __name__ == '__main__':
    re_encode(process_args())
