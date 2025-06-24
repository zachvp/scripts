import unittest
import os
from unittest.mock import patch, MagicMock
from typing import cast

from src.common_tags import Tags, read_tags

# Constants
MOCK_INPUT_DIR = '/mock/input'
MOCK_ARTIST = 'mock_artist'
MOCK_ALBUM = 'mock_album'
MOCK_TITLE = 'mock_title'
MOCK_GENRE = 'mock_genre'
MOCK_TONALITY = 'mock_tonality'

class TestTags(unittest.TestCase):    
    def test_success_init_key(self) -> None:
        '''Tests that all attributes, including the new key/tonality attribute, are properly initialized.'''
        # Call target function
        actual = Tags(MOCK_ARTIST, MOCK_ALBUM, MOCK_TITLE, MOCK_GENRE, MOCK_TONALITY)
        
        # Assert expectations
        self.assertEqual(actual.artist, MOCK_ARTIST)
        self.assertEqual(actual.album, MOCK_ALBUM)
        self.assertEqual(actual.title, MOCK_TITLE)
        self.assertEqual(actual.genre, MOCK_GENRE)
        self.assertEqual(actual.key, MOCK_TONALITY)
        
    def test_success_str_key(self) -> None:
        '''Tests that all attributes, including the new key/tonality attribute, are present in the string representation.'''
        # Call target function
        actual = str(Tags(MOCK_ARTIST, MOCK_ALBUM, MOCK_TITLE, MOCK_GENRE, MOCK_TONALITY))
        
        self.assertIn(MOCK_ARTIST, actual)
        self.assertIn(MOCK_ALBUM, actual)
        self.assertIn(MOCK_TITLE, actual)
        self.assertIn(MOCK_GENRE, actual)
        self.assertIn(MOCK_TONALITY, actual)
        
class TestReadTags(unittest.TestCase):
    @patch('src.common_tags.get_track_key')
    @patch('mutagen.File')
    def test_success(self,
                     mock_file_constructor: MagicMock,
                     mock_get_track_key: MagicMock) -> None:
        '''Tests that the existing and new tags are properly read from a track when they're all present.'''
        # Set up mocks
        ## Mock the file contents
        mock_title_key = 'mock_title_key'
        mock_artist_key = 'mock_artist_key'
        mock_album_key = 'mock_album_key'
        mock_genre_key = 'mock_genre_key'
        mock_tonality_key = 'mock_tonality_key'
        
        mock_filename = 'mock_file.mp3'

        mock_file = MagicMock()
        data = {
            mock_title_key: MOCK_TITLE,
            mock_artist_key: MOCK_ARTIST,
            mock_album_key: MOCK_ALBUM,
            mock_genre_key: MOCK_GENRE,
            mock_tonality_key: MOCK_TONALITY,
        }
        mock_file.__contains__.side_effect = data.__contains__
        mock_file.__getitem__.side_effect = data.__getitem__
        mock_file.tags = MagicMock()
        mock_file_constructor.return_value = mock_file
        
        ## Mock get track key
        mock_get_track_key.side_effect = [mock_title_key, mock_artist_key, mock_album_key, mock_genre_key, mock_tonality_key]
        
        # Call target function
        actual = read_tags(f"{MOCK_INPUT_DIR}{os.sep}{mock_filename}")
        
        # Assert expectations
        self.assertIsNotNone(actual)
        actual = cast(Tags, actual)
        self.assertEqual(actual.artist, MOCK_ARTIST)
        self.assertEqual(actual.album, MOCK_ALBUM)
        self.assertEqual(actual.title, MOCK_TITLE)
        self.assertEqual(actual.genre, MOCK_GENRE)
        self.assertEqual(actual.key, MOCK_TONALITY)