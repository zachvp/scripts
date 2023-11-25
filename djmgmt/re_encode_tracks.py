'''
re-encode tracks

# core command
ffmpeg -i "/path/to/track.foo"\
    -ar 44100 -c:a pcm_s16be -write_id3v2 1\
    path/to/output/file.bar"

'''

import subprocess
import argparse

# CONSTANTS
SAMPLE_RATE = 44100 #: Hz

# MAIN
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='the input file to process, including extension')
    # parser.add_argument('output', type=str, help='the output file path, including extension')

    args = parser.parse_args()

    # command = f"ffmpeg -i {args.input} -ar 44100 -c:a pcm_s16be -write_id3v2 1 {args.output}"
    command = args.input

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, encoding='utf-8')
        print(f"success:\n{result.stdout.strip()}\n")
    except subprocess.CalledProcessError as error:
        print(f"error subprocess:\n{error.stderr}")
        # print(f"stderr:\n{result.stderr.strip()}")
