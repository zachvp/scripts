import unittest
import zipfile
import os
import shutil
from typing import Any, Tuple

import batch_operations_music

# Constants
INPUT_DIR = 'test_input'
OUTPUT_DIR = 'test_output'
DUMMY_DATA = b'<dummy_data>'

# Helpers
def create_zip_archive(path: str, files: dict[str, Any]) -> None:
    '''Simulates how an automated script typically compresses a zip: writing to the archive root.'''
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    with zipfile.ZipFile(path, 'w') as archive:
        for name, content in files.items():
            archive.writestr(name, content)

def create_zip_with_archive_name(folder_path, zip_path):
    '''Simulates how an OS typically compresses a zip.
    E.g. A MacOS User right-clicks a folder in Finder and selects the 'Compress' action.'''
    with zipfile.ZipFile(zip_path, 'w') as archive:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, os.path.dirname(folder_path))
                archive.write(full_path, arcname=rel_path) # Use folder name as archive name
    # For testing purposes, the original folder should always be deleted.
    shutil.rmtree(folder_path)

def create_files(dir_path: str, files: dict[str, Any]) -> None:
    for file, content in files.items():
        full_path = os.path.join(dir_path, file)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(content)
            
def get_input_output_paths(filename: str) -> Tuple[str, str]:
    '''Returns tuple of input, output paths.'''
    return f"{INPUT_DIR}/{filename}", f"{OUTPUT_DIR}/{filename}"

def clear_directory(path):
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)

# Primary test class
class TestSweepMusic(unittest.TestCase):
    def setUp(self) -> None:
        if not os.path.exists(INPUT_DIR):
            os.makedirs(INPUT_DIR)
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
    
    def tearDown(self) -> None:
        if os.path.exists(INPUT_DIR):
            shutil.rmtree(INPUT_DIR)
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
    
    def test_sweep_beatport_archive(self) -> None:
        '''Test that a Beatport zip archive is swept to the output directory.'''
        input_path, output_path = get_input_output_paths('beatport_tracks.zip')
        create_zip_archive(input_path, { 'file_0.aiff': DUMMY_DATA })
        
        batch_operations_music.sweep(INPUT_DIR, OUTPUT_DIR, False, batch_operations_music.EXTENSIONS, batch_operations_music.PREFIX_HINTS)
        self.assertTrue(os.path.exists(output_path), 'Beatport archive not present in output directory.')
        
    def test_sweep_juno_archive(self) -> None:
        '''Test that a Juno zip archive is swept to the output directory.'''
        input_path, output_path = get_input_output_paths('juno_download.zip')
        create_zip_archive(input_path, { 'file_0.aiff': DUMMY_DATA })
        
        batch_operations_music.sweep(INPUT_DIR, OUTPUT_DIR, False, batch_operations_music.EXTENSIONS, batch_operations_music.PREFIX_HINTS)
        self.assertTrue(os.path.exists(output_path), 'Juno archive not present in output directory.')
    
    def test_sweep_music_archive(self) -> None:
        '''Test that a zip containing only music files is swept to the output directory.'''
        input_path, output_path = get_input_output_paths('music_archive.zip')
        create_zip_archive(input_path, { 'file_0.aiff': DUMMY_DATA })
        
        batch_operations_music.sweep(INPUT_DIR, OUTPUT_DIR, False, batch_operations_music.EXTENSIONS, batch_operations_music.PREFIX_HINTS)
        self.assertTrue(os.path.exists(output_path), 'Music archive not present in output directory.')
    
    def test_sweep_album_archive(self) -> None:
        '''Test that a zip containing music files and a cover photo is swept to the output directory.'''
        input_path, output_path = get_input_output_paths('album.zip')
        create_zip_archive(input_path, { 'cover.jpg': DUMMY_DATA, 'file_0.aiff': DUMMY_DATA })
        
        batch_operations_music.sweep(INPUT_DIR, OUTPUT_DIR, False, batch_operations_music.EXTENSIONS, batch_operations_music.PREFIX_HINTS)
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
        create_files(INPUT_DIR, files)
        
        batch_operations_music.sweep(INPUT_DIR, OUTPUT_DIR, False, batch_operations_music.EXTENSIONS, batch_operations_music.PREFIX_HINTS)
        for f in files:
            expected_path = f"{OUTPUT_DIR}/{f}"
            self.assertTrue(os.path.exists(expected_path), f"The expected path '{expected_path}' does not exist in output directory.")
    
    def test_no_sweep_non_music_files(self) -> None:
        '''Test that loose, non-music files are not swept.'''
        files = {
            'track_0.foo' : DUMMY_DATA,
            'img_0.jpg'   : DUMMY_DATA,
            'img_1.jpeg'  : DUMMY_DATA,
            'img_2.png'   : DUMMY_DATA,
        }
        create_files(INPUT_DIR, files)
        
        batch_operations_music.sweep(INPUT_DIR, OUTPUT_DIR, False, batch_operations_music.EXTENSIONS, batch_operations_music.PREFIX_HINTS)
        for f in files:
            unexpected_path = f"{OUTPUT_DIR}/{f}"
            self.assertFalse(os.path.exists(unexpected_path), f"The unexpected path '{unexpected_path}' should not exist in output directory.")

