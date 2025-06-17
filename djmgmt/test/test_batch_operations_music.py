import unittest
import zipfile
import os
import shutil
from typing import Any, Tuple
from argparse import Namespace
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock, call

from src import batch_operations_music
from src import batch_operations_music
from src.common_tags import Tags

# Constants
INPUT_DIR = 'test_input'
OUTPUT_DIR = 'test_output'
DUMMY_DATA = b'<dummy_data>'


MOCK_INPUT_DIR = '/mock/input'
MOCK_XML_FILE_PATH = '/mock/xml/file.xml'
MOCK_ARTIST = 'mock_artist'
MOCK_ALBUM = 'mock_album'
MOCK_TITLE = 'mock_title'

COLLECTION_XML = f'''
<?xml version="1.0" encoding="UTF-8"?>

<DJ_PLAYLISTS Version="1.0.0">
  <PRODUCT Name="rekordbox" Version="6.8.5" Company="AlphaTheta"/>
  <COLLECTION Entries="1">
    <TRACK
        TrackID="1"
        Name="{MOCK_TITLE}"
        Artist="{MOCK_ARTIST}"
        Album="{MOCK_ALBUM}"
        DateAdded="2020-02-03"
        Location="file://localhost/Users/user/Music/DJ/MOCK_FILE.aiff">
    </TRACK>
  </COLLECTION>
</DJ_PLAYLISTS>
'''.strip()

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
        
