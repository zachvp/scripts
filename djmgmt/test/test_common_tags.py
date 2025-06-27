# Core dependencies
import unittest
import io
import numpy as np
import mutagen.aiff, mutagen.id3, mutagen.flac, mutagen.mp3, mutagen.wave

from imagehash import ImageHash
from PIL import Image
from unittest.mock import patch, MagicMock
from typing import cast

# Test targets
from src import common_tags
from src.common_tags import Tags

# Constants
## Mock input arguments
MOCK_INPUT_PATH = '/mock/input'
MOCK_ARTIST = 'mock_artist'
MOCK_ALBUM = 'mock_album'
MOCK_TITLE = 'mock_title'
MOCK_GENRE = 'mock_genre'
MOCK_MUSIC_KEY = 'mock_music_key'
MOCK_IMAGE = Image.new('RGB', (1, 1), color='white')
MOCK_IMAGE_DESCRIPTION = 'mock_image_description'

## Mock tag data keys
MOCK_TITLE_KEY = 'mock_title_key'
MOCK_ARTIST_KEY = 'mock_artist_key'
MOCK_ALBUM_KEY = 'mock_album_key'
MOCK_GENRE_KEY = 'mock_genre_key'
MOCK_MUSIC_KEY = 'mock_music_key'

## Mock track file data
MOCK_TRACK_DATA = {
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
    '''Generates raw data for a minimal PNG image.'''
    image = Image.new('RGB', (1, 1), color='white')
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()

def image_to_bytes(image: Image.Image) -> bytes:
    '''Converts the given PNG image to bytes'''
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()

def create_full_mock_tags() -> Tags:
    '''Convenience function to create a tags instance with all possible attributes.'''
    return Tags(MOCK_ARTIST,
                MOCK_ALBUM,
                MOCK_TITLE,
                MOCK_GENRE,
                MOCK_MUSIC_KEY,
                MOCK_IMAGE,
                MOCK_IMAGE_DESCRIPTION)

class TestTags(unittest.TestCase):
    '''Tests for creating a Tags instance.'''
    
    def test_success_init_full(self) -> None:
        '''Tests that all attributes are properly initialized.'''
        # Call target function
        actual = create_full_mock_tags()
        
        # Assert expectations
        self.assertEqual(actual.artist, MOCK_ARTIST)
        self.assertEqual(actual.album, MOCK_ALBUM)
        self.assertEqual(actual.title, MOCK_TITLE)
        self.assertEqual(actual.genre, MOCK_GENRE)
        self.assertEqual(actual.key, MOCK_MUSIC_KEY)
        
        ## Image assertions: compare byte contents
        self.assertIsNotNone(actual.cover_image)
        self.assertEqual(image_to_bytes(cast(Image.Image, actual.cover_image)), image_to_bytes(MOCK_IMAGE))
        self.assertEqual(actual.cover_image_str, MOCK_IMAGE_DESCRIPTION)
        
    def test_success_str(self) -> None:
        '''Tests that all attributes are present in the string representation.'''
        # Call target function
        actual = str(create_full_mock_tags())
        
        # Assert expectations
        self.assertIn(MOCK_ARTIST, actual)
        self.assertIn(MOCK_ALBUM, actual)
        self.assertIn(MOCK_TITLE, actual)
        self.assertIn(MOCK_GENRE, actual)
        self.assertIn(MOCK_MUSIC_KEY, actual)
        self.assertIn(MOCK_IMAGE_DESCRIPTION, actual)

class TestReadTags(unittest.TestCase):
    '''Tests for read_tags.'''
    
    # Helpers
    def assert_image(self, actual: Tags, mock_data) -> None:
        # Assert image content matches mock data
        self.assertIsNotNone(actual)
        image = cast(Image.Image, actual.cover_image)
        self.assertEqual(image_to_bytes(image), mock_data)
        
        # Assert the image type was extracted to Tags instance
        self.assertEqual(actual.cover_image_str, str(MOCK_IMAGE_TYPE))
        
    def create_mock_tag_data(self, mock_data: bytes, include_tags: bool = True) -> MagicMock:
        mock_tag_data = MagicMock()
        tags_data = {
            'mock_id3_apic': mutagen.id3.APIC(data=mock_data, type=MOCK_IMAGE_TYPE),
        }
        if not include_tags:
            tags_data = {}
        mock_tag_data.__contains__.side_effect = tags_data.__contains__
        mock_tag_data.__getitem__.side_effect = tags_data.__getitem__
        mock_tag_data.values.side_effect = tags_data.values
        return mock_tag_data
    
    def configure_mock_track(self, mock_track: MagicMock) -> None:
        mock_track.__contains__.side_effect = MOCK_TRACK_DATA.__contains__ # type: ignore
        mock_track.__getitem__.side_effect = MOCK_TRACK_DATA.__getitem__ # type: ignore
        
    def run_read_tags_id3_filetype(self, mock_track: MagicMock, mock_file_constructor: MagicMock, mock_get_track_key: MagicMock):
        '''Common test runner for ID3-like file type cases (e.g. MP3, AIFF, WAV).'''
        # Mock data
        mock_data = create_mock_image_data()
        
        # Configure mocks
        self.configure_mock_track(mock_track)
        
        ## Configure the mock mutagen tags
        mock_tag_data = self.create_mock_tag_data(mock_data)
        
        # Set the mock attributes
        mock_track.tags = mock_tag_data
        mock_file_constructor.return_value = mock_track
        
        ## Mock get track key
        mock_get_track_key.side_effect = [ MOCK_TITLE_KEY, MOCK_ARTIST_KEY, MOCK_ALBUM_KEY, MOCK_GENRE_KEY, MOCK_MUSIC_KEY]
        
        # Call target function
        actual = common_tags.read_tags(MOCK_INPUT_PATH)
        
        # Assert expectations
        mock_file_constructor.assert_called_once_with(MOCK_INPUT_PATH)
        
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
    
    # Test cases
    @patch('src.common_tags.get_track_key')
    @patch('mutagen.File')
    def test_success_mp3(self,
                         mock_file_constructor: MagicMock,
                         mock_get_track_key: MagicMock) -> None:
        '''Tests that the MP3 file tags are properly read when they're all present.'''
        # Set up mocks
        mock_track = MockMP3()
        
        # Run the common test logic for file type
        self.run_read_tags_id3_filetype(mock_track, mock_file_constructor, mock_get_track_key)
        
    @patch('src.common_tags.get_track_key')
    @patch('mutagen.File')
    def test_success_wav(self,
                         mock_file_constructor: MagicMock,
                         mock_get_track_key: MagicMock) -> None:
        '''Tests that the WAV file tags are properly read when they're all present.'''
        # Set up mocks
        mock_track = MockWav()
        
        # Run the common test logic for file type
        self.run_read_tags_id3_filetype(mock_track, mock_file_constructor, mock_get_track_key)
        
    @patch('src.common_tags.get_track_key')
    @patch('mutagen.File')
    def test_success_aiff(self,
                          mock_file_constructor: MagicMock,
                          mock_get_track_key: MagicMock) -> None:
        '''Tests that the AIFF file tags are properly read when they're all present.'''
        # Set up mocks
        mock_track = MockAIFF()
        
        # Run the common test logic for file type
        self.run_read_tags_id3_filetype(mock_track, mock_file_constructor, mock_get_track_key)
        
    @patch('src.common_tags.get_track_key')
    @patch('mutagen.File')
    def test_success_flac(self,
                          mock_file_constructor: MagicMock,
                          mock_get_track_key: MagicMock) -> None:
        '''Tests that the FLAC file tags are properly read when they're all present.'''
        # Set up mocks: FLAC images are stored differently than ID3-like images, so custom mocking is required.
        mock_data = create_mock_image_data()

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
        mock_tag_data = self.create_mock_tag_data(mock_data, include_tags=False)
        
        # Set the mock attributes
        mock_track.tags = mock_tag_data
        mock_file_constructor.return_value = mock_track
        
        ## Mock get track key
        mock_get_track_key.side_effect = [ MOCK_TITLE_KEY, MOCK_ARTIST_KEY, MOCK_ALBUM_KEY, MOCK_GENRE_KEY, MOCK_MUSIC_KEY]
        
        # Call target function
        actual = common_tags.read_tags(MOCK_INPUT_PATH)
        
        # Assert expectations
        mock_file_constructor.assert_called_once_with(MOCK_INPUT_PATH)
        
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
    def test_success_no_cover_image(self,
                                    mock_file_constructor: MagicMock,
                                    mock_get_track_key: MagicMock) -> None:
        '''Tests that the existing and new tags are properly read from a track when they're all present.'''
        # Set up mocks
        mock_file = MagicMock()
        self.configure_mock_track(mock_file)
        mock_file_constructor.return_value = mock_file
        
        ## Mock get track key
        mock_get_track_key.side_effect = [ MOCK_TITLE_KEY, MOCK_ARTIST_KEY, MOCK_ALBUM_KEY, MOCK_GENRE_KEY, MOCK_MUSIC_KEY]
        
        # Call target function
        actual = common_tags.read_tags(MOCK_INPUT_PATH)
        
        # Assert expectations
        self.assertIsNotNone(actual)
        actual = cast(Tags, actual)
        self.assertEqual(actual.artist, MOCK_ARTIST)
        self.assertEqual(actual.album, MOCK_ALBUM)
        self.assertEqual(actual.title, MOCK_TITLE)
        self.assertEqual(actual.genre, MOCK_GENRE)
        self.assertEqual(actual.key, MOCK_MUSIC_KEY)
        self.assertIsNone(actual.cover_image)
        self.assertIsNone(actual.cover_image_str)
        
    @patch('src.common_tags.get_track_key')
    @patch('mutagen.File')
    def test_success_no_artist_no_title(self,
                                        mock_file_constructor: MagicMock,
                                        mock_get_track_key: MagicMock) -> None:
        '''Tests that None is returned when title and artist are missing.'''
        # Set up mocks
        mock_file = MagicMock()
        self.configure_mock_track(mock_file)
        mock_file_constructor.return_value = mock_file
        
        ## Mock get track key
        mock_get_track_key.side_effect = [ None, None, MOCK_ALBUM_KEY, MOCK_GENRE_KEY, MOCK_MUSIC_KEY]
        
        # Call target function
        actual = common_tags.read_tags(MOCK_INPUT_PATH)
        
        self.assertIsNone(actual)

class TestCoverHash(unittest.TestCase):
    '''Tests for the newly requested 'cover_hash' function.'''
    @patch('imagehash.phash')
    def test_success_image_present(self, mock_phash: MagicMock) -> None:
        '''Tests that a Tags instance containing an image is hashed with that image.'''
        # Set up mocks
        mock_hash = MagicMock()
        mock_phash.return_value = mock_hash
        
        # Call target function
        tags = create_full_mock_tags()
        actual = tags.cover_hash()
        
        # Assert expectations
        self.assertEqual(actual, mock_hash)
        mock_phash.assert_called_once_with(MOCK_IMAGE)
    
    @patch('imagehash.phash')
    def test_success_image_missing(self, mock_phash: MagicMock) -> None:
        '''Tests that a Tags instance missing an image generates None for the hash.'''
        # Call target function with tags that lack image data
        tags = Tags(MOCK_ARTIST,
                    MOCK_ALBUM,
                    MOCK_TITLE,
                    MOCK_GENRE,
                    MOCK_MUSIC_KEY)
        actual = tags.cover_hash()
        
        # Assert expectations
        self.assertIsNone(actual, 'Expect None value for hash when image is missing.')
        mock_phash.assert_not_called()
    
    @patch('logging.error')
    @patch('imagehash.phash')
    def test_error_hash_failure(self, mock_phash: MagicMock, mock_log_error: MagicMock) -> None:
        '''Tests that a hash failure raises the expected error.'''
        # Set up mocks
        mock_phash.side_effect = Exception()
        
        # Call target function, exepting exception due to the mock error
        tags = create_full_mock_tags()
        with self.assertRaises(ValueError):
            tags.cover_hash()
            
        # Assert expectations
        mock_phash.assert_called_once_with(MOCK_IMAGE)
        mock_log_error.assert_called()
        
class TestEQCoverImage(unittest.TestCase):
    '''Tests for the newly requested 'compare_cover' function.'''
    @patch('src.common_tags.Tags.cover_hash')
    def test_success_same_images(self, mock_cover_hash: MagicMock) -> None:
        '''Tests that comparison for images with the same hash returns True.'''
        # Set up mocks
        mock_cover_hash.return_value = ImageHash(np.array([[0, 0, 0, 1]], dtype=np.bool_))
        
        # Call target function
        tags_lhs = Tags()
        tags_rhs = Tags()
        actual = tags_lhs._eq_cover_image(tags_rhs)
        
        # Assert expectations
        self.assertTrue(actual)
        self.assertEqual(mock_cover_hash.call_count, 2)
        
    @patch('src.common_tags.Tags.cover_hash')
    def test_success_different_images(self, mock_cover_hash: MagicMock) -> None:
        '''Tests that comparison for images with different hashes returns True.'''
        # Set up mocks: two different hash return values
        mock_cover_hash.side_effect = [ImageHash(np.array([[0, 0, 0, 1]], dtype=np.bool_)),
                                       ImageHash(np.array([[1, 0, 0, 0]], dtype=np.bool_))]
        
        # Call target function
        tags_lhs = Tags()
        tags_rhs = Tags()
        actual = tags_lhs._eq_cover_image(tags_rhs)
        
        # Assert expectations
        self.assertFalse(actual)
        self.assertEqual(mock_cover_hash.call_count, 2)
    
    @patch('src.common_tags.Tags.cover_hash')
    def test_success_exists_vs_none(self, mock_cover_hash: MagicMock) -> None:
        '''Tests that comparison between Tags containing an image and Tags missing an image returns False.'''
        # Set up mocks: lhs exists, rhs None.
        mock_cover_hash.side_effect = [ImageHash(np.array([[0, 0, 0, 1]], dtype=np.bool_)),
                                       None]
        
        # Call target function
        tags_lhs = Tags()
        tags_rhs = Tags()
        actual = tags_lhs._eq_cover_image(tags_rhs)
        
        # Assert expectations
        self.assertFalse(actual)
        
    @patch('src.common_tags.Tags.cover_hash')
    def test_success_none_vs_exists(self, mock_cover_hash: MagicMock) -> None:
        '''Tests that comparison between Tags missing an image and Tags containing an image returns False.'''
        # Set up mocks: lhs None, rhs exists
        mock_cover_hash.side_effect = [None,
                                       ImageHash(np.array([[0, 0, 0, 1]], dtype=np.bool_))]
        
        # Call target function
        tags_lhs = Tags()
        tags_rhs = Tags()
        actual = tags_lhs._eq_cover_image(tags_rhs)
        
        # Assert expectations
        self.assertFalse(actual)
        
    @patch('src.common_tags.Tags.cover_hash')
    def test_success_none_vs_none(self, mock_cover_hash: MagicMock) -> None:
        '''Tests that comparison between two Tags instances missing an image returns True.'''
        # Set up mocks: both hashes as None
        mock_cover_hash.side_effect = [None, None]
        
        # Call target function
        tags_lhs = Tags()
        tags_rhs = Tags()
        actual = tags_lhs._eq_cover_image(tags_rhs)
        
        # Assert expectations
        self.assertTrue(actual)
    
    @patch('src.common_tags.Tags.cover_hash')
    def test_error_hash(self, mock_cover_hash: MagicMock) -> None:
        '''Tests that comparison resulting in a hash error raises a value error.'''
        # Set up mocks: hash exception
        mock_cover_hash.side_effect = ValueError()
        
        # Call target function, expecting exception and error log
        tags_lhs = Tags()
        tags_rhs = Tags()
        with self.assertRaises(ValueError):
            tags_lhs._eq_cover_image(tags_rhs)
        mock_cover_hash.assert_called()

