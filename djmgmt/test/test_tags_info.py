import unittest
from unittest.mock import patch, MagicMock

# Test target imports
from src import tags_info

class TestCompareTags(unittest.TestCase):
    @patch('src.common_tags.read_tags')
    @patch('src.common.collect_paths')
    def test_success_file_match(self, mock_collect_paths: MagicMock, mock_read_tags: MagicMock) -> None:
        # Set up mocks
        mock_collect_paths.side_effect = [
            ['/mock/source/file_0.mp3'],
            ['/mock/compare/file_0.mp3']
        ]
        mock_read_tags.side_effect = [MagicMock(), MagicMock()]
        
        # Call target function
        actual = tags_info.compare_tags('/mock/source', '/mock/compare')
        
        # Assert expectations
        self.assertEqual(actual, [('/mock/source/file_0.mp3', '/mock/compare/file_0.mp3')])
        self.assertEqual(mock_collect_paths.call_count, 2)
        self.assertEqual(mock_read_tags.call_count, 2)
        
    @patch('src.common_tags.read_tags')
    @patch('src.common.collect_paths')
    def test_success_file_difference(self, mock_collect_paths: MagicMock, mock_read_tags: MagicMock) -> None:
        # Set up mocks
        mock_collect_paths.side_effect = [
            ['/mock/source/file_0.mp3'],
            ['/mock/compare/different.mp3']
        ]
        mock_read_tags.side_effect = [MagicMock(), MagicMock()]
        
        # Call target function
        actual = tags_info.compare_tags('/mock/source', '/mock/compare')
        
        # Assert expectations
        self.assertEqual(actual, [])
        self.assertEqual(mock_collect_paths.call_count, 2)
        mock_read_tags.assert_not_called()
        
    @patch('src.common_tags.read_tags')
    @patch('src.common.collect_paths')
    def test_success_read_tags_fail(self, mock_collect_paths: MagicMock, mock_read_tags: MagicMock) -> None:
        # Set up mocks
        mock_collect_paths.side_effect = [
            ['/mock/source/file_0.mp3'],
            ['/mock/compare/file_0.mp3']
        ]
        mock_read_tags.return_value = None
        
        # Call target function
        actual = tags_info.compare_tags('/mock/source', '/mock/compare')
        
        # Assert expectations
        self.assertEqual(actual, [])
        self.assertEqual(mock_collect_paths.call_count, 2)
        self.assertEqual(mock_read_tags.call_count, 2)