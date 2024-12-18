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

import common
import constants

def ffmpeg_base(input_path: str, output_path: str, options: str) -> list[str]:
    all_options = f"-ar 44100 -map 0 -write_id3v2 1 {options}"
    return ['ffmpeg', '-i', input_path] + shlex.split(all_options) + [output_path]

def ffmpeg_standardize(input_path: str, output_path: str) -> list[str]:
    '''Returns a list of ffmpeg command line arguments that will encode the `input_path` to the `output_path`.
    Core command:
        ffmpeg -i /path/to/input.foo -ar 44100 -c:a pcm_s16be -write_id3v2 1 -y path/to/output.bar
        ffmpeg options: 44100 Hz sample rate, decode audio stream, 16-bit PCM big-endian, write ID3V2 tags
    '''
    options = '-c:a pcm_s16be'

    return ffmpeg_base(input_path, output_path, options)

def ffmpeg_mp3(input_path: str, output_path: str) -> list[str]: # todo: use shlex.quote()
    options = '-b:a 320k'
    return ffmpeg_base(input_path, output_path, options)

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
            logging.debug(f"read_ffprobe_value: {command}")
        value = subprocess.run(command, check=True, capture_output=True, encoding='utf-8').stdout.strip()
        if args.verbose:
            logging.debug(f"read_ffprobe_value: {value}")
        return value
    except subprocess.CalledProcessError as error:
        logging.error(f"fatal: read_ffprobe_value: CalledProcessError:\n{error.stderr.strip()}")
        logging.debug(f"command: {shlex.join(command)}")
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
    logging.debug(f"set up store path: {store_path}")

    return store_path

def encode_lossless(args: argparse.Namespace) -> None:
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

def encode_lossy_cli(args: argparse.Namespace) -> None:
    '''Parse each path mapping entry into an encoding operation.'''
    path_mappings = common.collect_paths(args.input)
    path_mappings = common.add_output_path(args.output, path_mappings, args.input)
    return encode_lossy(path_mappings, args.extension)

def run_command(command: list[str]) -> None:
    try:
        logging.debug(f"run command: {shlex.join(command)}")
        subprocess.run(command, check=True, capture_output=True, encoding='utf-8')
        logging.debug(f"command success")
    except subprocess.CalledProcessError as error:
        logging.error(f"return code '{error.returncode}':\n{error.stderr.strip()}")

# todo: extend to encode multiple files at a time
def encode_lossy(path_mappings: list[str], extension: str) -> None:
    tasks = []
    loop = asyncio.get_event_loop()
    
    for mapping in path_mappings:
        source, dest = mapping.split(constants.FILE_OPERATION_DELIMITER)
        dest = os.path.splitext(dest)[0] + extension
        
        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir):
            logging.debug(f"create path: '{dest_dir}'")
            os.makedirs(dest_dir)
        
        if os.path.exists(dest):
            logging.debug(f"path exists, skipping: '{dest}'")
            continue
        command = ffmpeg_mp3(source, dest)
        # thread = threading.Thread(target=run_command, args=[command, source, dest])
        # run_command(command)
        task = loop.create_task(run_command_async(command))
        tasks.append(task)
        print(f"add task: {len(tasks)}")
        logging.debug(f"add task: {len(tasks)}")
        if len(tasks) > 15:
            run_tasks = tasks.copy()
            loop.run_until_complete(collect_tasks(run_tasks))
            print(f"ran {len(run_tasks)} tasks")
            logging.debug(f"ran {len(run_tasks)} tasks")
            tasks.clear()
    if tasks:
        run_tasks = tasks.copy()
        loop.run_until_complete(collect_tasks(run_tasks))
        logging.debug(f"ran {len(tasks)} tasks")
        tasks.clear()
        
        
async def collect_tasks(tasks: list[asyncio.Task]) -> list[asyncio.Future]:
    return await asyncio.gather(*tasks)

async def run_command_async(command: list[str]) -> bool:
    logging.debug(f"run command: {shlex.join(command)}")
    process = await asyncio.create_subprocess_shell(
        shlex.join(command),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    
    # wait for process to finish
    stdout, stderr = await process.communicate()
    if process.returncode == 0:
        message = f"command output:\n"
        if stdout:
            message += stdout.decode()
            logging.debug(message)
        elif stderr:
            message += stderr.decode()
            logging.debug(message)
        return True
    else:
        logging.error(f"return code '{process.returncode}':\n{stderr.decode()}")
    return False                

def process_args(functions: set[str]) -> argparse.Namespace:
    '''Process the script's command line aruments.'''
    parser = argparse.ArgumentParser()
    parser.add_argument('function', type=str, help=f"the function to run; one of: '{functions}'")
    parser.add_argument('input', type=str, help='the input directory to recursively process')
    parser.add_argument('output', type=str, help='the output directory to contain all the files in a flat structure')
    parser.add_argument('extension', type=str, help='the output extension for each file')

    parser.add_argument('--store-path', type=str, help='the script storage path to write to')
    parser.add_argument('--store-skipped', action='store_true', help='store the skipped files in store path')
    parser.add_argument('--interactive', '-i', action='store_true', help='run the script in interactive mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='run the script with verbose output')

    args = parser.parse_args()
    
    if args.function not in functions:
        parser.error(f"invalid function '{args.function}', expect one of: '{functions}'")

    if args.store_skipped and not args.store_path:
        parser.error("if option '--store-skipped' is set, option '--store-path' is required")

    return args

# Main
if __name__ == '__main__':
    FUNCTION_LOSSLESS = 'lossless'
    FUNCTION_LOSSY = 'lossy'
    FUNCTIONS = {FUNCTION_LOSSLESS, FUNCTION_LOSSY}
    
    # testing
    async def wrapper():
        source = "/Users/zachvp/developer/test-private/data/tracks/2020/03 march/21/album/artist/2pole - Atom (Original Mix).aiff"
        dest = "/Users/zachvp/developer/test-private/data/tracks-output/2020/03 march/21/album/artist/2pole - Atom (Original Mix).mp3"
        command = ffmpeg_mp3(source, dest)
        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        # process_0 = asyncio.run(run_command_async(command))
        loop = asyncio.get_event_loop()
        task_command_0 = loop.create_task(run_command_async(command))
        
        source = '/Users/zachvp/developer/test-private/data/tracks/2021/03 march/07/01 Crystal.aiff'
        dest = '/Users/zachvp/developer/test-private/data/tracks-output/2021/03 march/07/01 Crystal.mp3'
        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        command = ffmpeg_mp3(source, dest)
        task_command_1 = loop.create_task(run_command_async(command))
        
        await asyncio.gather(task_command_0, task_command_1)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(wrapper())
    # asyncio.run(handle_process(process_0))
    
    exit()
    

    process_1 = asyncio.run(run_command_async(command))
    # print(process.returncode)
    
    
    
    processes = [process_0, process_1]
    # if processes:
    #     result = asyncio.run(handle_process(processes[0]))
    #     print(f"result: {result}")
    
    exit()
    args = process_args(FUNCTIONS)
    
    if args.function == FUNCTION_LOSSLESS:
        encode_lossless(args)
    elif args.function == FUNCTION_LOSSY:
        encode_lossy_cli(args)
