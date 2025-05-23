import unittest
from unittest.mock import patch, MagicMock

import common

class CommonTest(unittest.TestCase):
    @patch('logging.basicConfig')
    @patch('os.makedirs')
    def test_configure_log_default(self, mock_makedirs: MagicMock, mock_basic_config: MagicMock) -> None:
        common.configure_log()
        
        mock_makedirs.assert_called_once_with()

if __name__ == '__main__':
    unittest.main()