# Primary test class
class TestFlatten(unittest.TestCase):
    def setUp(self) -> None:
        if not os.path.exists(INPUT_DIR):
            os.makedirs(INPUT_DIR)
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
    
    def tearDown(self) -> None:
        if os.path.exists(INPUT_DIR):
            shutil.rmtree(INPUT_DIR)
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
    
    def test_loose_files(self) -> None:
        '''Tests that all loose files at the input root are flattened to output.'''
        files = {
            'file_0.foo': DUMMY_DATA,
            'file_1.foo': DUMMY_DATA,
            'file_2.foo': DUMMY_DATA,
        }
        create_files(INPUT_DIR, files)
        
        batch_operations_music.flatten_hierarchy(INPUT_DIR, OUTPUT_DIR, False)
        self.assertEqual(len(os.listdir(OUTPUT_DIR)), len(files), "Unexpected number of files in output directory.")
        for f in files:
            expected_path = f"{OUTPUT_DIR}/{f}"
            self.assertTrue(os.path.exists(expected_path), f"The expected path '{expected_path}' does not exist in output directory.")
    
    def test_folder_files(self) -> None:
        '''Tests that all files in subfolders are flattened to output.'''
        files = {
            'folder_0/file_0.foo': DUMMY_DATA,
            'folder_1/file_1.foo': DUMMY_DATA,
            'folder_2/file_2.foo': DUMMY_DATA,
            'folder_3/subfolder/subfolder_file_0.foo' : DUMMY_DATA
        }
        create_files(INPUT_DIR, files)
        
        batch_operations_music.flatten_hierarchy(INPUT_DIR, OUTPUT_DIR, False)
        self.assertEqual(len(os.listdir(OUTPUT_DIR)), len(files), "Unexpected number of files in output directory.")
        for f in files:
            expected_path = f"{OUTPUT_DIR}/{os.path.basename(f)}"
            self.assertTrue(os.path.exists(expected_path), f"The expected path '{expected_path}' does not exist in output directory.")
    
    def test_zip_files(self) -> None:
        '''Tests that all files in zip folders are flattened to output.'''
        files = {
            'file_0.foo': DUMMY_DATA,
            'file_1.foo': DUMMY_DATA,
            'file_2.foo': DUMMY_DATA,
        }
        create_zip_archive(f"{INPUT_DIR}/archive.zip", files)
        
        batch_operations_music.flatten_hierarchy(INPUT_DIR, OUTPUT_DIR, False)
        self.assertEqual(len(os.listdir(OUTPUT_DIR)), len(files), "Unexpected number of files in output directory.")
        for f in files:
            expected_path = f"{OUTPUT_DIR}/{os.path.basename(f)}"
            self.assertTrue(os.path.exists(expected_path), f"The expected path '{expected_path}' does not exist in output directory.")
    
    def test_nested_zip_files(self) -> None:
        '''Tests that a zip archive in a subfolder is flattened to output.'''
        files = {
            'file_0.foo': DUMMY_DATA,
            'file_1.foo': DUMMY_DATA,
            'file_2.foo': DUMMY_DATA,
        }
        create_zip_archive(f"{INPUT_DIR}/subfolder/archive.zip", files)
        
        batch_operations_music.flatten_hierarchy(INPUT_DIR, OUTPUT_DIR, False)
        self.assertEqual(len(os.listdir(OUTPUT_DIR)), len(files), "Unexpected number of files in output directory.")
        for f in files:
            expected_path = f"{OUTPUT_DIR}/{os.path.basename(f)}"
            self.assertTrue(os.path.exists(expected_path), f"The expected path '{expected_path}' does not exist in output directory.")
    
    def test_zip_files_archive_name(self) -> None:
        '''Tests that a zip archive created from a folder with an archive name is flattened to output.'''
        files = {
            'folder_0/file_0.foo': DUMMY_DATA
        }
        create_files(INPUT_DIR, files)
        create_zip_with_archive_name(f"{INPUT_DIR}/folder_0", f"{INPUT_DIR}/folder_0.zip")
        
        batch_operations_music.flatten_hierarchy(INPUT_DIR, OUTPUT_DIR, False)
        self.assertEqual(len(os.listdir(OUTPUT_DIR)), len(files), "Unexpected number of files in output directory.")
        for f in files:
            expected_path = f"{OUTPUT_DIR}/{os.path.basename(f)}"
            self.assertTrue(os.path.exists(expected_path), f"The expected path '{expected_path}' does not exist in output directory.")
        

if __name__ == "__main__":
    unittest.main()