class TestPruneNonMusicFiles(unittest.TestCase):
    @patch('shutil.rmtree')
    @patch('os.remove')
    @patch('os.walk')
    def test_success_remove_non_music(self,
                                      mock_os_walk: MagicMock,
                                      mock_os_remove: MagicMock,
                                      mock_rmtree: MagicMock) -> None:
        '''Tests that non-music files are removed.'''
        # Setup mocks
        mock_walk_data = [
            ('/mock/source', ['mock/dir/0'], ['mock_file.foo'])
        ]
        mock_os_walk.return_value = mock_walk_data
        
        # Call target function and assert expectations
        batch_operations_music.prune_non_music('/mock/source/', batch_operations_music.EXTENSIONS, False)
        
        mock_os_walk.assert_called()
        mock_os_remove.assert_called_once_with('/mock/source/mock_file.foo')
        mock_rmtree.assert_not_called()
    
    @patch('shutil.rmtree')
    @patch('os.remove')
    @patch('os.walk')
    def test_success_skip_music(self,
                                mock_os_walk: MagicMock,
                                mock_os_remove: MagicMock,
                                mock_rmtree: MagicMock) -> None:
        '''Tests that music files are not removed.'''
        # Setup mocks
        mock_walk_data = [
            ('/mock/source', ['mock/dir/0'], ['mock_music.mp3'])
        ]
        mock_os_walk.return_value = mock_walk_data
        
        # Call target function and assert expectations
        batch_operations_music.prune_non_music('/mock/source/', batch_operations_music.EXTENSIONS, False)
        
        mock_os_walk.assert_called()
        mock_os_remove.assert_not_called()
        mock_rmtree.assert_not_called()
    
    @patch('shutil.rmtree')
    @patch('os.remove')
    @patch('os.walk')
    def test_success_skip_music_subdirectory(self,
                                             mock_os_walk: MagicMock,
                                             mock_os_remove: MagicMock,
                                             mock_rmtree: MagicMock) -> None:
        '''Tests that nested music files are not removed.'''
        # Setup mocks
        mock_walk_data = [
            ('/mock/source', ['mock/dir/0'], []),
            ('/mock/source/mock/dir/0', [], ['mock_music.mp3'])
        ]
        mock_os_walk.return_value = mock_walk_data
        
        # Call target function and assert expectations
        batch_operations_music.prune_non_music('/mock/source/', batch_operations_music.EXTENSIONS, False)
        
        mock_os_walk.assert_called()
        mock_os_remove.assert_not_called()
        mock_rmtree.assert_not_called()
    
    @patch('shutil.rmtree')
    @patch('os.remove')
    @patch('os.walk')
    def test_success_remove_non_music_subdirectory(self,
                                                   mock_os_walk: MagicMock,
                                                   mock_os_remove: MagicMock,
                                                   mock_rmtree: MagicMock) -> None:
        '''Tests that nested non-music files are removed.'''
        # Setup mocks
        mock_walk_data = [
            ('/mock/source', ['mock/dir/0'], []),
            ('/mock/source/mock/dir/0', [], ['mock_music.foo'])
        ]
        mock_os_walk.return_value = mock_walk_data
        
        # Call target function and assert expectations
        batch_operations_music.prune_non_music('/mock/source/', batch_operations_music.EXTENSIONS, False)
        
        mock_os_walk.assert_called()
        mock_os_remove.assert_called_once_with('/mock/source/mock/dir/0/mock_music.foo')
        mock_rmtree.assert_not_called()
    
    @patch('shutil.rmtree')
    @patch('os.remove')
    @patch('os.walk')
    def test_success_remove_hidden_file(self,
                                        mock_os_walk: MagicMock,
                                        mock_os_remove: MagicMock,
                                        mock_rmtree: MagicMock) -> None:
        '''Tests that hidden files are removed.'''
        # Setup mocks
        mock_walk_data = [
            ('/mock/source', ['mock/dir/0'], ['.mock_hidden'])
        ]
        mock_os_walk.return_value = mock_walk_data
        
        # Call target function and assert expectations
        batch_operations_music.prune_non_music('/mock/source/', batch_operations_music.EXTENSIONS, False)
        
        mock_os_walk.assert_called()
        mock_os_remove.assert_called_once_with('/mock/source/.mock_hidden')
        mock_rmtree.assert_not_called()
    
    @patch('shutil.rmtree')
    @patch('os.remove')
    @patch('os.walk')
    def test_success_remove_zip_archive(self,
                                        mock_os_walk: MagicMock,
                                        mock_os_remove: MagicMock,
                                        mock_rmtree: MagicMock) -> None:
        '''Tests that zip archives are removed.'''
        # Setup mocks
        mock_walk_data = [
            ('/mock/source', ['mock/dir/0'], ['mock.zip'])
        ]
        mock_os_walk.return_value = mock_walk_data
        
        # Call target function and assert expectations
        batch_operations_music.prune_non_music('/mock/source/', batch_operations_music.EXTENSIONS, False)
        
        mock_os_walk.assert_called()
        mock_os_remove.assert_called_once_with('/mock/source/mock.zip')
        mock_rmtree.assert_not_called()
    
    @patch('shutil.rmtree')
    @patch('os.remove')
    @patch('os.walk')
    def test_success_remove_app(self,
                                mock_os_walk: MagicMock,
                                mock_os_remove: MagicMock,
                                mock_rmtree: MagicMock) -> None:
        '''Tests that .app archives are removed.'''
        # Setup mocks
        mock_walk_data = [
            ('/mock/source', ['mock/dir/0'], ['mock.app'])
        ]
        mock_os_walk.return_value = mock_walk_data
        
        # Call target function and assert expectations
        batch_operations_music.prune_non_music('/mock/source/', batch_operations_music.EXTENSIONS, False)
        
        mock_os_walk.assert_called()
        mock_os_remove.assert_not_called()
        mock_rmtree.assert_called_once_with('/mock/source/mock.app')
    
    @patch('shutil.rmtree')
    @patch('os.remove')
    @patch('os.walk')
    def test_success_skip_music_hidden_dir(self,
                                           mock_os_walk: MagicMock,
                                           mock_os_remove: MagicMock,
                                           mock_rmtree: MagicMock) -> None:
        '''Tests that music files in a hidden directory are not removed.'''
        # Setup mocks
        mock_walk_data = [
            ('/mock/source/mock/', ['.mock_hidden_dir'], []),
            ('/mock/source/mock/.mock_hidden_dir', [], ['mock_music.mp3'])
        ]
        mock_os_walk.return_value = mock_walk_data
        
        # Call target function and assert expectations
        batch_operations_music.prune_non_music('/mock/source/', batch_operations_music.EXTENSIONS, False)
        
        mock_os_walk.assert_called()
        mock_os_remove.assert_not_called()
        mock_rmtree.assert_not_called()
    
    @patch('shutil.rmtree')
    @patch('os.remove')
    @patch('os.walk')
    def test_success_remove_non_music_hidden_dir(self,
                                                 mock_os_walk: MagicMock,
                                                 mock_os_remove: MagicMock,
                                                 mock_rmtree: MagicMock) -> None:
        '''Tests that non-music files in a hidden directory are removed.'''
        # Setup mocks
        mock_walk_data = [
            ('/mock/source/', ['.mock_hidden_dir'], []),
            ('/mock/source/.mock_hidden_dir', [], ['mock.foo'])
        ]
        mock_os_walk.return_value = mock_walk_data
        
        # Call target function and assert expectations
        batch_operations_music.prune_non_music('/mock/source/', batch_operations_music.EXTENSIONS, False)
        
        mock_os_walk.assert_called()
        mock_os_remove.assert_called_once_with('/mock/source/.mock_hidden_dir/mock.foo')
        mock_rmtree.assert_not_called()
        
    @patch('batch_operations_music.prune_non_music')
    def test_success_cli(self, mock_prune_non_music: MagicMock) -> None:
        '''Tests that the CLI wrapper function exists and is called properly.'''
        import inspect
        
        # Assert that the expected function exists
        self.assertTrue(inspect.isfunction(getattr(batch_operations_music, 'prune_non_music_cli', None)), 'Expected function does not exist')
        
        # Call target function and assert expectations
        mock_namespace = Namespace(input='/mock/input/', output='/mock/output/', interactive=False)
        batch_operations_music.prune_non_music_cli(mock_namespace, set())  # type: ignore
        
        mock_prune_non_music.assert_called_once_with(mock_namespace.input, set(), mock_namespace.interactive)
    
    @patch('shutil.rmtree')
    @patch('builtins.input')
    @patch('os.remove')
    @patch('os.walk')
    def test_success_interactive_skip(self,
                                      mock_os_walk: MagicMock,
                                      mock_os_remove: MagicMock,
                                      mock_input: MagicMock,
                                      mock_rmtree: MagicMock) -> None:
        '''Tests that an interactive prune prompts the user to remove the non-music file and skips removal.'''
        # Setup mocks
        mock_walk_data = [
            ('/mock/source', ['mock/dir/0'], ['mock_file.foo'])
        ]
        mock_os_walk.return_value = mock_walk_data
        mock_input.return_value = 'N'
        
        # Call target function and assert expectations
        batch_operations_music.prune_non_music('/mock/source/', batch_operations_music.EXTENSIONS, True)
        
        mock_os_walk.assert_called()
        mock_input.assert_called()
        mock_os_remove.assert_not_called()
        mock_rmtree.assert_not_called()
        
    @patch('shutil.rmtree')
    @patch('builtins.input')
    @patch('os.remove')
    @patch('os.walk')
    def test_success_interactive_remove(self,
                                        mock_os_walk: MagicMock,
                                        mock_os_remove: MagicMock,
                                        mock_input: MagicMock,
                                        mock_rmtree: MagicMock) -> None:
        '''Tests that an interactive prune prompts the user to remove the non-music file and performs removal.'''
        # Setup mocks
        mock_walk_data = [
            ('/mock/source', ['mock/dir/0'], ['mock_file.foo'])
        ]
        mock_os_walk.return_value = mock_walk_data
        mock_input.return_value = 'y'
        
        # Call target function and assert expectations        
        batch_operations_music.prune_non_music('/mock/source/', batch_operations_music.EXTENSIONS, True)
        
        mock_os_walk.assert_called()
        mock_input.assert_called()
        mock_os_remove.assert_called_once()
        mock_rmtree.assert_not_called()
        
