import unittest
import os
from typing import Tuple, cast
from argparse import Namespace
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock, call

from src import batch_operations_music
from src import batch_operations_music
from src.common_tags import Tags

# Constants
MOCK_INPUT_DIR = '/mock/input'
MOCK_OUTPUT_DIR = '/mock/output'
MOCK_XML_FILE_PATH = '/mock/xml/file.xml'
MOCK_ARTIST = 'mock_artist'
MOCK_ALBUM = 'mock_album'
MOCK_TITLE = 'mock_title'

COLLECTION_XML = f'''
<?xml version="1.0" encoding="UTF-8"?>

<DJ_PLAYLISTS Version="1.0.0">
    <PRODUCT Name="rekordbox" Version="6.8.5" Company="AlphaTheta"/>
    <COLLECTION Entries="1">
    
    </COLLECTION>
    <PLAYLISTS>
        <NODE Type="0" Name="ROOT" Count="2">
            <NODE Name="CUE Analysis Playlist" Type="1" KeyType="0" Entries="0"/>
            <NODE Name="_pruned" Type="1" KeyType="0" Entries="0">
            </NODE>
        </NODE>
    </PLAYLISTS>
</DJ_PLAYLISTS>
'''.strip()

# Helpers
def get_input_output_paths(filename: str) -> Tuple[str, str]:
    '''Returns tuple of input, output paths.'''
    return f"{MOCK_INPUT_DIR}/{filename}", f"{MOCK_OUTPUT_DIR}/{filename}"

