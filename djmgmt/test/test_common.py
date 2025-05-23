import unittest
from unittest.mock import patch, MagicMock
import logging
import os

# Constants
PROJECT_ROOT = os.path.abspath(f"{os.path.dirname(__file__)}/{os.path.pardir}")

# Custom imports
import sys
sys.path.append(PROJECT_ROOT)

from src import common

class CommonTest(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()