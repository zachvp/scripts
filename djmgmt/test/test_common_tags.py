import unittest
import os
import io
from PIL import Image
from unittest.mock import patch, MagicMock
from typing import cast

# explicit imports to load possible submodules;
# by default, the test environment will not include these
import mutagen.aiff, mutagen.id3, mutagen.flac, mutagen.mp3, mutagen.wave

from src import common_tags
from src.common_tags import Tags

# Constants
MOCK_INPUT_DIR = '/mock/input'
MOCK_ARTIST = 'mock_artist'
MOCK_ALBUM = 'mock_album'
MOCK_TITLE = 'mock_title'
MOCK_GENRE = 'mock_genre'
MOCK_MUSIC_KEY = 'mock_music_key'
MOCK_IMAGE_DESCRIPTION = 'mock_image_description'

MOCK_TITLE_KEY = 'mock_title_key'
MOCK_ARTIST_KEY = 'mock_artist_key'
MOCK_ALBUM_KEY = 'mock_album_key'
MOCK_GENRE_KEY = 'mock_genre_key'
MOCK_MUSIC_KEY = 'mock_music_key'

MOCK_FILE_DATA = {
    MOCK_TITLE_KEY: MOCK_TITLE,
    MOCK_ARTIST_KEY: MOCK_ARTIST,
    MOCK_ALBUM_KEY: MOCK_ALBUM,
    MOCK_GENRE_KEY: MOCK_GENRE,
    MOCK_MUSIC_KEY: MOCK_MUSIC_KEY,
}

MOCK_IMAGE_TYPE = mutagen.id3.PictureType.COVER_FRONT

# Classes: Corresponds to each type in constants.EXTENSIONS
class MockMP3(MagicMock, mutagen.mp3.MP3):
    pass

class MockWav(MagicMock, mutagen.wave.WAVE):
    pass

class MockAIFF(MagicMock, mutagen.aiff.AIFF):
    pass

class MockFLAC(MagicMock, mutagen.flac.FLAC):
    pass

# Helpers
def create_mock_image_data() -> bytes:
    image = Image.new('RGB', (1, 1), color='white')
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()

def image_to_bytes(image: Image.Image, format: str='PNG') -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()

class TestTags(unittest.TestCase):
    def test_success_init_image(self) -> None:
        '''Tests that all existing and the new cover image attributes are properly initialized.'''
        # Call target function
        actual = Tags(MOCK_ARTIST,
                      MOCK_ALBUM,
                      MOCK_TITLE,
                      MOCK_GENRE,
                      MOCK_MUSIC_KEY,
                      Image.Image(), # type: ignore
                      MOCK_IMAGE_DESCRIPTION)
        
        # Assert expectations
        self.assertEqual(actual.artist, MOCK_ARTIST)
        self.assertEqual(actual.album, MOCK_ALBUM)
        self.assertEqual(actual.title, MOCK_TITLE)
        self.assertEqual(actual.genre, MOCK_GENRE)
        self.assertEqual(actual.key, MOCK_MUSIC_KEY)
        
        # Assert expectations
        ## Assert that an instance of PIL.Image exists as a Tags attribute
        actual_attributes = vars(actual)
        contains_image_attribute = False
        contains_image_description = False
        for value in actual_attributes.values():
            contains_image_attribute |= isinstance(value, Image.Image)
            contains_image_description |= value == MOCK_IMAGE_DESCRIPTION
        self.assertTrue(contains_image_attribute, 'Expect Tags instance to contain an image attribute.')
        
        ## Expect existing 5 attributes, plus additional Image and an image description
        self.assertEqual(len(actual_attributes), 7)
        
    def test_success_str_image(self) -> None:
        '''Tests that all existing and the new cover image attributes are present in the string representation.'''
        # Call target function
        actual = str(Tags(MOCK_ARTIST,
                      MOCK_ALBUM,
                      MOCK_TITLE,
                      MOCK_GENRE,
                      MOCK_MUSIC_KEY,
                      Image.Image(), # type: ignore
                      MOCK_IMAGE_DESCRIPTION))
        
        self.assertIn(MOCK_ARTIST, actual)
        self.assertIn(MOCK_ALBUM, actual)
        self.assertIn(MOCK_TITLE, actual)
        self.assertIn(MOCK_GENRE, actual)
        self.assertIn(MOCK_MUSIC_KEY, actual)
        self.assertIn(MOCK_IMAGE_DESCRIPTION, actual)
        