# Primary test class
class TestSweepMusic(unittest.TestCase):
    @patch('shutil.move')
    @patch('zipfile.ZipFile')
    @patch('src.batch_operations_music.is_prefix_match')
    @patch('os.path.exists')
    @patch('os.walk')
    def test_sweep_music_files(self,
                                  mock_walk: MagicMock,
                                  mock_path_exists: MagicMock,
                                  mock_is_prefix_match: MagicMock,
                                  mock_zipfile: MagicMock,
                                  mock_move: MagicMock) -> None:
        '''Test that loose music files are swept.'''
        # Set up mocks
        mock_filenames = [f"mock_file{ext}" for ext in batch_operations_music.EXTENSIONS]
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], mock_filenames)]
        mock_path_exists.return_value = False
        mock_is_prefix_match.return_value = False
        
        # Call target function
        batch_operations_music.sweep(MOCK_INPUT_DIR, MOCK_OUTPUT_DIR,
                                     False,
                                     batch_operations_music.EXTENSIONS,
                                     batch_operations_music.PREFIX_HINTS)
        
        # Assert expectations
        mock_walk.assert_called_once_with(MOCK_INPUT_DIR)
        self.assertEqual(mock_path_exists.call_count, len(mock_filenames))
        mock_is_prefix_match.assert_not_called()
        mock_zipfile.assert_not_called()
        mock_move.assert_has_calls([
            call(f"{MOCK_INPUT_DIR}{os.sep}{mock_filenames[i]}",
                 f"{MOCK_OUTPUT_DIR}{os.sep}{mock_filenames[i]}")
            for i in range(len(mock_filenames))
        ])
    
    @patch('shutil.move')
    @patch('zipfile.ZipFile')
    @patch('src.batch_operations_music.is_prefix_match')
    @patch('os.path.exists')
    @patch('os.walk')
    def test_no_sweep_non_music_files(self,
                                  mock_walk: MagicMock,
                                  mock_path_exists: MagicMock,
                                  mock_is_prefix_match: MagicMock,
                                  mock_zipfile: MagicMock,
                                  mock_move: MagicMock) -> None:
        '''Test that loose, non-music files are not swept.'''
        mock_filenames = [
            'track_0.foo',
            'img_0.jpg'  ,
            'img_1.jpeg' ,
            'img_2.png'  ,
        ]
        # Set up mocks
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], mock_filenames)]
        mock_path_exists.return_value = False
        mock_is_prefix_match.return_value = False
        
        # Call target function
        batch_operations_music.sweep(MOCK_INPUT_DIR, MOCK_OUTPUT_DIR,
                                     False,
                                     batch_operations_music.EXTENSIONS,
                                     batch_operations_music.PREFIX_HINTS)
        
        # Assert expectations
        mock_walk.assert_called_once_with(MOCK_INPUT_DIR)
        self.assertEqual(mock_path_exists.call_count, len(mock_filenames))
        mock_is_prefix_match.assert_not_called()
        mock_zipfile.assert_not_called()
        mock_move.assert_not_called()
    
    @patch('shutil.move')
    @patch('zipfile.ZipFile')
    @patch('src.batch_operations_music.is_prefix_match')
    @patch('os.path.exists')
    @patch('os.walk')
    def test_sweep_prefix_archive(self,
                                  mock_walk: MagicMock,
                                  mock_path_exists: MagicMock,
                                  mock_is_prefix_match: MagicMock,
                                  mock_zipfile: MagicMock,
                                  mock_move: MagicMock) -> None:
        '''Test that a prefix zip archive is swept to the output directory.'''
        # Set up mocks
        mock_filename = 'mock_valid_prefix.zip'
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], [mock_filename])]
        mock_path_exists.return_value = False
        mock_is_prefix_match.return_value = True
        
        # Call target function
        batch_operations_music.sweep(MOCK_INPUT_DIR, MOCK_OUTPUT_DIR,
                                     False,
                                     batch_operations_music.EXTENSIONS,
                                     batch_operations_music.PREFIX_HINTS)
        
        # Assert expectations
        mock_walk.assert_called_once_with(MOCK_INPUT_DIR)
        mock_path_exists.assert_called_once_with(f"{MOCK_OUTPUT_DIR}{os.sep}{mock_filename}")
        mock_is_prefix_match.assert_called_once_with(mock_filename, batch_operations_music.PREFIX_HINTS)
        mock_zipfile.assert_not_called()
        mock_move.assert_called_once_with(f"{MOCK_INPUT_DIR}{os.sep}{mock_filename}",
                                          f"{MOCK_OUTPUT_DIR}{os.sep}{mock_filename}")

    @patch('shutil.move')
    @patch('zipfile.ZipFile')
    @patch('src.batch_operations_music.is_prefix_match')
    @patch('os.path.exists')
    @patch('os.walk')
    def test_sweep_music_archive(self,
                                 mock_walk: MagicMock,
                                 mock_path_exists: MagicMock,
                                 mock_is_prefix_match: MagicMock,
                                 mock_zipfile: MagicMock,
                                 mock_move: MagicMock) -> None:
        '''Test that a zip containing only music files is swept to the output directory.'''
        # Set up mocks
        mock_filename = 'mock_music_archive.zip'
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], [mock_filename])]
        mock_path_exists.return_value = False
        mock_is_prefix_match.return_value = False
        
        # Mock archive content
        mock_archive = MagicMock()
        mock_archive.namelist.return_value = [f"mock_file{ext}" for ext in batch_operations_music.EXTENSIONS]
        mock_zipfile.return_value.__enter__.return_value = mock_archive

        # Call target function        
        batch_operations_music.sweep(MOCK_INPUT_DIR,
                                     MOCK_OUTPUT_DIR,
                                     False,
                                     batch_operations_music.EXTENSIONS,
                                     batch_operations_music.PREFIX_HINTS)
        
        # Assert expectations
        mock_walk.assert_called_once_with(MOCK_INPUT_DIR)
        mock_path_exists.assert_called_once_with(f"{MOCK_OUTPUT_DIR}{os.sep}{mock_filename}")
        mock_is_prefix_match.assert_called_once_with(mock_filename, batch_operations_music.PREFIX_HINTS)
        mock_zipfile.assert_called_once()
        mock_move.assert_called_once_with(f"{MOCK_INPUT_DIR}{os.sep}{mock_filename}",
                                          f"{MOCK_OUTPUT_DIR}{os.sep}{mock_filename}")
    
    @patch('shutil.move')
    @patch('zipfile.ZipFile')
    @patch('src.batch_operations_music.is_prefix_match')
    @patch('os.path.exists')
    @patch('os.walk')
    def test_sweep_album_archive(self,
                                 mock_walk: MagicMock,
                                 mock_path_exists: MagicMock,
                                 mock_is_prefix_match: MagicMock,
                                 mock_zipfile: MagicMock,
                                 mock_move: MagicMock) -> None:
        '''Test that a zip containing music files and a cover photo is swept to the output directory.'''
        # Set up mocks
        mock_filename = 'mock_album_archive.zip'
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], [mock_filename])]
        mock_path_exists.return_value = False
        mock_is_prefix_match.return_value = False
        
        # Mock archive content
        mock_archive = MagicMock()
        mock_archive.namelist.return_value =  [f"mock_file{ext}" for ext in batch_operations_music.EXTENSIONS]
        mock_archive.namelist.return_value += ['mock_cover.jpg']
        mock_zipfile.return_value.__enter__.return_value = mock_archive

        # Call target function        
        batch_operations_music.sweep(MOCK_INPUT_DIR,
                                     MOCK_OUTPUT_DIR,
                                     False,
                                     batch_operations_music.EXTENSIONS,
                                     batch_operations_music.PREFIX_HINTS)
        
        # Assert expectations
        mock_walk.assert_called_once_with(MOCK_INPUT_DIR)
        mock_path_exists.assert_called_once_with(f"{MOCK_OUTPUT_DIR}{os.sep}{mock_filename}")
        mock_is_prefix_match.assert_called_once_with(mock_filename, batch_operations_music.PREFIX_HINTS)
        mock_zipfile.assert_called_once()
        mock_move.assert_called_once_with(f"{MOCK_INPUT_DIR}{os.sep}{mock_filename}",
                                          f"{MOCK_OUTPUT_DIR}{os.sep}{mock_filename}")