class TestProcess(unittest.TestCase):
    @patch('batch_operations_music.record_collection')
    @patch('batch_operations_music.standardize_lossless')
    @patch('batch_operations_music.prune_non_music')
    @patch('batch_operations_music.prune_empty')
    @patch('batch_operations_music.flatten_hierarchy')
    @patch('batch_operations_music.extract')
    @patch('batch_operations_music.sweep')
    def test_success(self,
                     mock_sweep: MagicMock,
                     mock_extract: MagicMock,
                     mock_flatten: MagicMock,
                     mock_prune_empty: MagicMock,
                     mock_prune_non_music: MagicMock,
                     mock_standardize_lossless: MagicMock,
                     mock_record_collection: MagicMock) -> None:
        '''Tests that the process function calls the expected functions in the the correct order.'''
        # Set up mocks
        mock_call_container = MagicMock()
        mock_sweep.side_effect = lambda *_, **__: mock_call_container.sweep()
        mock_extract.side_effect = lambda *_, **__: mock_call_container.extract()
        mock_flatten.side_effect = lambda *_, **__: mock_call_container.flatten()
        mock_prune_empty.side_effect = lambda *_, **__: mock_call_container.prune_empty()
        mock_prune_non_music.side_effect = lambda *_, **__: mock_call_container.prune_non_music()
        mock_standardize_lossless.side_effect = lambda *_, **__: mock_call_container.standardize_lossless()
        mock_record_collection.side_effect = lambda *_, **__: mock_call_container.record_collection()
        
        # Mock the result of the lossless function
        mock_standardize_lossless.return_value = [
            ('/mock/input/file_0.aif', '/mock/output/file_0.aiff'),
            ('/mock/input/file_1.wav', '/mock/output/file_1.aiff')
        ]
        
        # Call target function
        args = Namespace(input='/mock/input/', output='/mock/output/', interactive=False)
        batch_operations_music.process_cli(args, set(), set()) # type: ignore
        
        # Assert that the primary dependent functions are called in the correct order
        self.assertEqual(mock_call_container.mock_calls[0], call.sweep())
        self.assertEqual(mock_call_container.mock_calls[1], call.extract())
        self.assertEqual(mock_call_container.mock_calls[2], call.flatten())
        self.assertEqual(mock_call_container.mock_calls[3], call.standardize_lossless())
        self.assertEqual(mock_call_container.mock_calls[4], call.prune_non_music())
        self.assertEqual(mock_call_container.mock_calls[5], call.prune_empty())
        self.assertEqual(mock_call_container.mock_calls[6], call.record_collection())
        
        # Assert call counts and parameters
        mock_sweep.assert_called_once()
        mock_extract.assert_called_once()
        mock_flatten.assert_called_once()
        
        mock_standardize_lossless.assert_called_once()
        mock_standardize_lossless.assert_called_once_with(args.output, set(), set(), args.interactive)
        
        mock_record_collection.assert_called_once()
        self.assertEqual(mock_record_collection.call_args[0][0], args.output)
        self.assertRegex(mock_record_collection.call_args[0][1], r'.+\/data\/.+\.xml')

