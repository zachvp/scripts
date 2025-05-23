import unittest
from unittest.mock import patch, MagicMock

import sys
sys.path.append('/Users/zachvp/developer/scripts/djmgmt') # TODO: refactor so no reliance on abs path

from src import common

class CommonTest(unittest.TestCase):
    @patch('logging.basicConfig')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_configure_log_default(self, mock_makedirs: MagicMock, mock_path_exists: MagicMock, mock_basic_config: MagicMock) -> None:        
        # set up scenario
        mock_path_exists.return_value = False
        
        # call test target
        common.configure_log()
        
        # assert expectation
        log_path = '/Users/zachvp/developer/scripts/djmgmt/src/logs'
        self.assertEqual(mock_basic_config.call_args.kwargs['filename'], f"{log_path}/common.log")

if __name__ == '__main__':
    unittest.main()