# Primary test class
class TestFlattenHierarchy(unittest.TestCase):
    @patch('shutil.move')
    @patch('src.batch_operations_music.flatten_zip')
    @patch('os.walk')
    def test_success_loose_files(self,
                                 mock_walk: MagicMock,
                                 mock_flatten_zip: MagicMock,
                                 mock_move: MagicMock) -> None:
        '''Tests that all loose files at the input root are flattened to output.'''
        # Set up mocks
        mock_filenames = [
            'file_0.foo',
            'file_1.foo',
            'file_2.foo',
        ]
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], mock_filenames)]

        # Call target function        
        batch_operations_music.flatten_hierarchy(MOCK_INPUT_DIR, MOCK_OUTPUT_DIR, False)
        
        # Assert expectations
        mock_walk.assert_called_once_with(MOCK_INPUT_DIR)
        mock_flatten_zip.assert_not_called()
        mock_move.assert_has_calls([
            call(f"{MOCK_INPUT_DIR}{os.sep}{mock_filenames[i]}",
                 f"{MOCK_OUTPUT_DIR}{os.sep}{mock_filenames[i]}")
            for i in range(len(mock_filenames))
        ])
    
    @patch('shutil.move')
    @patch('src.batch_operations_music.flatten_zip')
    @patch('os.walk')
    def test_success_zip_files(self,
                               mock_walk: MagicMock,
                               mock_flatten_zip: MagicMock,
                               mock_move: MagicMock) -> None:
        '''Tests that flatten zip is called for a zip archive.'''
        # Set up mocks
        mock_filename = 'mock_archive.zip'
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], ['mock_archive.zip'])]
        
        # Call target function        
        batch_operations_music.flatten_hierarchy(MOCK_INPUT_DIR, MOCK_OUTPUT_DIR, False)
        
        # Assert expectations
        input_filepath = f"{MOCK_INPUT_DIR}{os.sep}{mock_filename}"
        mock_walk.assert_called_once_with(MOCK_INPUT_DIR)
        mock_flatten_zip.assert_called_once_with(input_filepath, MOCK_OUTPUT_DIR)
        mock_move.assert_not_called()
        
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
        
    @patch('src.batch_operations_music.prune_non_music')
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
    @patch('src.batch_operations_music.standardize_lossless')
    @patch('src.batch_operations_music.prune_non_music')
    @patch('src.batch_operations_music.prune_empty')
    @patch('src.batch_operations_music.flatten_hierarchy')
    @patch('src.batch_operations_music.extract')
    @patch('src.batch_operations_music.sweep')
    def test_success(self,
                     mock_sweep: MagicMock,
                     mock_extract: MagicMock,
                     mock_flatten: MagicMock,
                     mock_prune_empty: MagicMock,
                     mock_prune_non_music: MagicMock,
                     mock_standardize_lossless: MagicMock) -> None:
        '''Tests that the process function calls the expected functions in the the correct order.'''
        # Set up mocks
        mock_call_container = MagicMock()
        mock_sweep.side_effect = lambda *_, **__: mock_call_container.sweep()
        mock_extract.side_effect = lambda *_, **__: mock_call_container.extract()
        mock_flatten.side_effect = lambda *_, **__: mock_call_container.flatten()
        mock_prune_empty.side_effect = lambda *_, **__: mock_call_container.prune_empty()
        mock_prune_non_music.side_effect = lambda *_, **__: mock_call_container.prune_non_music()
        mock_standardize_lossless.side_effect = lambda *_, **__: mock_call_container.standardize_lossless()
        
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
        
        # Assert call counts and parameters
        mock_sweep.assert_called_once()
        mock_extract.assert_called_once()
        mock_flatten.assert_called_once()
        
        mock_standardize_lossless.assert_called_once()
        mock_standardize_lossless.assert_called_once_with(args.output, set(), set(), args.interactive)

class TestPruneEmpty(unittest.TestCase):
    @patch('shutil.rmtree')
    @patch('src.batch_operations_music.is_empty_dir')
    @patch('src.batch_operations_music.get_dirs')
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
    @patch('src.batch_operations_music.is_empty_dir')
    @patch('src.batch_operations_music.get_dirs')
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
        
    @patch('src.batch_operations_music.prune_empty')
    def test_success_cli(self, mock_prune_empty: MagicMock) -> None:
        '''Tests that the CLI wrapper calls the correct function.'''
        batch_operations_music.prune_empty('/mock/source/', False)
        mock_prune_empty.assert_called_once_with('/mock/source/', False)
        
