import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock

from src import organize_library_dates as library
from src import constants

# Constants
TRACK_XML = '''
    <TRACK
        TrackID="123456789"
        Name="Test Track"
        Artist="MOCK_ARTIST"
        Album="MOCK_ALBUM"
        DateAdded="2020-02-03"
        Location="file://localhost/Users/user/Music/DJ/MOCK_FILE.aiff">
    </TRACK>
'''.strip()

COLLECTION_XML = f'''
    <?xml version="1.0" encoding="UTF-8"?>
    <COLLECTION Entries="1">
    {TRACK_XML}
    </COLLECTION>
'''.strip()

# Test classes
class TestGenerateDatePaths(unittest.TestCase):
    @patch('src.common.remove_subpath')
    @patch('src.common.find_date_context')
    @patch('src.organize_library_dates.full_path')
    @patch('src.organize_library_dates.swap_root')
    @patch('src.organize_library_dates.collection_path_to_syspath')
    def test_success_default_parameters(self,
                                        mock_collection_path_to_syspath: MagicMock,
                                        mock_swap_root: MagicMock,
                                        mock_full_path: MagicMock,
                                        mock_date_context: MagicMock,
                                        mock_remove_subpath: MagicMock) -> None:
        '''Tests that a collection with a single track yields the expected input/output path mapping
        when called with only the required positional arguments.
        '''
        # Set up mocks
        mock_collection_path_to_syspath.return_value = '/Users/user/Music/DJ/MOCK_FILE.aiff'
        mock_full_path.return_value = '/Users/user/Music/DJ/2020/02 february/03/MOCK_FILE.aiff'
        mock_swap_root.return_value = '/mock/root/Music/DJ/2020/02 february/03/MOCK_FILE.aiff'
        mock_date_context.return_value = ('2020/02 february/03', 5)
        mock_remove_subpath.return_value = '/mock/root/2020/02 february/03/MOCK_FILE.aiff'
        
        # Set up input
        collection = ET.fromstring(COLLECTION_XML)
        
        # Call test function
        actual = library.generate_date_paths(collection, '/mock/root/')
        
        # Assert expectations
        # Output
        expected = [('/Users/user/Music/DJ/MOCK_FILE.aiff',
                     '/mock/root/2020/02 february/03/MOCK_FILE.aiff')]
        self.assertEqual(actual, expected)
        
        # Dependency calls
        mock_collection_path_to_syspath.assert_called()
        mock_full_path.assert_called_once()
        mock_date_context.assert_called_once()
        mock_remove_subpath.assert_called_once()
    
    @patch('src.common.remove_subpath')
    @patch('src.common.find_date_context')
    @patch('src.organize_library_dates.full_path')
    @patch('src.organize_library_dates.swap_root')
    @patch('src.organize_library_dates.collection_path_to_syspath')
    def test_success_metadata_path(self,
                                   mock_collection_path_to_syspath: MagicMock,
                                   mock_swap_root: MagicMock,
                                   mock_full_path: MagicMock,
                                   mock_date_context: MagicMock,
                                   mock_remove_subpath: MagicMock) -> None:
        '''Tests that a collection with a single track yields the expected input/output path mapping
        when called with the include metadata in path parameter.
        '''
        # Set up mocks
        mock_collection_path_to_syspath.return_value = '/Users/user/Music/DJ/MOCK_FILE.aiff'
        mock_full_path.return_value = '/Users/user/Music/DJ/2020/02 february/03/MOCK_ARTIST/MOCK_ALBUM/MOCK_FILE.aiff'
        mock_swap_root.return_value = '/mock/root/Music/DJ/2020/02 february/03/MOCK_ARTIST/MOCK_ALBUM/MOCK_FILE.aiff'
        mock_date_context.return_value = ('2020/02 february/03', 5)
        mock_remove_subpath.return_value = '/mock/root/2020/02 february/03/MOCK_ARTIST/MOCK_ALBUM/MOCK_FILE.aiff'
        
        # Set up input
        collection = ET.fromstring(COLLECTION_XML)
        
        # Call test function
        actual = library.generate_date_paths(collection, '/mock/root/', metadata_path=True)
        
        # Assert expectations
        # Output
        expected = [('/Users/user/Music/DJ/MOCK_FILE.aiff',
                     '/mock/root/2020/02 february/03/MOCK_ARTIST/MOCK_ALBUM/MOCK_FILE.aiff')]
        self.assertEqual(actual, expected)
        
        # Dependency calls
        mock_collection_path_to_syspath.assert_called()
        mock_full_path.assert_called_once()
        mock_date_context.assert_called_once()
        mock_remove_subpath.assert_called_once()
        
    @patch('src.common.remove_subpath')
    @patch('src.common.find_date_context')
    @patch('src.organize_library_dates.full_path')
    @patch('src.organize_library_dates.swap_root')
    @patch('src.organize_library_dates.collection_path_to_syspath')
    def test_success_playlist_ids_include(self,
                                          mock_collection_path_to_syspath: MagicMock,
                                          mock_swap_root: MagicMock,
                                          mock_full_path: MagicMock,
                                          mock_date_context: MagicMock,
                                          mock_remove_subpath: MagicMock) -> None:
        '''Tests that a collection with a single track yields the expected input/output path mapping
        when the collection includes the playlist ID in the given set.
        '''
        # Set up mocks
        mock_collection_path_to_syspath.return_value = '/Users/user/Music/DJ/MOCK_FILE.aiff'
        mock_full_path.return_value = '/Users/user/Music/DJ/2020/02 february/03/MOCK_FILE.aiff'
        mock_swap_root.return_value = '/mock/root/Music/DJ/2020/02 february/03/MOCK_FILE.aiff'
        mock_date_context.return_value = ('2020/02 february/03', 5)
        mock_remove_subpath.return_value = '/mock/root/2020/02 february/03/MOCK_FILE.aiff'
        
        # Set up input
        collection = ET.fromstring(COLLECTION_XML)
        
        # Call test function
        actual = library.generate_date_paths(collection, '/mock/root/', playlist_ids={'123456789'})
        
        # Assert expectations
        # Output
        expected = [('/Users/user/Music/DJ/MOCK_FILE.aiff',
                     '/mock/root/2020/02 february/03/MOCK_FILE.aiff')]
        self.assertEqual(actual, expected)
        
        # Dependency calls
        mock_collection_path_to_syspath.assert_called()
        mock_full_path.assert_called_once()
        mock_date_context.assert_called_once()
        mock_remove_subpath.assert_called_once()
        
    @patch('src.common.remove_subpath')
    @patch('src.common.find_date_context')
    @patch('src.organize_library_dates.full_path')
    @patch('src.organize_library_dates.swap_root')
    @patch('src.organize_library_dates.collection_path_to_syspath')
    def test_success_playlist_ids_exclude(self,
                                          mock_collection_path_to_syspath: MagicMock,
                                          mock_swap_root: MagicMock,
                                          mock_full_path: MagicMock,
                                          mock_date_context: MagicMock,
                                          mock_remove_subpath: MagicMock) -> None:
        '''Tests that a collection with a single track yields an empty path mapping
        when the collection does NOT include the playlist ID in the given set.
        '''
        # Set up mocks
        mock_collection_path_to_syspath.return_value = '/Users/user/Music/DJ/MOCK_FILE.aiff'
        
        # Set up input
        collection = ET.fromstring(COLLECTION_XML)
        
        # Call test function
        actual = library.generate_date_paths(collection, '/mock/root/', playlist_ids={'MOCK_ID_TO_SKIP'})
        
        # Assert expectations
        # Output
        expected = []
        self.assertEqual(actual, expected)
        
        # Dependency calls - only one call expected, the others should be skipped
        mock_collection_path_to_syspath.assert_called_once()
        mock_full_path.assert_not_called()
        mock_date_context.assert_not_called()
        mock_remove_subpath.assert_not_called()