class TestPruneEmpty(unittest.TestCase):
    @patch('shutil.rmtree')
    @patch('batch_operations_music.is_empty_dir')
    @patch('batch_operations_music.get_dirs')
    def test_success_remove_empty_dir(self,
                                      mock_get_dirs: MagicMock,
                                      mock_is_empty_dir: MagicMock,
                                      mock_rmtree: MagicMock) -> None:
        '''Test that prune removes an empty directory.'''
        # Setup mocks
        mock_get_dirs.return_value = ['mock_empty_dir']
        
        # Call target function and assert expectations
        batch_operations_music.prune_empty('/mock/source/', False)
        
        mock_get_dirs.assert_called()
        mock_is_empty_dir.assert_called()
        mock_rmtree.assert_called_once_with('/mock/source/mock_empty_dir')
        
    @patch('shutil.rmtree')
    @patch('batch_operations_music.is_empty_dir')
    @patch('batch_operations_music.get_dirs')
    def test_success_skip_non_empty_dir(self,
                                        mock_get_dirs: MagicMock,
                                        mock_is_empty_dir: MagicMock,
                                        mock_rmtree: MagicMock) -> None:
        '''Test that prune does not remove a non-empty directory.'''
        # Setup mocks
        mock_get_dirs.side_effect = [['mock_non_empty_dir'], []]
        mock_is_empty_dir.return_value = False
        
        # Call target function and assert expectations
        batch_operations_music.prune_empty('/mock/source/', False)
        
        mock_get_dirs.assert_called()
        mock_is_empty_dir.assert_called()
        mock_rmtree.assert_not_called()
        
    @patch('batch_operations_music.prune_empty')
    def test_success_cli(self, mock_prune_empty: MagicMock) -> None:
        '''Tests that the CLI wrapper calls the correct function.'''
        batch_operations_music.prune_empty('/mock/source/', False)
        mock_prune_empty.assert_called_once_with('/mock/source/', False)
        
