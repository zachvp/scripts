import unittest
import zipfile
import os
import shutil
from typing import Any, Tuple

import batch_operations_music

# Constants
SWEEP_INPUT_DIR = 'test_sweep_input'
SWEEP_OUTPUT_DIR = 'test_sweep_output'
DUMMY_DATA = b'<dummy_data>'

# Helpers
def createZipArchive(path: str, files: dict[str, Any]):
    with zipfile.ZipFile(path, 'w') as archive:
        for name, content in files.items():
            archive.writestr(name, content)
            
def createFiles(files: dict[str, Any]):
    for path, content in files.items():
        full_path = os.path.join(SWEEP_INPUT_DIR, path)
        os.makedirs(SWEEP_INPUT_DIR, exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(content)

def clear_directory(path):
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
            
def getInputOutputPaths(filename: str) -> Tuple[str, str]:
    '''Returns tuple of input, output paths.'''
    return f"{SWEEP_INPUT_DIR}/{filename}", f"{SWEEP_OUTPUT_DIR}/{filename}"

# Primary test class
class TestSweepMusic(unittest.TestCase):
    def tearDown(self) -> None:
        clear_directory(SWEEP_INPUT_DIR)
        clear_directory(SWEEP_OUTPUT_DIR)
    
    def test_sweep_beatport_archive(self) -> None:
        '''Test that a Beatport zip archive is swept to the output directory.'''
        input_path, output_path = getInputOutputPaths('beatport_tracks.zip')
        createZipArchive(input_path, { 'file_0.aiff': DUMMY_DATA })
        
        batch_operations_music.sweep(SWEEP_INPUT_DIR, SWEEP_OUTPUT_DIR, False, batch_operations_music.EXTENSIONS, batch_operations_music.PREFIX_HINTS)
        self.assertTrue(os.path.exists(output_path), 'Beatport archive not present in output directory.')
        
    def test_sweep_juno_archive(self) -> None:
        '''Test that a Juno zip archive is swept to the output directory.'''
        input_path, output_path = getInputOutputPaths('juno_download.zip')
        createZipArchive(input_path, { 'file_0.aiff': DUMMY_DATA })
        
        batch_operations_music.sweep(SWEEP_INPUT_DIR, SWEEP_OUTPUT_DIR, False, batch_operations_music.EXTENSIONS, batch_operations_music.PREFIX_HINTS)
        self.assertTrue(os.path.exists(output_path), 'Juno archive not present in output directory.')
    
    def test_sweep_music_archive(self) -> None:
        '''Test that a zip containing only music files is swept to the output directory.'''
        input_path, output_path = getInputOutputPaths('music_archive.zip')
        createZipArchive(input_path, { 'file_0.aiff': DUMMY_DATA })
        
        batch_operations_music.sweep(SWEEP_INPUT_DIR, SWEEP_OUTPUT_DIR, False, batch_operations_music.EXTENSIONS, batch_operations_music.PREFIX_HINTS)
        self.assertTrue(os.path.exists(output_path), 'Music archive not present in output directory.')
    
    def test_sweep_album_archive(self) -> None:
        '''Test that a zip containing music files and a cover photo is swept to the output directory.'''
        input_path, output_path = getInputOutputPaths('album.zip')
        createZipArchive(input_path, { 'cover.jpg': DUMMY_DATA, 'file_0.aiff': DUMMY_DATA })
        
        batch_operations_music.sweep(SWEEP_INPUT_DIR, SWEEP_OUTPUT_DIR, False, batch_operations_music.EXTENSIONS, batch_operations_music.PREFIX_HINTS)
        self.assertTrue(os.path.exists(output_path), 'Album archive not present in output directory.')
    
    def test_sweep_music_files(self) -> None:
        '''Test that loose music files are swept.'''
        files = {
            'track_0.mp3'  : DUMMY_DATA,
            'track_1.wav'  : DUMMY_DATA,
            'track_2.aif'  : DUMMY_DATA,
            'track_3.aiff' : DUMMY_DATA,
            'track_4.flac' : DUMMY_DATA,
        }
        createFiles(files)
        
        batch_operations_music.sweep(SWEEP_INPUT_DIR, SWEEP_OUTPUT_DIR, False, batch_operations_music.EXTENSIONS, batch_operations_music.PREFIX_HINTS)
        for f in files:
            expected_path = f"{SWEEP_OUTPUT_DIR}/{f}"
            self.assertTrue(os.path.exists(expected_path), f"The expected path '{expected_path}' does not exist in output directory.")
    
    def test_no_sweep_non_music_files(self) -> None:
        '''Test that loose, non-music files are not swept.'''
        files = {
            'track_0.foo' : DUMMY_DATA,
            'img_0.jpg'   : DUMMY_DATA,
            'img_1.jpeg'  : DUMMY_DATA,
            'img_2.png'   : DUMMY_DATA,
        }
        createFiles(files)
        
        batch_operations_music.sweep(SWEEP_INPUT_DIR, SWEEP_OUTPUT_DIR, False, batch_operations_music.EXTENSIONS, batch_operations_music.PREFIX_HINTS)
        for f in files:
            unexpected_path = f"{SWEEP_OUTPUT_DIR}/{f}"
            self.assertFalse(os.path.exists(unexpected_path), f"The unexpected path '{unexpected_path}' should not exist in output directory.")

if __name__ == "__main__":
    unittest.main()