class TestReadTags(unittest.TestCase):
    # Helpers
    def assert_image(self, actual: Tags, mock_data) -> None:
        actual_attributes = vars(actual)
        image_attribute: Image.Image | None = None
        image_count = 0
        for value in actual_attributes.values():
            if isinstance(value, Image.Image):
                image_attribute = value
                image_count += 1
        
        # Assert exactly 1 image exists
        self.assertIsNotNone(image_attribute)
        self.assertEqual(image_count, 1, 'Expect only one image in Tags instance')
        
        # Assert image content matches mock data
        image_attribute = cast(Image.Image, image_attribute)
        self.assertEqual(image_to_bytes(image_attribute), mock_data)
        
        # Assert the image type was extracted to Tags instance
        self.assertIn(str(MOCK_IMAGE_TYPE), vars(actual).values())
        
    def create_mock_tags(self, mock_data: bytes, include_tags: bool = True) -> MagicMock:
        mock_tags = MagicMock()
        tags_data = {
            'mock_id3_apic': mutagen.id3.APIC(data=mock_data, type=MOCK_IMAGE_TYPE),
        }
        if not include_tags:
            tags_data = {}
        mock_tags.__contains__.side_effect = tags_data.__contains__
        mock_tags.__getitem__.side_effect = tags_data.__getitem__
        mock_tags.values.side_effect = tags_data.values
        return mock_tags
    
    def configure_mock_track(self, mock_track: MagicMock) -> None:
        mock_track.__contains__.side_effect = MOCK_FILE_DATA.__contains__ # type: ignore
        mock_track.__getitem__.side_effect = MOCK_FILE_DATA.__getitem__ # type: ignore
    
    @patch('src.common_tags.get_track_key')
    @patch('mutagen.File')
    def test_success_mp3(self,
                         mock_file_constructor: MagicMock,
                         mock_get_track_key: MagicMock) -> None:
        '''Tests that the existing tags and the new cover image are properly read from a track when they're all present.'''
        # Set up mocks
        mock_data = create_mock_image_data()
        mock_filename = 'mock_file.mp3'
        mock_path = f"{MOCK_INPUT_DIR}{os.sep}{mock_filename}"

        ## Mock the track file contents
        mock_track = MockMP3()
        self.configure_mock_track(mock_track)
        
        ## Configure the mock mutagen tags
        mock_tags = self.create_mock_tags(mock_data)
        
        # Set the mock attributes
        mock_track.tags = mock_tags
        mock_file_constructor.return_value = mock_track
        
        ## Mock get track key
        mock_get_track_key.side_effect = [ MOCK_TITLE_KEY, MOCK_ARTIST_KEY, MOCK_ALBUM_KEY, MOCK_GENRE_KEY, MOCK_MUSIC_KEY]
        
        # Call target function
        actual = common_tags.read_tags(mock_path)
        
        # Assert expectations
        mock_file_constructor.assert_called_once_with(mock_path)
        
        self.assertIsNotNone(actual)
        actual = cast(Tags, actual)
        
        ## Assert existing tags
        self.assertEqual(actual.artist, MOCK_ARTIST)
        self.assertEqual(actual.album, MOCK_ALBUM)
        self.assertEqual(actual.title, MOCK_TITLE)
        self.assertEqual(actual.genre, MOCK_GENRE)
        self.assertEqual(actual.key, MOCK_MUSIC_KEY)
        
        ## Assert that the Tags instance contains a PIL.Image with the expected data
        self.assert_image(actual, mock_data)
        
    @patch('src.common_tags.get_track_key')
    @patch('mutagen.File')
    def test_success_wav(self,
                         mock_file_constructor: MagicMock,
                         mock_get_track_key: MagicMock) -> None:
        '''Tests that the existing tags and the new cover image are properly read from a track when they're all present.'''
        # Set up mocks
        mock_data = create_mock_image_data()
        mock_filename = 'mock_file.wav'
        mock_path = f"{MOCK_INPUT_DIR}{os.sep}{mock_filename}"

        ## Mock the track file contents
        mock_track = MockWav()
        self.configure_mock_track(mock_track)
        
        ## Configure the mock mutagen tags
        mock_tags = self.create_mock_tags(mock_data)
        
        # Set the mock attributes
        mock_track.tags = mock_tags
        mock_file_constructor.return_value = mock_track
        
        ## Mock get track key
        mock_get_track_key.side_effect = [ MOCK_TITLE_KEY, MOCK_ARTIST_KEY, MOCK_ALBUM_KEY, MOCK_GENRE_KEY, MOCK_MUSIC_KEY]
        
        # Call target function
        actual = common_tags.read_tags(mock_path)
        
        # Assert expectations
        mock_file_constructor.assert_called_once_with(mock_path)
        
        self.assertIsNotNone(actual)
        actual = cast(Tags, actual)
        
        ## Assert existing tags
        self.assertEqual(actual.artist, MOCK_ARTIST)
        self.assertEqual(actual.album, MOCK_ALBUM)
        self.assertEqual(actual.title, MOCK_TITLE)
        self.assertEqual(actual.genre, MOCK_GENRE)
        self.assertEqual(actual.key, MOCK_MUSIC_KEY)
        
        ## Assert that the Tags instance contains a PIL.Image with the expected data
        self.assert_image(actual, mock_data)
        
    @patch('src.common_tags.get_track_key')
    @patch('mutagen.File')
    def test_success_aiff(self,
                          mock_file_constructor: MagicMock,
                          mock_get_track_key: MagicMock) -> None:
        '''Tests that the existing tags and the new cover image are properly read from a track when they're all present.'''
        # Set up mocks
        mock_data = create_mock_image_data()
        mock_filename = 'mock_file.aiff'
        mock_path = f"{MOCK_INPUT_DIR}{os.sep}{mock_filename}"

        ## Mock the track file contents
        mock_track = MockAIFF()
        self.configure_mock_track(mock_track)
        
        ## Configure the mock mutagen tags
        mock_tags = self.create_mock_tags(mock_data)
        
        # Set the mock attributes
        mock_track.tags = mock_tags
        mock_file_constructor.return_value = mock_track
        
        ## Mock get track key
        mock_get_track_key.side_effect = [ MOCK_TITLE_KEY, MOCK_ARTIST_KEY, MOCK_ALBUM_KEY, MOCK_GENRE_KEY, MOCK_MUSIC_KEY]
        
        # Call target function
        actual = common_tags.read_tags(mock_path)
        
        # Assert expectations
        mock_file_constructor.assert_called_once_with(mock_path)
        
        self.assertIsNotNone(actual)
        actual = cast(Tags, actual)
        
        ## Assert existing tags
        self.assertEqual(actual.artist, MOCK_ARTIST)
        self.assertEqual(actual.album, MOCK_ALBUM)
        self.assertEqual(actual.title, MOCK_TITLE)
        self.assertEqual(actual.genre, MOCK_GENRE)
        self.assertEqual(actual.key, MOCK_MUSIC_KEY)
        
        ## Assert that the Tags instance contains a PIL.Image with the expected data
        self.assert_image(actual, mock_data)
        
    @patch('src.common_tags.get_track_key')
    @patch('mutagen.File')
    def test_success_flac(self,
                          mock_file_constructor: MagicMock,
                          mock_get_track_key: MagicMock) -> None:
        '''Tests that the existing tags and the new cover image are properly read from a track when they're all present.'''
        # Set up mocks
        mock_data = create_mock_image_data()
        mock_filename = 'mock_file.flac'
        mock_path = f"{MOCK_INPUT_DIR}{os.sep}{mock_filename}"

        ## Mock the track file contents
        mock_track = MockFLAC(spec=mutagen.flac.FLAC)
        self.configure_mock_track(mock_track)
        
        # Additional mock config for FLAC picture
        picture = mutagen.flac.Picture()
        picture.data = mock_data
        picture.type = MOCK_IMAGE_TYPE
        mock_track.metadata_blocks = []
        mock_track.add_picture(picture)
        
        ## Configure the mock mutagen tags
        mock_tags = self.create_mock_tags(mock_data, include_tags=False)
        
        # Set the mock attributes
        mock_track.tags = mock_tags
        mock_file_constructor.return_value = mock_track
        
        ## Mock get track key
        mock_get_track_key.side_effect = [ MOCK_TITLE_KEY, MOCK_ARTIST_KEY, MOCK_ALBUM_KEY, MOCK_GENRE_KEY, MOCK_MUSIC_KEY]
        
        # Call target function
        actual = common_tags.read_tags(mock_path)
        
        # Assert expectations
        mock_file_constructor.assert_called_once_with(mock_path)
        
        self.assertIsNotNone(actual)
        actual = cast(Tags, actual)
        
        ## Assert existing tags
        self.assertEqual(actual.artist, MOCK_ARTIST)
        self.assertEqual(actual.album, MOCK_ALBUM)
        self.assertEqual(actual.title, MOCK_TITLE)
        self.assertEqual(actual.genre, MOCK_GENRE)
        self.assertEqual(actual.key, MOCK_MUSIC_KEY)
        
        ## Assert that the Tags instance contains a PIL.Image with the expected data
        self.assert_image(actual, mock_data)

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
        mock_music_key = 'mock_music_key'
        
        mock_filename = 'mock_file.mp3'

        mock_file = MagicMock()
        data = {
            mock_title_key: MOCK_TITLE,
            mock_artist_key: MOCK_ARTIST,
            mock_album_key: MOCK_ALBUM,
            mock_genre_key: MOCK_GENRE,
            mock_music_key: MOCK_MUSIC_KEY,
        }
        mock_file.__contains__.side_effect = data.__contains__
        mock_file.__getitem__.side_effect = data.__getitem__
        mock_file.tags = MagicMock()
        mock_file_constructor.return_value = mock_file
        
        ## Mock get track key
        mock_get_track_key.side_effect = [ mock_title_key, mock_artist_key, mock_album_key, mock_genre_key, mock_music_key]
        
        # Call target function
        actual = common_tags.read_tags(f"{MOCK_INPUT_DIR}{os.sep}{mock_filename}")
        
        # Assert expectations
        self.assertIsNotNone(actual)
        actual = cast(Tags, actual)
        self.assertEqual(actual.artist, MOCK_ARTIST)
        self.assertEqual(actual.album, MOCK_ALBUM)
        self.assertEqual(actual.title, MOCK_TITLE)
        self.assertEqual(actual.genre, MOCK_GENRE)
        self.assertEqual(actual.key, MOCK_MUSIC_KEY)