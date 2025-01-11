'''
re-encode tracks
'''

import subprocess
import argparse
import os
import sys
import shlex
import logging
import sys
import asyncio
from asyncio import Task, Future, AbstractEventLoop
from typing import Any


import common
import constants


class Namespace(argparse.Namespace):
    # arguments
    function: str
    input: str
    output: str
    extension: str
    
    store_path: str
    store_skipped: bool
    interactive: bool
    verbose: bool
    
    # functions
    FUNCTION_LOSSLESS = 'lossless'
    FUNCTION_LOSSY = 'lossy'
    FUNCTION_MISSING_ART = 'missing_art'
    FUNCTIONS = {FUNCTION_LOSSLESS, FUNCTION_LOSSY, FUNCTION_MISSING_ART}

def parse_args(functions: set[str]) -> type[Namespace]:
    '''Process the script's command line aruments.'''
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"the function to run; one of: '{functions}'")
    parser.add_argument('input', type=str, help='the input path')
    parser.add_argument('output', type=str, help='the output path')
    
    parser.add_argument('--extension', '-e', type=str, help='the output extension for each file')
    parser.add_argument('--store-path', type=str, help='the script storage path to write to')
    parser.add_argument('--store-skipped', action='store_true', help='store the skipped files in store path')
    parser.add_argument('--interactive', '-i', action='store_true', help='run the script in interactive mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='run the script with verbose output')

    args = parser.parse_args(namespace=Namespace)
    
    if args.function not in functions:
        parser.error(f"invalid function '{args.function}', expect one of: '{functions}'")

    if args.store_skipped and not args.store_path:
        parser.error("if option '--store-skipped' is set, option '--store-path' is required")

    return args

def ffmpeg_base(input_path: str, output_path: str, options: str) -> list[str]:
    all_options = f"-ar 44100 -write_id3v2 1 {options}"
    return ['ffmpeg', '-i', input_path] + shlex.split(all_options) + [output_path]

def ffmpeg_standardize(input_path: str, output_path: str) -> list[str]:
    '''Returns a list of ffmpeg command line arguments that will encode the `input_path` to the `output_path`.
    Core command:
        ffmpeg -i /path/to/input.foo -ar 44100 -c:a pcm_s16be -write_id3v2 1 -y path/to/output.bar
        ffmpeg options: 44100 Hz sample rate, decode audio stream, 16-bit PCM big-endian, write ID3V2 tags
    '''
    options = '-c:a pcm_s16be'

    return ffmpeg_base(input_path, output_path, options)

def ffmpeg_mp3(input_path: str, output_path: str, map_options: str='-map 0') -> list[str]: # todo: use shlex.quote()
    options = f"-b:a 320k {map_options}"
    return ffmpeg_base(input_path, output_path, options)

def read_ffprobe_value(args: type[Namespace], input_path: str, stream_key: str) -> str:
    '''Uses ffprobe command line tool. Reads the ffprobe value for a particular stream entry.

    Args:
    `args`        : The script's arguments.
    `input_path`  : Path to the file to probe.
    `stream_key`  : The stream label according to 'ffprobe' documentation.

    Returns:
    Stripped stdout of the ffprobe command or empty string.
    '''
    command = shlex.split(f"ffprobe -v error -show_entries stream={stream_key} -of default=noprint_wrappers=1:nokey=1")
    command.append(input_path)

    try:
        if args.verbose:
            logging.debug(f"read_ffprobe_value: {command}")
        value = subprocess.run(command, check=True, capture_output=True, encoding='utf-8').stdout.strip()
        if args.verbose:
            logging.debug(f"read_ffprobe_value: {value}")
        return value
    except subprocess.CalledProcessError as error:
        logging.error(f"fatal: read_ffprobe_value: CalledProcessError:\n{error.stderr.strip()}")
        logging.debug(f"command: {shlex.join(command)}")
        sys.exit()

def command_ffprobe_json(path: str) -> list[str]:
    # todo: read the tag data to try to determine if only 'Publisher Logotype' is expected.
    # ffprobe -v error -select_streams v -show_entries stream=index,codec_name,codec_type,width,height,:tags=comment -of json '/Users/zachvp/Music/DJ/Bernard Badie - Train feat Dajae (Original .aiff'
    
    command_str = f"ffprobe -v error -select_streams v"
    command_str += f" -show_entries stream=index,width,height,:tags=comment -of json {shlex.quote(path)}"
    command = shlex.split(command_str)
    return command    

def read_ffprobe_json(path: str) -> list[dict[str, Any]]:
    '''Reads the ffprobe video streams of the given file.'''
    import json
    command = command_ffprobe_json(path)
    code, output = run_command(command)
    
    if code == 0:
        streams = json.loads(output)['streams']
        logging.debug(f"read streams for '{path}':\n{streams}")
        return streams
    return []

def guess_cover_stream_specifier(streams: list[dict[str, Any]]) -> int:
    '''Inspects the width and height of the video stream JSON to try to find a likely cover image.'''
    min_index, min_diff = -1, float('inf')
    for stream in streams:
        index = stream['index']
        width, height = stream['width'], stream['height']
        
        diff = abs(width - height)
        threshold = 3 # based on common placeholder image dimensions 250x1500
        
        if width / height >  threshold or height / width > threshold:
            logging.debug(f"found non-square video content at index {index}")
            continue
        if 'comment' in stream['tags'] and 'logotype' in stream['tags']['comment'].lower():
            logging.debug(f"found non-cover video content at index {index}: '{stream['tags']['comment']}")
            continue
        if diff < min_diff:
            min_diff = diff
            min_index = index
    return min_index

def check_skip_sample_rate(args: type[Namespace], input_path: str) -> bool:
    '''Returns `True` if sample rate for `input_path` is at or below the standardized value.'''
    result = read_ffprobe_value(args, input_path, 'sample_rate')
    return False if len(result) < 1 else int(result) <= 44100

def check_skip_bit_depth(args: type[Namespace], input_path: str) -> bool:
    '''Returns `True` if bit depth (aka 'sample format') is at or below the standardized value.'''
    result = read_ffprobe_value(args, input_path, 'sample_fmt').lstrip('s')
    return False if len(result) < 1 else int(result) <= 16

def setup_storage(args: type[Namespace], filename: str) -> str:
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
    logging.debug(f"set up store path: {store_path}")

    return store_path

def encode_lossless(args: type[Namespace]) -> None:
    '''Primary script function. Recursively walks the input path specified in `args` to re-encode each eligible file.
    A file is eligible if:
        1) It is an uncompressed `aiff` or `wav` type.
        2) It has a sample rate exceeding 44100 Hz or bit depth exceeding 16 bits.

    All other files are skipped. If `args` is configured properly, the user can store each skipped path in a file.

    If `args` is configured properly, the script can also store each difference in file size before and after re-encoding.
    '''

    if not args.extension.startswith('.'):
        error = ValueError(f"invalid extension {args.extension}")
        logging.error(error)
        raise error
    size_diff_sum = 0.0

    # set up storage
    store_path_size_diff: str | None = None
    store_path_skipped: str | None = None
    skipped_files: list[str] | None = None
    if args.store_path:
        store_path_size_diff = setup_storage(args, 'size-diff.tsv')
    if args.store_skipped:
        store_path_skipped = setup_storage(args, 'skipped.tsv')
        skipped_files = []

    # confirm storage with user
    if args.interactive and args.store_path:
        choice = input("storage set up, does everything look okay? [y/N]")
        if choice != 'y':
            logging.info("user quit")
            return

    # main processing loop
    for working_dir, dirnames, filenames in os.walk(args.input):
        # prune hidden directories
        for index, directory in enumerate(dirnames):
            if directory.startswith('.'):
                logging.debug(f"skip: hidden directory '{os.path.join(working_dir, directory)}'")
                del dirnames[index]

        for name in filenames:
            input_path = os.path.join(working_dir, name)
            name_split = os.path.splitext(name)

            if name.startswith('.'):
                logging.debug(f"skip: hidden file '{input_path}'")
                logging.debug(f"skip: hidden files are not written to skip storage '{input_path}'")
                continue
            if name_split[1] not in { '.aif', '.aiff', '.wav', }:
                logging.debug(f"skip: unsupported file: '{input_path}'")
                if skipped_files:
                    skipped_files.append(f"{input_path}\n")
                continue
            if not name.endswith('.wav') and\
            check_skip_sample_rate(args, input_path) and\
            check_skip_bit_depth(args, input_path):
                logging.debug(f"skip: optimal sample rate and bit depth: '{input_path}'")
                if skipped_files:
                    skipped_files.append(f"{input_path}\n")
                continue

            # -- build the output path
            # swap existing extension with the configured one
            output_filename = name_split[0] + args.extension
            output_path = os.path.join(args.output, ''.join(output_filename))

            if os.path.splitext(os.path.basename(input_path))[0] != os.path.splitext(os.path.basename(output_path))[0]:
                choice = input(f"warn: mismatched file names for '{input_path}' and '{output_path}'. Continue? [y/N]")
                if choice != 'y' or choice.lower() == 'n':
                    logging.info('exit, user quit')
                    break

            # interactive mode
            if args.interactive:
                choice = input(f"re-encode '{input_path}'? [y/N]")
                if choice != 'y':
                    logging.info('exit, user quit')
                    break

            # -- build and run the ffmpeg encode command
            command = ffmpeg_standardize(input_path, output_path)
            if args.verbose:
                logging.debug(f"run cmd:\n\t{command}")
            try:
                subprocess.run(command, check=True, capture_output=True, encoding='utf-8')
                logging.debug(f"success: {output_path}")
            except subprocess.CalledProcessError as error:
                logging.error(f"subprocess:\n{error.stderr.strip()}")

            # compute (input - output) size difference after encoding
            size_diff = os.path.getsize(input_path)/10**6 - os.path.getsize(output_path)/10**6
            size_diff_sum += size_diff
            size_diff = round(size_diff, 2)
            logging.info(f"file size diff: {size_diff} MB")

            if args.store_path and store_path_size_diff:
                with open(store_path_size_diff, 'a', encoding='utf-8') as store_file:
                    store_file.write(f"{input_path}\t{output_path}\t{size_diff}\n")
            # separate entries
            logging.info("= = = =")

    if args.store_path and store_path_size_diff:
        with open(store_path_size_diff, 'a', encoding='utf-8') as store_file:
            store_file.write(f"\n=> size diff sum: {round(size_diff_sum, 2)} MB")
            logging.info(f"wrote cumulative size difference to '{store_path_size_diff}'")
    if args.store_skipped and store_path_skipped and skipped_files:
        with open(store_path_skipped, 'a', encoding='utf-8') as store_file:
            store_file.writelines(skipped_files)
            logging.info(f"wrote skipped files to '{store_path_skipped}'")

def run_command(command: list[str]) -> tuple[int, str]:
    try:
        logging.debug(f"run command: {shlex.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, encoding='utf-8')
        logging.debug(f"command success:\n{result.stdout.strip()}")
        return (result.returncode, result.stdout.strip())
    except subprocess.CalledProcessError as error:
        logging.error(f"return code '{error.returncode}':\n{error.stderr.strip()}")
        return (error.returncode, error.stderr.strip())

async def run_command_async(command: list[str]) -> tuple[int, str]:
    logging.debug(f"run command: {shlex.join(command)}")
    process = await asyncio.create_subprocess_shell(
        shlex.join(command),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    
    # wait for process to finish
    stdout, stderr = await process.communicate()
    if process.returncode is None:
        raise RuntimeError(f"process has return code 'None'.")
    if process.returncode == 0:
        message = f"command output:\n"
        output = ''
        if stdout:
            output = stdout.decode()
        elif stderr:
            output = stderr.decode()
        
        message += output
        logging.debug(message)
        return (process.returncode, output)
    else:
        stderr = stderr.decode()
        logging.error(f"return code '{process.returncode}':\n{stderr}")
        return (process.returncode, stderr)

async def collect_tasks(tasks: list[Task]) -> list[Future]:
    return await asyncio.gather(*tasks)

def encode_lossy_cli(args: type[Namespace]) -> None:
    '''Parse each path mapping entry into an encoding operation.'''
    path_mappings = common.collect_paths(args.input)
    path_mappings = common.add_output_path(args.output, path_mappings, args.input)
    return encode_lossy(path_mappings, args.extension)

def encode_lossy(path_mappings: list[tuple[str, str]], extension: str, threads: int = 4) -> None:
    tasks: list[Task[tuple[int, str]]] = []
    loop = asyncio.get_event_loop()
    
    for mapping in path_mappings:
        source, dest = mapping[0], mapping[1]
        dest = os.path.splitext(dest)[0] + extension
        
        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir):
            logging.debug(f"create path: '{dest_dir}'")
            os.makedirs(dest_dir)
        
        if os.path.exists(dest):
            logging.debug(f"path exists, skipping: '{dest}'")
            continue
        
        ffprobe_data = read_ffprobe_json(source)
        cover_stream = guess_cover_stream_specifier(ffprobe_data)
        map_options = f"-map 0:0"
        if cover_stream > -1:
            logging.debug(f"guessed cover image in stream: {cover_stream}")
            map_options += f" -map 0:{cover_stream}"
        else:
            logging.info(f"no cover image found for '{source}'")
            
        command = ffmpeg_mp3(source, dest, map_options=map_options)
        
        # run synchronous 
        # run_command(command)
        
        task = loop.create_task(run_command_async(command))
        tasks.append(task)
        logging.debug(f"add task: {len(tasks)}")
        if len(tasks) > threads - 1:
            run_tasks = tasks.copy()
            loop.run_until_complete(collect_tasks(run_tasks))
            logging.debug(f"ran {len(run_tasks)} tasks")
            tasks.clear()
    if tasks:
        run_tasks = tasks.copy()
        loop.run_until_complete(collect_tasks(run_tasks))
        logging.debug(f"ran {len(tasks)} tasks")
        tasks.clear()

class CommandOutput:
    def __init__(self, task: Task, return_code: int, output: str) -> None:
        self.task = task
        self.return_code = return_code
        self.output = output

class CommandTask:
    def __init__(self, command: str, output: CommandOutput) -> None:
        self.command = command
        self.output = output

# TODO: change complex type into a class
def run_missing_art_tasks(loop: AbstractEventLoop, tasks: list[tuple[str, Task[tuple[int, str]]]], output_path: str):
    import json
    
    run_tasks = [task[1] for task in tasks]
    loop.run_until_complete(collect_tasks(run_tasks))
    logging.debug(f"ran {len(run_tasks)} tasks")
    
    for i, task in enumerate(run_tasks):
        source = tasks[i][0]
        output = json.loads(task.result()[1])['streams']    
        cover_stream = guess_cover_stream_specifier(output)
    
        if cover_stream > -1:
            logging.info(f"guessed cover image in stream: {cover_stream}")
        else:
            logging.info(f"no cover image found for '{source}'")
            with open(output_path, 'a', encoding='utf-8') as file:
                file.write(f"{os.path.basename(source)}\n")
    tasks.clear()

def find_missing_art(collection_file_path: str, output_path: str, collection_xpath: str, playlist_xpath: str, threads=24):
    import organize_library_dates as library
    
    # clear the output file
    with open(output_path, 'w', encoding='utf-8'):
        pass
    
    collection = library.find_node(collection_file_path, collection_xpath)
    playlist = library.find_node(collection_file_path, playlist_xpath)
    
    # collect the playlist IDs
    tasks: list[tuple[str, Task[tuple[int, str]]]] = []
    playlist_ids: set[str] = set(track.attrib[constants.ATTR_KEY] for track in playlist)
    
    loop = asyncio.get_event_loop()
    for node in collection:
        # check if node is in playlist
        source = library.collection_path_to_syspath(node.attrib[constants.ATTR_PATH])
        if playlist_ids and node.attrib[constants.ATTR_TRACK_ID] not in playlist_ids:
            logging.info(f"skip non-playlist track: '{source}'")
            continue
        
        task = loop.create_task(run_command_async(command_ffprobe_json(source)))
        tasks.append((source, task))
        logging.debug(f"add task: {len(tasks)}")
        if len(tasks) > threads - 1:
            run_missing_art_tasks(loop, tasks, output_path)
    
    # run remaining tasks
    run_missing_art_tasks(loop, tasks, output_path)

# Main
if __name__ == '__main__':
    common.configure_log(level=logging.DEBUG)
    script_args = parse_args(Namespace.FUNCTIONS)
    
    if script_args.function == Namespace.FUNCTION_LOSSLESS:
        encode_lossless(script_args)
    elif script_args.function == Namespace.FUNCTION_LOSSY:
        encode_lossy_cli(script_args)
    elif script_args.function == Namespace.FUNCTION_MISSING_ART:
        # TODO: add timing
        find_missing_art(script_args.input, script_args.output, constants.XPATH_COLLECTION, constants.XPATH_PRUNED, threads=72)
            
            
