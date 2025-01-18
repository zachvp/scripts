'''
Uses a combination of audio file metadata to determine duplicates
'''

import os
import argparse
import common_tags

def log_duplicates(root: str) -> None:
    # script state
    file_set: set[str] = set()

    # script process
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            # skip hidden files
            if name[0] == '.':
                continue

            # build full filepath
            path = os.path.join(dirpath, name)

            # load track tags, check for errors
            tags = common_tags.read_tags(path)
            if not tags:
                continue

            # set item = concatenation of track title & artist
            item = f"{tags.artist}{tags.title}".lower()

            # check for duplicates based on set contents
            # before and after insertion
            count = len(file_set)

            file_set.add(item)
            if len(file_set) == count:
                logging.info(path)

if __name__ == '__main__':
    import common
    import logging
    
    common.configure_log(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='The path to the search directory root.')

    script_args = parser.parse_args()
    script_args.input = os.path.normpath(script_args.input)

    log_duplicates(script_args.input)

    # DEV investigation:
    # printed = dev_print_relevant_values(track, relevant_keys)
    # sorted_dict = dict(sorted(printed.items(), key=lambda item: item[0]))
    # for p in sorted_dict:
        # print(f"{p} -> {', '.join(sorted(printed[p]))}")
