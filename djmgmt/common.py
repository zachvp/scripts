import logging
import os
import constants

def configure_log(python_filename: str) -> None:
    '''Standard log configuration.'''
    filename = os.path.splitext(os.path.basename(python_filename))[0]
    logging.basicConfig(filename=f"logs/{filename}.log",
                        level=logging.DEBUG,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%D %H:%M:%S")

def collect_paths(root: str) -> list[str]:
    '''Returns the paths of all files for the given root.'''
    paths: list[str] = []
    for working_dir, _, names in os.walk(root):
        for name in names:
            if name.startswith('.'):
                continue
            paths.append(os.path.join(working_dir, name))
    return paths

def add_output_path(output_path, input_paths: list[str], root_input_path: str) -> list[str]:
    '''Adds the given path + filename as the output path for each input path.
    Maintains the path structure relative to the root input path.'''
    paths: list[str] = []
    for input_path in input_paths:
        full_output_path = os.path.join(output_path, os.path.relpath(input_path, root_input_path))
        paths.append(f"{input_path}{constants.FILE_OPERATION_DELIMITER}{full_output_path}")
    return paths

# import sys
# root_input = sys.argv[1]
# paths = collect_paths(root_input)
# print(add_output_path('/Users/zachvp/developer/test-private/data/tracks-output', paths, root_input))