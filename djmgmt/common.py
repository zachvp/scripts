import logging
import os

import constants

def configure_log(level=logging.DEBUG) -> None:
    '''Standard log configuration.'''
    filename = 'scripts'
    logging.basicConfig(filename=f"logs/{filename}.log",
                        level=level,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%D %H:%M:%S",
                        filemode='w')

def collect_paths(root: str) -> list[str]:
    '''Returns the paths of all files for the given root.'''
    paths: list[str] = []
    for working_dir, dirnames, names in os.walk(root):
        for index, directory in enumerate(dirnames):
            if directory.startswith('.'):
                del dirnames[index]
        
        for name in names:
            if name.startswith('.'):
                continue
            paths.append(os.path.join(working_dir, name))
    return paths

def add_output_path(output_path: str, input_paths: list[str], root_input_path: str) -> list[tuple[str, str]]:
    '''Adds the given path + filename as the output path for each input path.
    Maintains the path structure relative to the root input path.'''
    paths: list[tuple[str, str]] = []
    for input_path in input_paths:
        full_output_path = os.path.join(output_path, os.path.relpath(input_path, root_input_path))
        paths.append((input_path, full_output_path))
        
    return paths

def raise_exception(error: Exception):
    logging.exception(error)
    raise error

def find_date_context(path: str) -> str | None:
    '''Extracts the date subpath from the input path.
    Example path: '/data/tracks-output/2022/04 april/24/1-Gloria_Jones_-_Tainted_Love_(single_version).mp3'
    Example output: '2022/04 april/24'
    '''
    # Edge case: '/Users/zachvp/developer/test-private/data/tracks-output/2024/08 august/18/Paolo Mojo/1983/159678_1983_(Eric_Prydz_Remix).aiff'
    components = path.split(os.sep)
    found: dict[str, int] = {}
    context: list[str] = []
    
    for i, component in enumerate(components):
        if 'y' not in found and len(component) == 4 and component.isdecimal():
            found['y'] = i
            context.append(component)
        if 'y' in found and found['y'] == i - 1:
            month_label = component.split()
            month_num = month_label[0]
            if len(month_num) == 2 and month_num.isdecimal()\
                and int(month_num) in constants.MAPPING_MONTH and constants.MAPPING_MONTH[int(month_num)] == month_label[1]:
                    found['m'] = i
                    context.append(component)
        if 'm' in found and found['m'] == i - 1:
            if len(component) == 2 and component.isdecimal():
                found['d'] = i
                context.append(component)
    # check for valid date context
    if len(context) != 3:
        return None
    
    return '/'.join(context)

# Development
def dev_testing():
    pass
    # print(find_date_context('/data/tracks-output/2022/04 april/24/1-Gloria_Jones_-_Tainted_Love_(single_version).mp3', ''))

# dev_testing()
    