class TestRecordCollection(unittest.TestCase):
    @patch('batch_operations_music.ET.ElementTree')
    @patch('batch_operations_music.ET.parse')
    @patch('os.path.exists')
    @patch('batch_operations_music.read_tags')
    @patch('os.walk')
    def test_success_file_not_exist(self,
                                    mock_walk: MagicMock,
                                    mock_read_tags: MagicMock,
                                    mock_path_exists: MagicMock, # mock in case implementation uses os API
                                    mock_xml_parse: MagicMock,
                                    mock_xml_tree: MagicMock) -> None:
        '''Tests that a single music file is correctly written to a non-existent XML file.'''
        # Set up mocks
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], ['mock_file.aiff'])]
        mock_read_tags.return_value = Tags(MOCK_ARTIST, MOCK_ALBUM, MOCK_TITLE)
        mock_path_exists.return_value = False
        mock_xml_parse.side_effect = FileNotFoundError() # mock in case implementation catches exception to check for file
        
        # Call the target function
        batch_operations_music.record_collection(MOCK_INPUT_DIR, MOCK_XML_FILE_PATH)
        
        # Assert expectations
        mock_walk.assert_called_once()
        
        # Assert that the function reads the file tags
        FILE_PATH_MUSIC = f"{MOCK_INPUT_DIR}{os.sep}mock_file.aiff"
        mock_read_tags.assert_called_once_with(FILE_PATH_MUSIC)
        
        # Assert that the XML contents are expected
        xml_root: ET.Element  = mock_xml_tree.call_args[0]
        self.assertEqual(len(xml_root), 1)
        
        # Check DJ_PLAYLISTS node
        dj_playlists = xml_root[0]
        self.assertEqual(dj_playlists.tag, 'DJ_PLAYLISTS')
        self.assertEqual(dj_playlists.attrib, {'Version': '1.0.0'})
        self.assertEqual(len(dj_playlists), 2)
        
        # Check PRODUCT node
        product = dj_playlists[0]
        expected_attrib = {'Name': 'rekordbox', 'Version': '6.8.5', 'Company': 'AlphaTheta'}
        self.assertEqual(product.tag, 'PRODUCT')
        self.assertEqual(product.attrib, expected_attrib)
        
        # Check COLLECTION node
        collection = dj_playlists[1]
        self.assertEqual(collection.tag, 'COLLECTION')
        self.assertEqual(collection.attrib, {'Entries': '1'})
        self.assertEqual(len(collection), 1)
        
        # Check TRACK node
        track = collection[0]
        self.assertEqual(track.tag, 'TRACK')
        self.assertEqual(len(track), 0)
        
        self.assertIn('TrackID', track.attrib)
        self.assertRegex(track.attrib['TrackID'], r'\d+')
        
        self.assertIn('Name', track.attrib)
        self.assertEqual(track.attrib['Name'], MOCK_TITLE)
        
        self.assertIn('Artist', track.attrib)
        self.assertEqual(track.attrib['Artist'], MOCK_ARTIST)
        
        self.assertIn('Album', track.attrib)
        self.assertEqual(track.attrib['Album'], MOCK_ALBUM)
        
        self.assertIn('DateAdded', track.attrib)
        self.assertRegex(track.attrib['DateAdded'], r"\d{4}-\d{2}-\d{2}")
        
        self.assertIn('Location', track.attrib)
        self.assertRegex(track.attrib['Location'], r'file://localhost/.+')
                
        # Assert that the function writes to the given XML file
        self.assertIn(call().write(MOCK_XML_FILE_PATH, encoding='UTF-8', xml_declaration=True), mock_xml_tree.mock_calls)

    @patch('batch_operations_music.ET.parse')
    @patch('os.path.exists')
    @patch('batch_operations_music.read_tags')
    @patch('os.walk')
    def test_success_file_exists(self,
                                 mock_walk: MagicMock,
                                 mock_read_tags: MagicMock,
                                 mock_path_exists: MagicMock, # mock in case implementation uses os API
                                 mock_xml_parse: MagicMock) -> None:
        '''Tests that a single music file is correctly written to an existing XML file.'''
        # Set up mocks
        mock_path_exists.return_value = True
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], ['mock_file.aiff'])]
        mock_read_tags.return_value = Tags(MOCK_ARTIST, MOCK_ALBUM, MOCK_TITLE)
        mock_xml_parse.return_value = ET.ElementTree(ET.fromstring(COLLECTION_XML))
        
        # Call the target function
        # Limit the path scope for ElementTree so a real instance can be used in the return value above
        with patch('batch_operations_music.ET.ElementTree') as mock_xml_tree:
            batch_operations_music.record_collection(MOCK_INPUT_DIR, MOCK_XML_FILE_PATH)
            
            # Assert expectations
            mock_walk.assert_called_once()
            mock_xml_parse.assert_called_with(MOCK_XML_FILE_PATH)
            
            # Assert that the function reads the file tags
            FILE_PATH_MUSIC = f"{MOCK_INPUT_DIR}{os.sep}mock_file.aiff"
            mock_read_tags.assert_called_once_with(FILE_PATH_MUSIC)
            
            # Assert that the XML contents are expected
            xml_root: ET.Element  = mock_xml_tree.call_args[0]
            self.assertEqual(len(xml_root), 1)
            
            # Check DJ_PLAYLISTS node
            dj_playlists = xml_root[0]
            self.assertEqual(dj_playlists.tag, 'DJ_PLAYLISTS')
            self.assertEqual(dj_playlists.attrib, {'Version': '1.0.0'})
            self.assertEqual(len(dj_playlists), 2)
            
            # Check PRODUCT node
            product = dj_playlists[0]
            expected_attrib = {'Name': 'rekordbox', 'Version': '6.8.5', 'Company': 'AlphaTheta'}
            self.assertEqual(product.tag, 'PRODUCT')
            self.assertEqual(product.attrib, expected_attrib)
            
            # Check COLLECTION node
            collection = dj_playlists[1]
            self.assertEqual(collection.tag, 'COLLECTION')
            self.assertEqual(collection.attrib, {'Entries': '2'})
            self.assertEqual(len(collection), 2)
            
            # Check TRACK nodes
            for track in collection:
            # track = collection[0]
                self.assertEqual(track.tag, 'TRACK')
                self.assertEqual(len(track), 0)
                
                self.assertIn('TrackID', track.attrib)
                self.assertRegex(track.attrib['TrackID'], r'\d+')
                
                self.assertIn('Name', track.attrib)
                self.assertEqual(track.attrib['Name'], MOCK_TITLE)
                
                self.assertIn('Artist', track.attrib)
                self.assertEqual(track.attrib['Artist'], MOCK_ARTIST)
                
                self.assertIn('Album', track.attrib)
                self.assertEqual(track.attrib['Album'], MOCK_ALBUM)
                
                self.assertIn('DateAdded', track.attrib)
                self.assertRegex(track.attrib['DateAdded'], r"\d{4}-\d{2}-\d{2}")
                
                self.assertIn('Location', track.attrib)
                self.assertRegex(track.attrib['Location'], r'file://localhost/.+')
            
            # Assert that the function writes to the given XML file
            self.assertIn(call().write(MOCK_XML_FILE_PATH, encoding='UTF-8', xml_declaration=True), mock_xml_tree.mock_calls)
    
    @patch('batch_operations_music.ET.ElementTree')
    @patch('batch_operations_music.ET.parse')
    @patch('os.path.exists')
    @patch('batch_operations_music.read_tags')
    @patch('os.walk')
    def test_success_no_music_files(self,
                                    mock_walk: MagicMock,
                                    mock_read_tags: MagicMock,
                                    mock_path_exists: MagicMock, # mock in case implementation uses os API
                                    mock_xml_parse: MagicMock,
                                    mock_xml_tree: MagicMock) -> None:
        '''Tests that either no XML is written or XML content contains no Tracks when no music files are present.'''
        # Setup mocks
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], ['mock_file.foo'])]
        mock_path_exists.return_value = False
        mock_xml_parse.side_effect = FileNotFoundError() # mock in case implementation catches exception to check for file
        
        # Call target function
        batch_operations_music.record_collection(MOCK_INPUT_DIR, MOCK_XML_FILE_PATH)
        
        # Assert expectations
        mock_read_tags.assert_not_called()
        
        # Valid implementation may either write an empty XML doc or write no XML
        if mock_xml_tree.call_count > 0:
            # Check root
            xml_root: ET.Element  = mock_xml_tree.call_args[0]
            self.assertEqual(len(xml_root), 1)
            
            # Check DJ_PLAYLISTS node
            dj_playlists = xml_root[0]
            self.assertEqual(dj_playlists.tag, 'DJ_PLAYLISTS')
            self.assertEqual(dj_playlists.attrib, {'Version': '1.0.0'})
            self.assertEqual(len(dj_playlists), 2)
            
            # Check PRODUCT node
            product = dj_playlists[0]
            expected_attrib = {'Name': 'rekordbox', 'Version': '6.8.5', 'Company': 'AlphaTheta'}
            self.assertEqual(product.tag, 'PRODUCT')
            self.assertEqual(product.attrib, expected_attrib)
            
            # Check COLLECTION node
            collection = dj_playlists[1]
            self.assertEqual(collection.tag, 'COLLECTION')
            self.assertEqual(collection.attrib, {'Entries': '0'})
            self.assertEqual(len(collection), 0)
        else:
            mock_xml_tree.assert_not_called()

if __name__ == "__main__":
    unittest.main()