class TestFullPath(unittest.TestCase):
    @patch('src.organize_library_dates.date_path')
    def test_success_default_parameters(self, mock_date_path: MagicMock) -> None:
        '''Tests for expected output with only required positional arguments provided.'''
        # Set up input
        node = ET.fromstring(TRACK_XML)
        
        # Set up mocks
        mock_date_path.return_value = '2020/02 february/03'
        
        # Call test function
        actual = library.full_path(node, constants.REKORDBOX_ROOT, constants.MAPPING_MONTH)
        
        # Assert expectations
        expected = '/Users/user/Music/DJ/2020/02 february/03/MOCK_FILE.aiff'
        self.assertEqual(actual, expected)
        
    @patch('src.organize_library_dates.date_path')
    def test_success_include_metadata(self, mock_date_path: MagicMock) -> None:
        '''Tests for expected output with metadata included paramter.'''
        # Set up input
        node = ET.fromstring(TRACK_XML)
        
        # Set up mocks
        mock_date_path.return_value = '2020/02 february/03'
        
        # Call test function
        actual = library.full_path(node, constants.REKORDBOX_ROOT, constants.MAPPING_MONTH, include_metadata=True)
        
        # Assert expectations
        expected = '/Users/user/Music/DJ/2020/02 february/03/MOCK_ARTIST/MOCK_ALBUM/MOCK_FILE.aiff'
        self.assertEqual(actual, expected)

class TestCollectionPathToSyspath(unittest.TestCase):
    def test_success_simple_path(self) -> None:
        '''Tests that the Collection XML Location path format is correctly converted into system format
        when the path contains no URL-encoded characters.'''
        # Set up input
        path = 'file://localhost/Users/user/Music/DJ/MOCK_FILE.aiff'
        
        # Call test function
        actual = library.collection_path_to_syspath(path)
        
        # Assert expectations
        expected = '/Users/user/Music/DJ/MOCK_FILE.aiff'
        self.assertEqual(actual, expected)
        
    def test_success_complex_path(self) -> None:
        '''Tests that the Collection XML Location path format is correctly converted into system format
        when the path contains URL-encoded characters.'''
        # Set up input
        path = 'file://localhost/Users/user/Music/DJ/MOCK%20-%20COMPLEX_PATH.aiff'
        
        # Call test function
        actual = library.collection_path_to_syspath(path)
        
        # Assert expectations
        expected = '/Users/user/Music/DJ/MOCK - COMPLEX_PATH.aiff'
        self.assertEqual(actual, expected)

if __name__ == "__main__":
    unittest.main()
