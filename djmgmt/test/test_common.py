import unittest
import logging
import os
from unittest.mock import patch, MagicMock
from typing import cast

# Constants
PROJECT_ROOT = os.path.abspath(f"{os.path.dirname(__file__)}/{os.path.pardir}")

# Custom imports
import sys
sys.path.append(PROJECT_ROOT)

from src import common

class TestConfigureLog(unittest.TestCase):
    @patch('logging.basicConfig')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_configure_log_default(self,
                                   mock_makedirs: MagicMock,
                                   mock_path_exists: MagicMock,
                                   mock_basic_config: MagicMock) -> None:
        '''Tests that a default log configuration is created for common.log'''
        # call test target
        common.configure_log()
        
        # assert expectation
        LOG_PATH = f"{PROJECT_ROOT}/src/logs/common.log"
        self.assertEqual(mock_basic_config.call_args.kwargs['filename'], LOG_PATH)
        self.assertEqual(mock_basic_config.call_args.kwargs['level'], logging.DEBUG)
        
    @patch('logging.basicConfig')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_configure_log_custom_args(self,
                                       mock_makedirs: MagicMock,
                                       mock_path_exists: MagicMock,
                                       mock_basic_config: MagicMock) -> None:
        '''Tests that a custom log configuration is respected.'''
        # call test target
        common.configure_log(level=logging.INFO, path=__file__)
        
        # assert expectation
        LOG_PATH = f"{PROJECT_ROOT}/test/logs/test_common.log"
        self.assertEqual(mock_basic_config.call_args.kwargs['filename'], LOG_PATH)
        self.assertEqual(mock_basic_config.call_args.kwargs['level'], logging.INFO)
        
class TestFindDateContext(unittest.TestCase):
    def test_success_basic(self) -> None:
        path = '/data/tracks-output/2022/04 april/24/1-Gloria_Jones_-_Tainted_Love_(single_version).mp3'
        actual = common.find_date_context(path)
        
        self.assertIsNotNone(actual)
        actual = cast(tuple[str, int], actual)
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual, ('2022/04 april/24', 3))
    
    def test_success_tricky_metadata_subpath(self) -> None:
        path = '/Users/user/developer/test-private/data/tracks-output/2024/08 august/18/Paolo Mojo/1983/159678_1983_(Eric_Prydz_Remix).aiff'
        actual = common.find_date_context(path)
        
        self.assertIsNotNone(actual)
        actual = cast(tuple[str, int], actual)
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual, ('2024/08 august/18', 7))
    
    def test_success_invalid_month_name(self):
        path = '/mock/input/2025/08 aug/22/artist/album/track.mp3'
        actual = common.find_date_context(path)
        
        self.assertIsNone(actual)
        
    def test_success_invalid_month_index(self):
        path = '/mock/input/2025/01 august/22/artist/album/track.mp3'
        actual = common.find_date_context(path)
        
        self.assertIsNone(actual)

if __name__ == '__main__':
    unittest.main()