class TestRecordCollection(unittest.TestCase):
    # ----------------------
    # Begin happy path cases
    # ----------------------
    @patch.object(ET.ElementTree, 'write')
    @patch('src.batch_operations_music.ET.parse')
    @patch('os.path.exists')
    @patch('src.batch_operations_music.read_tags')
    @patch('os.walk')
    def test_success_new_file(self,
                              mock_walk: MagicMock,
                              mock_read_tags: MagicMock,
                              mock_path_exists: MagicMock,
                              mock_xml_parse: MagicMock,
                              mock_xml_write: MagicMock) -> None:
        '''Tests that a single music file is correctly written to a non-existent XML collection.'''
        # Set up mocks
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], ['mock_file.aiff', '03 - 暴風一族 (Remix).mp3'])]
        mock_read_tags.return_value = Tags(MOCK_ARTIST, MOCK_ALBUM, MOCK_TITLE)
        mock_path_exists.return_value = False
        
        # Call the target function
        actual = batch_operations_music.record_collection(MOCK_INPUT_DIR, MOCK_XML_FILE_PATH)
        
        # Assert call expectations
        mock_path_exists.assert_called_once_with(MOCK_XML_FILE_PATH)
        mock_walk.assert_called_once_with(MOCK_INPUT_DIR)
        mock_xml_parse.assert_not_called()
        mock_xml_write.assert_called_once_with(MOCK_XML_FILE_PATH, encoding='UTF-8', xml_declaration=True)
        
        # Assert that the function reads the file tags
        FILE_PATH_MUSIC = f"{MOCK_INPUT_DIR}{os.sep}"
        mock_read_tags.assert_has_calls([
            call(f"{FILE_PATH_MUSIC}mock_file.aiff"),
            call(f"{FILE_PATH_MUSIC}03 - 暴風一族 (Remix).mp3")
        ])
        
        # Assert that the XML contents are expected
        # Check DJ_PLAYLISTS root node
        dj_playlists: ET.Element  = cast(ET.Element, actual.getroot()) 
        self.assertEqual(len(dj_playlists), 3)
        self.assertEqual(dj_playlists.tag, 'DJ_PLAYLISTS')
        self.assertEqual(dj_playlists.attrib, {'Version': '1.0.0'})
        
        # Check PRODUCT node
        product = dj_playlists[0]
        self.assertEqual(len(product), 0)
        expected_attrib = {'Name': 'rekordbox', 'Version': '6.8.5', 'Company': 'AlphaTheta'}
        self.assertEqual(product.tag, 'PRODUCT')
        self.assertEqual(product.attrib, expected_attrib)
        
        # Check COLLECTION node
        collection = dj_playlists[1]
        self.assertEqual(collection.tag, 'COLLECTION')
        self.assertEqual(collection.attrib, {'Entries': '2'})
        self.assertEqual(len(collection), 2)
        
        # Check TRACK node base attributes
        for track in collection:
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
        
        # Check URL encoded paths
        # Check track 0 path: no URL encoding required
        track_0 = collection[0]
        self.assertEqual(track_0.attrib['Location'], f"file://localhost{MOCK_INPUT_DIR}/mock_file.aiff")
        
        # Check track 1 path: URL encoding required
        track_1 = collection[1]
        self.assertIn('Location', track_1.attrib)
        self.assertEqual(track_1.attrib['Location'].lower(),
                         f"file://localhost{MOCK_INPUT_DIR}/03%20-%20%E6%9A%B4%E9%A2%A8%E4%B8%80%E6%97%8F%20(Remix).mp3".lower())
        
        # Check PLAYLISTS node
        playlists = dj_playlists[2]
        self.assertEqual(len(playlists), 1) # Expect 1 'ROOT' Node
        
        # Check ROOT node
        playlist_root = playlists[0]
        self.assertEqual(playlist_root.tag, 'NODE')
        expected_attrib = {
            'Type' : '0',
            'Name' : 'ROOT',
            'Count': '2'
        }
        self.assertEqual(playlist_root.attrib, expected_attrib)
        
        # Expect 'CUE Analysis Playlist' and '_pruned' Nodes
        self.assertEqual(len(playlist_root), 2)
        
        # Check 'CUE Analysis Playlist' node
        cue_analysis = playlist_root[0]
        self.assertEqual(cue_analysis.tag, 'NODE')
        expected_attrib = {
            'Name'    : "CUE Analysis Playlist",
            'Type'    : "1",
            'KeyType' : "0",
            'Entries' : "0"
        }
        self.assertEqual(cue_analysis.attrib, expected_attrib)
        self.assertEqual(len(cue_analysis), 0) # expect no child nodes
        
        # Check '_pruned' playlist_root Node
        pruned = playlist_root[1]
        self.assertEqual(pruned.tag, 'NODE')
        self.assertIsNotNone(pruned)
        self.assertIn('Name', pruned.attrib)
        self.assertEqual(pruned.attrib['Name'], '_pruned')
        self.assertEqual(len(pruned), 2)
        
        # Check '_pruned' track
        track = pruned[0]
        self.assertEqual(track.tag, 'TRACK')
        self.assertIn("Key", track.attrib)
        self.assertRegex(track.attrib['Key'], r'\d+')

    @patch.object(ET.ElementTree, 'write')
    @patch('src.batch_operations_music.ET.parse')
    @patch('os.path.exists')
    @patch('src.batch_operations_music.read_tags')
    @patch('os.walk')
    def test_success_file_exists(self,
                                 mock_walk: MagicMock,
                                 mock_read_tags: MagicMock,
                                 mock_path_exists: MagicMock,
                                 mock_xml_parse: MagicMock,
                                 mock_xml_write: MagicMock) -> None:
        '''Tests that a single music file is correctly added to an existing XML collection that contains an entry.'''
        # Set up mocks
        mock_path_exists.return_value = True
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], ['mock_file_0.aiff'])]
        mock_read_tags.return_value = Tags(MOCK_ARTIST, MOCK_ALBUM, MOCK_TITLE)
        mock_xml_parse.return_value = ET.ElementTree(ET.fromstring(COLLECTION_XML))
        
        # Insert the first track
        first_call = batch_operations_music.record_collection(MOCK_INPUT_DIR, MOCK_XML_FILE_PATH)
        
        # Reset mocks from first call
        mock_walk.reset_mock()
        mock_read_tags.reset_mock()
        mock_path_exists.reset_mock()
        mock_xml_parse.reset_mock()
        mock_xml_write.reset_mock()
        
        # Set up mocks for second call
        mock_path_exists.return_value = True
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], ['mock_file_1.aiff', '03 - 暴風一族 (Remix).mp3'])]
        mock_read_tags.return_value = Tags(MOCK_ARTIST, MOCK_ALBUM, MOCK_TITLE)
        mock_xml_parse.return_value = first_call
        
        # Call the target function to check that 'mock_file_1' was inserted
        actual = batch_operations_music.record_collection(MOCK_INPUT_DIR, MOCK_XML_FILE_PATH)
            
        # Assert call expectations
        mock_path_exists.assert_called_once_with(MOCK_XML_FILE_PATH)
        mock_walk.assert_called_once_with(MOCK_INPUT_DIR)
        mock_xml_parse.assert_called_with(MOCK_XML_FILE_PATH)
        mock_xml_write.assert_called_once_with(MOCK_XML_FILE_PATH, encoding='UTF-8', xml_declaration=True)
        
        # Assert that the function reads the file tags
        FILE_PATH_MUSIC = f"{MOCK_INPUT_DIR}{os.sep}"
        mock_read_tags.assert_has_calls([
            call(f"{FILE_PATH_MUSIC}mock_file_1.aiff"),
            call(f"{FILE_PATH_MUSIC}03 - 暴風一族 (Remix).mp3")
        ])
        
        # Assert that the XML contents are expected
        # Check DJ_PLAYLISTS root node
        dj_playlists = cast(ET.Element, actual.getroot())
        self.assertEqual(len(dj_playlists), 3)
        self.assertEqual(dj_playlists.tag, 'DJ_PLAYLISTS')
        self.assertEqual(dj_playlists.attrib, {'Version': '1.0.0'})
        
        # Check PRODUCT node
        product = dj_playlists[0]
        expected_attrib = {'Name': 'rekordbox', 'Version': '6.8.5', 'Company': 'AlphaTheta'}
        self.assertEqual(product.tag, 'PRODUCT')
        self.assertEqual(product.attrib, expected_attrib)
        
        # Check COLLECTION node
        collection = dj_playlists[1]
        self.assertEqual(collection.tag, 'COLLECTION')
        self.assertEqual(collection.attrib, {'Entries': '3'})
        self.assertEqual(len(collection), 3)
        
        # Check TRACK nodes
        for track in collection:
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
            
        # Check URL encoded paths
        # Track 0 is skipped, covered in new_file unit test
        # Check track 1 path: no URL encoding required
        track_1 = collection[1]
        self.assertEqual(track_1.attrib['Location'], f"file://localhost{MOCK_INPUT_DIR}/mock_file_1.aiff")
        
        # Check track 2 path: URL encoding required
        track_2 = collection[2]
        self.assertIn('Location', track_2.attrib)
        self.assertEqual(track_2.attrib['Location'].lower(),
                         f"file://localhost{MOCK_INPUT_DIR}/03%20-%20%E6%9A%B4%E9%A2%A8%E4%B8%80%E6%97%8F%20(Remix).mp3".lower())
        
        # Check PLAYLISTS node
        playlists = dj_playlists[2]
        self.assertIsNotNone(playlists)
        self.assertEqual(len(playlists), 1) # Expect 1 'ROOT' Node
        
        # Check ROOT node
        playlist_root = playlists[0]
        expected_attrib = {
            'Type' : '0',
            'Name' : 'ROOT',
            'Count': '2'
        }
        self.assertEqual(playlist_root.attrib, expected_attrib)
        
        # Expect 'CUE Analysis Playlist' and '_pruned' Nodes
        self.assertEqual(len(playlist_root), 2)
        
        # Check 'CUE Analysis Playlist' node
        cue_analysis = playlist_root[0]
        self.assertEqual(cue_analysis.tag, 'NODE')
        self.assertEqual(playlist_root.tag, 'NODE')
        expected_attrib = {
            'Name'    : "CUE Analysis Playlist",
            'Type'    : "1",
            'KeyType' : "0",
            'Entries' : "0"
        }
        self.assertEqual(cue_analysis.attrib, expected_attrib)
        self.assertEqual(len(cue_analysis), 0) # expect no child nodes
        
        # CHECK '_pruned' playlist
        pruned = playlist_root[1]
        self.assertEqual(pruned.tag, 'NODE')
        self.assertIsNotNone(pruned)
        self.assertIn('Name', pruned.attrib)
        self.assertEqual(pruned.attrib['Name'], '_pruned')
        self.assertEqual(len(pruned), 3)
        
        # Check '_pruned' tracks
        for track in pruned:
            self.assertEqual(track.tag, 'TRACK')
            self.assertIn("Key", track.attrib)
            self.assertRegex(track.attrib['Key'], r'\d+')
    
    # ----------------
    # Begin edge cases
    # ----------------
    @patch.object(ET.ElementTree, 'write')
    @patch('src.batch_operations_music.ET.parse')
    @patch('os.path.exists')
    @patch('src.batch_operations_music.read_tags')
    @patch('os.walk')
    def test_success_no_music_files(self,
                                    mock_walk: MagicMock,
                                    mock_read_tags: MagicMock,
                                    mock_path_exists: MagicMock,
                                    mock_xml_parse: MagicMock,
                                    mock_xml_write: MagicMock) -> None:
        '''Tests that the XML collection contains no Tracks when no music files are in the input directory.'''
        # Setup mocks
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], ['mock_file.foo'])]
        mock_path_exists.return_value = False
        
        # Call target function
        actual = batch_operations_music.record_collection(MOCK_INPUT_DIR, MOCK_XML_FILE_PATH)
        
        # Assert call expectations: all files should be skipped
        mock_walk.assert_called_once_with(MOCK_INPUT_DIR)
        mock_read_tags.assert_not_called()
        mock_xml_write.assert_called_once_with(MOCK_XML_FILE_PATH, encoding='UTF-8', xml_declaration=True)
        mock_xml_parse.assert_not_called()
        
        # Empty playlist still expected to be written
        # Check root 'DJ_PLAYLISTS' node
        dj_playlists = cast(ET.Element, actual.getroot())
        self.assertEqual(len(dj_playlists), 3)
        self.assertEqual(dj_playlists.tag, 'DJ_PLAYLISTS')
        self.assertEqual(dj_playlists.attrib, {'Version': '1.0.0'})
        self.assertEqual(len(dj_playlists), 3)
        
        # Check 'PRODUCT' node: same as normal
        product = dj_playlists[0]
        expected_attrib = {'Name': 'rekordbox', 'Version': '6.8.5', 'Company': 'AlphaTheta'}
        self.assertEqual(product.tag, 'PRODUCT')
        self.assertEqual(product.attrib, expected_attrib)
        
        # Check 'COLLECTION' node: expect empty entries
        collection = dj_playlists[1]
        self.assertEqual(collection.tag, 'COLLECTION')
        self.assertEqual(collection.attrib, {'Entries': '0'})
        self.assertEqual(len(collection), 0)
        
        # Check 'PLAYLISTS' node: same as normal
        playlists = dj_playlists[2]
        self.assertEqual(len(playlists), 1) # Expect 1 'ROOT' Node
        
        # Check ROOT node
        playlist_root = playlists[0]
        self.assertEqual(playlist_root.tag, 'NODE')
        expected_attrib = {
            'Type' : '0',
            'Name' : 'ROOT',
            'Count': '2'
        }
        self.assertEqual(playlist_root.attrib, expected_attrib)
        
        # Expect 'CUE Analysis Playlist' and '_pruned' Nodes
        self.assertEqual(len(playlist_root), 2)
        
        # Check 'CUE Analysis Playlist' node
        cue_analysis = playlist_root[0]
        self.assertEqual(cue_analysis.tag, 'NODE')
        expected_attrib = {
            'Name'    : "CUE Analysis Playlist",
            'Type'    : "1",
            'KeyType' : "0",
            'Entries' : "0"
        }
        self.assertEqual(cue_analysis.attrib, expected_attrib)
        self.assertEqual(len(cue_analysis), 0) # expect no child nodes
        
        # Check '_pruned' playlist_root Node
        pruned = playlist_root[1]
        self.assertEqual(pruned.tag, 'NODE')
        self.assertIsNotNone(pruned)
        self.assertIn('Name', pruned.attrib)
        self.assertEqual(pruned.attrib['Name'], '_pruned')
        
        # Check that '_pruned' contains no tracks
        self.assertEqual(len(pruned), 0)
    
    @patch.object(ET.ElementTree, 'write')
    @patch('src.batch_operations_music.ET.parse')
    @patch('os.path.exists')
    @patch('src.batch_operations_music.read_tags')
    @patch('os.walk')
    def test_success_track_exists(self,
                                  mock_walk: MagicMock,
                                  mock_read_tags: MagicMock,
                                  mock_path_exists: MagicMock,
                                  mock_xml_parse: MagicMock,
                                  mock_xml_write: MagicMock) -> None:
        '''Tests that a track is not added to the collection XML if it already exists.'''
        # Setup mocks
        mock_file = 'mock_file.mp3'
        existing_track_xml = f'''
        <?xml version="1.0" encoding="UTF-8"?>

        <DJ_PLAYLISTS Version="1.0.0">
            <PRODUCT Name="rekordbox" Version="6.8.5" Company="AlphaTheta"/>
            <COLLECTION Entries="1">
                <TRACK TrackID="1"
                Name="{MOCK_TITLE}"
                Artist="{MOCK_ARTIST}"
                Album="{MOCK_ALBUM}"
                DateAdded="2025-06-19"
                Location="file://localhost{MOCK_INPUT_DIR}/{mock_file}" />
            </COLLECTION>
            <PLAYLISTS>
                <NODE Type="0" Name="ROOT" Count="2">
                    <NODE Name="CUE Analysis Playlist" Type="1" KeyType="0" Entries="0"/>
                    <NODE Name="_pruned" Type="1" KeyType="0" Entries="1">
                        <TRACK Key="1" />
                    </NODE>
                </NODE>
            </PLAYLISTS>
        </DJ_PLAYLISTS>
        '''.strip()
        
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], [mock_file])]
        mock_path_exists.return_value = True
        mock_xml_parse.return_value = ET.ElementTree(ET.fromstring(existing_track_xml))
        
        # Call target function
        actual = batch_operations_music.record_collection(MOCK_INPUT_DIR, MOCK_XML_FILE_PATH)
        
        # Assert call expectations
        mock_walk.assert_called_once_with(MOCK_INPUT_DIR)
        mock_read_tags.assert_not_called()
        mock_xml_write.assert_called_once_with(MOCK_XML_FILE_PATH, encoding='UTF-8', xml_declaration=True)
        mock_xml_parse.assert_called_once_with(MOCK_XML_FILE_PATH)
        
        # Assert that the XML contents are the same as before attempting to add the track.
        self.assertEqual(ET.tostring(cast(ET.Element, actual.getroot()), encoding="UTF-8"),
                         ET.tostring(cast(ET.Element, mock_xml_parse.return_value.getroot()), encoding="UTF-8"))
        
    @patch.object(ET.ElementTree, 'write')
    @patch('src.batch_operations_music.ET.parse')
    @patch('os.path.exists')
    @patch('src.batch_operations_music.read_tags')
    @patch('os.walk')
    def test_success_unreadable_tags(self,
                                     mock_walk: MagicMock,
                                     mock_read_tags: MagicMock,
                                     mock_path_exists: MagicMock,
                                     mock_xml_parse: MagicMock,
                                     mock_xml_write: MagicMock) -> None:
        '''Tests that a track is not added to the collection XML if its tags are invalid.'''
        # Setup mocks
        mock_read_tags.return_value = None # Mock tag reading failure
        mock_bad_file = 'mock_bad_file.mp3'
        existing_track_xml = f'''
        <?xml version="1.0" encoding="UTF-8"?>

        <DJ_PLAYLISTS Version="1.0.0">
            <PRODUCT Name="rekordbox" Version="6.8.5" Company="AlphaTheta"/>
            <COLLECTION Entries="1">
                <TRACK TrackID="1"
                Name="{MOCK_TITLE}"
                Artist="{MOCK_ARTIST}"
                Album="{MOCK_ALBUM}"
                DateAdded="2025-06-19"
                Location="file://localhost{MOCK_INPUT_DIR}/mock_existing_file.mp3" />
            </COLLECTION>
            <PLAYLISTS>
                <NODE Type="0" Name="ROOT" Count="2">
                    <NODE Name="CUE Analysis Playlist" Type="1" KeyType="0" Entries="0"/>
                    <NODE Name="_pruned" Type="1" KeyType="0" Entries="1">
                        <TRACK Key="1" />
                    </NODE>
                </NODE>
            </PLAYLISTS>
        </DJ_PLAYLISTS>
        '''.strip()
        
        mock_walk.return_value = [(MOCK_INPUT_DIR, [], [mock_bad_file])]
        mock_path_exists.return_value = True
        mock_xml_parse.return_value = ET.ElementTree(ET.fromstring(existing_track_xml))
        
        # Call target function
        actual = batch_operations_music.record_collection(MOCK_INPUT_DIR, MOCK_XML_FILE_PATH)
        
        # Assert call expectations
        mock_walk.assert_called_once_with(MOCK_INPUT_DIR)
        mock_read_tags.assert_called_once_with(f"{MOCK_INPUT_DIR}{os.sep}{mock_bad_file}")
        mock_xml_write.assert_called_once_with(MOCK_XML_FILE_PATH, encoding='UTF-8', xml_declaration=True)
        mock_xml_parse.assert_called_once_with(MOCK_XML_FILE_PATH)
        
        # Assert that the XML contents are the same as before attempting to add the track.
        self.assertEqual(ET.tostring(cast(ET.Element, actual.getroot()), encoding="UTF-8"),
                         ET.tostring(cast(ET.Element, mock_xml_parse.return_value.getroot()), encoding="UTF-8"))
    
    @patch('logging.error')
    @patch.object(ET.ElementTree, 'write')
    @patch('src.batch_operations_music.ET.parse')
    @patch('os.path.exists')
    @patch('src.batch_operations_music.read_tags')
    @patch('os.walk')
    def test_collection_exists_invalid_content(self,
                                               mock_walk: MagicMock,
                                               mock_read_tags: MagicMock,
                                               mock_path_exists: MagicMock,
                                               mock_xml_parse: MagicMock,
                                               mock_xml_write: MagicMock,
                                               mock_log_error: MagicMock) -> None:
        '''Tests that the expected exception is raised when the collection file is invalid.'''
        # Setup mocks
        mock_exception_message = 'mock_parse_error'
        mock_path_exists.return_value = True
        mock_xml_parse.side_effect = Exception(mock_exception_message) # mock a parsing error
        
        # Call target function and assert expectations
        with self.assertRaisesRegex(Exception, mock_exception_message):
            batch_operations_music.record_collection(MOCK_INPUT_DIR, MOCK_XML_FILE_PATH)
            
        # Assert expectations: Code should only check that path exists and attempt to parse
        mock_walk.assert_not_called()
        mock_read_tags.assert_not_called()
        mock_path_exists.assert_called_once_with(MOCK_XML_FILE_PATH)
        mock_xml_parse.assert_called_once_with(MOCK_XML_FILE_PATH)
        mock_xml_write.assert_not_called()
        self.assertRegex(mock_log_error.call_args.args[0], r'^Error loading collection file.+$')
        
    @patch('logging.error')
    @patch.object(ET.ElementTree, 'write')
    @patch('src.batch_operations_music.ET.parse')
    @patch('os.path.exists')
    @patch('src.batch_operations_music.read_tags')
    @patch('os.walk')
    def test_collection_exists_missing_collection_tag(self,
                                                      mock_walk: MagicMock,
                                                      mock_read_tags: MagicMock,
                                                      mock_path_exists: MagicMock,
                                                      mock_xml_parse: MagicMock,
                                                      mock_xml_write: MagicMock,
                                                      mock_log_error: MagicMock) -> None:
        '''Tests that the expected exception is raised when the collection file is missing a COLLECTION tag.'''
        # Setup mocks
        mock_path_exists.return_value = True
        mock_xml_parse.return_value = ET.ElementTree(ET.fromstring('<MOCK_NO_COLLECTION></MOCK_NO_COLLECTION>'))
        
        # Call target function and assert expectations
        with self.assertRaisesRegex(ValueError, 'Invalid collection file format: missing COLLECTION element'):
            batch_operations_music.record_collection(MOCK_INPUT_DIR, MOCK_XML_FILE_PATH)
            
        # Assert expectations: Code should only check that path exists and attempt to parse
        mock_walk.assert_not_called()
        mock_read_tags.assert_not_called()
        mock_path_exists.assert_called_once_with(MOCK_XML_FILE_PATH)
        mock_xml_parse.assert_called_once_with(MOCK_XML_FILE_PATH)
        mock_xml_write.assert_not_called()
        self.assertRegex(mock_log_error.call_args.args[0], r'^Error loading collection file.+$')
            
