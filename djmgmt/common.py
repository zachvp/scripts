import logging
import os

def configure_log(python_filename: str) -> None:
    '''Standard log configuration.'''
    filename = os.path.splitext(os.path.basename(python_filename))[0]
    logging.basicConfig(filename=f"logs/{filename}.log",
                        level=logging.DEBUG,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%D %H:%M:%S")