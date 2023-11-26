'''
re-encode tracks

'''

import subprocess
import argparse
import os
import sys
import shlex

def dev_debug(args: argparse.Namespace) -> None:
    lexed = shlex.split(args.root)
    lexed = ['ffmpeg', '-i', "/Users/zachvp/developer/music/data/tracks/0C9E6352_24-Carat Black - Poverty's Paradis.aiff", '-ar', '44100', '-c:a', 'pcm_s16be', '-write_id3v2', '1', '/Users/zachvp/developer/music/data/tracks/re-encoded/manual-testing/lexed.aif']
    print(f"running: {lexed}")

    try:
        result = subprocess.run(lexed, check=True, capture_output=True, encoding='utf-8')
        print(result.stdout.strip())
    except subprocess.CalledProcessError as error:
        print(error.stderr.strip())

    sys.exit()

def process_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=str, help='the root directory to recursively process')
    parser.add_argument('output', type=str, help='the output directory to contain all the files in a flat structure')
    parser.add_argument('extension', type=str, help='the output extension for each file')

    parser.add_argument('--interactive', '-i', action='store_true', help='run the script in interactive mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='run the script with verbose output')

    return parser.parse_args()

def build_command(args: argparse.Namespace, filename: str, input_path: str) -> list:
    # core command:
    # ffmpeg -i /path/to/input.foo -ar 44100 -c:a pcm_s16be -write_id3v2 1 path/to/output.bar
    # ffmpeg options: 44100 Hz sample rate, 16-bit PCM big-endian, write ID3V2 tags

    options_str = '-ar 44100 -c:a pcm_s16be -write_id3v2 1'

    # swap existing extension with the configured one
    # output_filename = ''.join(filename.split('.')[:-1]) + args.extension
    output_filename = filename.split('.')
    output_filename[-1] = args.extension

    output_path = os.path.join(args.output, ''.join(output_filename))

    return ['ffmpeg', '-i', input_path] + shlex.split(options_str) + [output_path]

def re_encode(args: argparse.Namespace) -> None:
    if not args.extension.startswith('.'):
        print(f"error: invalid extension {args.extension}, exiting")
        sys.exit()

    # main processing loop
    for working_dir, _, filenames in os.walk(args.root):
        if os.path.dirname(working_dir).startswith('.'):  # working_dir.lstrip('.').lstrip('/').startswith('.'):
            print(f"skipping hidden dir {os.path.dirname(working_dir)}")
            continue

        for name in filenames:
            # print(f"current root: {working_dir}")
            if name.startswith('.'):
                continue

            full_input_path = os.path.join(working_dir, name)
            if not name.endswith('.aiff'):
                print(f"skip unsupported file: {full_input_path}")
                continue
            if name.endswith('.wav'):
                print(f"warn: encountered .wav file: {full_input_path}")
                continue

            # build ffmpeg command
            command = build_command(args, name, full_input_path)
            if args.verbose:
                print(f"will run cmd:\n\t{command}")

            # interactive mode
            if args.interactive:
                choice = input("continue? [y/N]")
                if choice != 'y':
                    print('exit, user quit')
                    sys.exit()

            # run the ffmpeg command
            try:
                subprocess.run(command, check=True, capture_output=True, encoding='utf-8')
                print(f"success: {name}\n")
            except subprocess.CalledProcessError as error:
                print(f"error subprocess:\n{error.stderr}")

    print('finished processing all files')

# MAIN
if __name__ == '__main__':
    re_encode(process_args())