class TestUpdateLibrary(unittest.TestCase):
    @patch('src.sync_media_server.run_sync_mappings')
    @patch('src.batch_operations_music.sweep')
    @patch('src.batch_operations_music.record_collection')
    @patch('src.batch_operations_music.process')
    def test_success(self,
                     mock_process: MagicMock,
                     mock_record_collection: MagicMock,
                     mock_sweep: MagicMock,
                     mock_run_sync_mappings: MagicMock) -> None:
        '''Tests that dependent functions are called in the correct order with expected parameters.'''
        # Set up mocks
        mock_call_container = MagicMock()
        mock_process.side_effect = lambda *_, **__: mock_call_container.process()
        mock_record_collection.side_effect = lambda *_, **__: mock_call_container.record_collection()
        mock_sweep.side_effect = lambda *_, **__: mock_call_container.sweep()
        mock_run_sync_mappings.side_effect = lambda *_, **__: mock_call_container.run_sync_mappings()
        
        # Call target function
        mock_library = '/mock/library'
        mock_client_mirror = '/mock/client/mirror'
        mock_interactive = False
        mock_extensions = {'.mock_ext'}
        mock_hints = {'mock_hint'}
        batch_operations_music.update_library(MOCK_INPUT_DIR,
                                              mock_library,
                                              mock_client_mirror,
                                              mock_interactive,
                                              mock_extensions,
                                              mock_hints)
        
        # Assert expectations
        # Assert that the primary dependent functions are called in the correct order
        self.assertEqual(mock_call_container.mock_calls[0], call.process())
        self.assertEqual(mock_call_container.mock_calls[1], call.sweep())
        self.assertEqual(mock_call_container.mock_calls[2], call.record_collection())
        self.assertEqual(mock_call_container.mock_calls[3], call.run_sync_mappings())
        
        # Assert the primary dependent function call counts
        mock_process.assert_called_once()
        mock_sweep.assert_called_once()
        mock_record_collection.assert_called_once()
        mock_run_sync_mappings.assert_called_once()
        
        # Assert the primary dependent function call parameters
        # Assert expected call parameters: process
        self.assertEqual(mock_process.call_args.args[0], MOCK_INPUT_DIR)
        # Argument 1 depends on implementation (e.g. temp folder path), so skip check
        # TODO: add asssertion for arg 1
        self.assertEqual(mock_process.call_args.args[2], mock_interactive)
        self.assertEqual(mock_process.call_args.args[3], mock_extensions)
        self.assertEqual(mock_process.call_args.args[4], mock_hints)
        
        # Assert expected call parameters: sweep
        # Argument 0 depends on implementation (e.g. temp folder path), so skip check
        # TODO: add asssertion for arg 0
        self.assertEqual(mock_sweep.call_args.args[1], mock_library)
        self.assertEqual(mock_sweep.call_args.args[2], mock_interactive)
        self.assertEqual(mock_sweep.call_args.args[3], mock_extensions)
        self.assertEqual(mock_sweep.call_args.args[4], mock_hints)
        
        # Assert expected call parameters: record_collection
        # Expect the collection to be updated according to the library path
        self.assertEqual(mock_record_collection.call_args.args, (mock_library, batch_operations_music.COLLECTION_PATH))
        
        # Assert expected call parameters: run_sync_mappings
        # Expect the sync to run with the result of record_collection and client mirror path in full scan mode
        self.assertEqual(mock_run_sync_mappings.call_args.args, (mock_call_container.record_collection(), mock_client_mirror, True))
        
    @patch('src.sync_media_server.run_sync_mappings')
    @patch('src.batch_operations_music.sweep')
    @patch('src.batch_operations_music.record_collection')
    @patch('src.batch_operations_music.process')
    def test_error_sync(self,
                        mock_process: MagicMock,
                        mock_record_collection: MagicMock,
                        mock_sweep: MagicMock,
                        mock_run_sync_mappings: MagicMock) -> None:
        '''Test that if sync fails, the expected functions are still called and the exception is seen.'''
        # Set up mocks
        mock_error = 'Mock error'
        mock_run_sync_mappings.side_effect = Exception(mock_error)
        
        # Call target function
        mock_library = '/mock/library'
        mock_client_mirror = '/mock/client/mirror'
        mock_interactive = False
        mock_extensions = {'.mock_ext'}
        mock_hints = {'mock_hint'}
        
        # Assert expectations
        with self.assertRaises(Exception) as e:
            batch_operations_music.update_library(MOCK_INPUT_DIR,
                                                  mock_library,
                                                  mock_client_mirror,
                                                  mock_interactive,
                                                  mock_extensions,
                                                  mock_hints)
            self.assertEqual(e.msg, 'Mock error')
        
        # Functions should be called before exception
        mock_process.assert_called_once()
        mock_record_collection.assert_called_once()
        mock_sweep.assert_called_once()
        mock_run_sync_mappings.assert_called_once()

if __name__ == "__main__":
    unittest.main()