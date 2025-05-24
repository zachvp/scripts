import unittest
from unittest.mock import patch, MagicMock, mock_open, call

import sync_media_server
import constants
import subsonic_client
import subprocess

import sync_media_server

# Constants
DATE_PROCESSED_EARLIEST = '2020/01 january/01'
DATE_PROCESSED_PAST     = '2025/05 may/19'
DATE_PROCESSED_CURRENT  = '2025/05 may/20'
DATE_PROCESSED_FUTURE   = '2025/05 may/21'

# Primary test class
class TestIsProcessed(unittest.TestCase):
    # Past dates
    @patch('builtins.open', new_callable=mock_open, read_data=f"sync_date: {DATE_PROCESSED_CURRENT}")
    def test_is_processed_past_contexts_match(self, mock_sync_state: MagicMock) -> None:
        '''Tests that matching date contexts before the processed date are considered processed.'''
        actual = sync_media_server.is_processed(DATE_PROCESSED_PAST, DATE_PROCESSED_PAST)
        self.assertTrue(actual, f"Date context '{DATE_PROCESSED_PAST}' is expected to be already processed.")
        mock_sync_state.assert_called_once()
        
    @patch('builtins.open', new_callable=mock_open, read_data=f"sync_date: {DATE_PROCESSED_CURRENT}")
    def test_is_processed_past_contexts_differ(self, mock_sync_state: MagicMock) -> None:
        '''Tests that different date contexts before the processed date are considered processed.'''
        actual = sync_media_server.is_processed(DATE_PROCESSED_PAST, DATE_PROCESSED_EARLIEST)
        self.assertTrue(actual, f"Date contexts '{DATE_PROCESSED_PAST}' and '{DATE_PROCESSED_EARLIEST}' are expected to be already processed.")
        mock_sync_state.assert_called_once()
    
    # Current dates
    @patch('builtins.open', new_callable=mock_open, read_data=f"sync_date: {DATE_PROCESSED_CURRENT}")
    def test_is_processed_current_contexts_match(self, mock_sync_state: MagicMock) -> None:
        '''Tests that matching date contexts equal to the processed date are considered processed.'''
        actual = sync_media_server.is_processed(DATE_PROCESSED_CURRENT, DATE_PROCESSED_CURRENT)
        self.assertTrue(actual, f"Date context '{DATE_PROCESSED_CURRENT}' is expected to be already processed.")
        mock_sync_state.assert_called_once()
        
    @patch('builtins.open', new_callable=mock_open, read_data=f"sync_date: {DATE_PROCESSED_CURRENT}")
    def test_is_processed_current_contexts_differ(self, mock_sync_state: MagicMock) -> None:
        '''Tests that date contexts that are equal to and before the processed date are considered processed.'''
        actual = sync_media_server.is_processed(DATE_PROCESSED_CURRENT, DATE_PROCESSED_PAST)
        self.assertTrue(actual, f"Date contexts '{DATE_PROCESSED_CURRENT}' and '{DATE_PROCESSED_PAST}' are expected to be already processed.")
        mock_sync_state.assert_called_once()
    
    # Future dates
    @patch('builtins.open', new_callable=mock_open, read_data=f"sync_date: {DATE_PROCESSED_CURRENT}")
    def test_is_processed_future_contexts_match(self, mock_sync_state: MagicMock) -> None:
        '''Tests that matching date contexts later than the processed date are NOT considered processed.'''
        actual = sync_media_server.is_processed(DATE_PROCESSED_FUTURE, DATE_PROCESSED_FUTURE)
        self.assertFalse(actual, f"Date context '{DATE_PROCESSED_FUTURE}' is NOT expected to be already processed.")
        mock_sync_state.assert_called_once()
        
    @patch('builtins.open', new_callable=mock_open, read_data=f"sync_date: {DATE_PROCESSED_CURRENT}")
    def test_is_processed_future_contexts_differ(self, mock_sync_state: MagicMock) -> None:
        '''Tests that date contexts that are after and equal to the processed date are NOT considered processed.'''
        actual = sync_media_server.is_processed(DATE_PROCESSED_FUTURE, DATE_PROCESSED_CURRENT)
        self.assertFalse(actual, f"Date context '{DATE_PROCESSED_FUTURE}' is NOT expected to be already processed.")
        mock_sync_state.assert_called_once()

class TestSyncBatch(unittest.TestCase):
    @patch('encode_tracks.encode_lossy')
    @patch('sync_media_server.transform_implied_path')
    @patch('sync_media_server.transfer_files')
    @patch('subsonic_client.call_endpoint')
    @patch('subsonic_client.handle_response')
    @patch('time.sleep')
    def test_success_full_scan(self,
                               mock_sleep: MagicMock,
                               mock_handle_response: MagicMock,
                               mock_call_endpoint: MagicMock,
                               mock_transfer: MagicMock,
                               mock_transform: MagicMock,
                               mock_encode: MagicMock) -> None:
        '''Tests that the function calls the expected dependencies with the proper parameters in a full scan context.'''
        # Setup for full scan
        batch = [('/source/path1.aiff', '/dest/2023/01 january/01/path1.aiff'),
                 ('/source/path2.aiff', '/dest/2023/01 january/01/path2.aiff')]
        date_context = '2023/01 january/01'
        source = '/source'
        dest = '/dest/2023/01 january/01/path1.aiff'
        full_scan = True
        
        # Configure mocks
        mock_transform.return_value = '/dest/./2023/01 january/01/'
        mock_transfer.return_value = (0, 'success')
        
        # Mock the API responses - expect endpoints to be called 4 times.
        mock_response = MagicMock(ok=True)
        mock_call_endpoint.return_value = mock_response
        
        # First call returns scanning=true, second call returns scanning=false
        mock_handle_response.side_effect = [{'scanning': 'true'}, {'scanning': 'false'}]
        
        # Call the function
        sync_media_server.sync_batch(batch, date_context, source, dest, full_scan)
        
        # Assert that the expected functions are called with expected parameters.
        mock_encode.assert_called_once_with(batch, '.mp3', threads=28)
        mock_transform.assert_called_once_with(dest)
        mock_transfer.assert_called_once_with(mock_transform.return_value, constants.RSYNC_URL, constants.RSYNC_MODULE_NAVIDROME)
        
        # Expect call to start scan, then re-ping when scanning, then stop pinging.
        mock_call_endpoint.assert_has_calls([
            call(subsonic_client.API.START_SCAN, {'fullScan': 'true'}),
            call(subsonic_client.API.GET_SCAN_STATUS),
            call(subsonic_client.API.GET_SCAN_STATUS)
        ])
        mock_sleep.assert_called()

    @patch('encode_tracks.encode_lossy')
    @patch('sync_media_server.transform_implied_path')
    @patch('sync_media_server.transfer_files')
    @patch('subsonic_client.call_endpoint')
    @patch('subsonic_client.handle_response')
    def test_success_quick_scan(self,
                                mock_handle_response: MagicMock,
                                mock_call_endpoint: MagicMock,
                                mock_transfer: MagicMock,
                                mock_transform: MagicMock,
                                mock_encode: MagicMock) -> None:
        '''Tests that the  function calls the expected dependencies with the proper parameters in a quick scan context.'''
        # Setup for quick scan
        batch = [('/source/path1.aiff', '/dest/2023/01 january/01/path1.aiff')]
        date_context = '2023/01 january/01'
        source = '/source'
        dest = '/dest/2023/01 january/01/path1.aiff'
        full_scan = False
        
        # Configure mocks
        mock_transform.return_value = '/dest/./2023/01 january/01/'
        mock_transfer.return_value = (0, 'success')
        
        # Mock the API responses
        mock_response = MagicMock(ok=True)
        mock_call_endpoint.return_value = mock_response
        
        # Return scanning=false immediately to simulate quick scan
        mock_handle_response.return_value = {'scanning': 'false'}
        
        # Call the function
        sync_media_server.sync_batch(batch, date_context, source, dest, full_scan)
        
        # Assertions
        mock_encode.assert_called_once_with(batch, '.mp3', threads=28)
        mock_transform.assert_called_once_with(dest)
        mock_transfer.assert_called_once()
        mock_call_endpoint.assert_called()
        
        # Verify the scan parameter is 'false' for quick scan
        # Expect call to start scan, then re-ping when scanning, then stop pinging.
        mock_call_endpoint.assert_has_calls([
            call(subsonic_client.API.START_SCAN, {'fullScan': 'false'}),
            call(subsonic_client.API.GET_SCAN_STATUS),
        ])

    @patch('encode_tracks.encode_lossy')
    @patch('sync_media_server.transform_implied_path')
    @patch('logging.error')
    def test_error_no_transfer_path(self,
                                    mock_log_error: MagicMock,
                                    mock_transform: MagicMock,
                                    mock_encode: MagicMock) -> None:
        '''Tests that an error is logged when the destination cannot be transformed into a transfer path.'''
        # Setup
        batch = [('/source/path1.aiff', '/dest/path1.aiff')]
        date_context = '2023/01 january/01'
        source = '/source'
        dest = '/dest/path1.aiff'
        full_scan = True
        
        # Configure mock to return None (no valid transfer path)
        mock_transform.return_value = None
        
        # Call the function
        sync_media_server.sync_batch(batch, date_context, source, dest, full_scan)
        
        # Assertions
        mock_encode.assert_called_once_with(batch, '.mp3', threads=28)
        mock_transform.assert_called_once_with(dest)
        mock_log_error.assert_called_once()  # Should log an error about empty transfer path
        
    @patch('encode_tracks.encode_lossy')
    @patch('sync_media_server.transform_implied_path')
    @patch('sync_media_server.transfer_files')
    @patch('subsonic_client.call_endpoint')
    @patch('subsonic_client.handle_response')
    def test_error_api(self,
                       mock_handle_response: MagicMock,
                       mock_call_endpoint: MagicMock,
                       mock_transfer: MagicMock,
                       mock_transform: MagicMock,
                       mock_encode: MagicMock) -> None:
        '''Tests that no exception is thrown and that the correct functions are invoked if the API call fails.'''
        # Setup
        batch = [('/source/path1.aiff', '/dest/2023/01 january/01/path1.aiff')]
        date_context = '2023/01 january/01'
        source = '/source'
        dest = '/dest/2023/01 january/01/path1.aiff'
        
        # Configure mocks
        mock_transform.return_value = '/dest/./2023/01 january/01/'
        mock_transfer.return_value = (0, 'success')
        
        # Mock the API responses
        mock_response = MagicMock(ok=False)
        mock_call_endpoint.return_value = mock_response
        
        # Return scanning=false immediately
        mock_handle_response.return_value = {'scanning': 'false'}
        
        # Call the function, expecting no exception
        try:
            sync_media_server.sync_batch(batch, date_context, source, dest, False)
        except:
            self.fail('No exception expected')
        
        # Assert that only the start scan API was called
        mock_call_endpoint.assert_has_calls([
            call(subsonic_client.API.START_SCAN, {'fullScan': 'false'})
        ])
        
        # Assert that the expected mocks were either called or not
        mock_encode.assert_called_once()
        mock_transform.assert_called_once()
        mock_transfer.assert_called_once()
        mock_handle_response.assert_not_called()
        
class TestTransferFiles(unittest.TestCase):
    @patch('subprocess.run')
    @patch('logging.debug')
    @patch('logging.info')
    def test_success(self,
                     mock_log_info: MagicMock,
                     mock_log_debug: MagicMock,
                     mock_subprocess_run: MagicMock) -> None:
        '''Tests that a call with valid input returns the expected success values and calls the proper functions.'''
        # Setup
        source_path = '/source/2023/01 january/01/'
        dest_address = 'rsync://example.com'
        rsync_module = 'music'
        
        # Configure mock
        process_mock = MagicMock(returncode=0, stdout='Transfer successful')
        mock_subprocess_run.return_value = process_mock
        
        # Call the function
        return_code, output = sync_media_server.transfer_files(source_path, dest_address, rsync_module)
        
        # Assert success
        self.assertEqual(return_code, 0)
        self.assertEqual(output, 'Transfer successful')
        mock_log_info.assert_called_once()
        self.assertEqual(mock_log_debug.call_count, 2)
        
        # Assert that the rsync command was called
        mock_subprocess_run.assert_called_once()
        self.assertEqual(mock_subprocess_run.call_args[0][0][0], 'rsync')

    @patch('subprocess.run')
    @patch('logging.error')
    def test_error_subprocess(self,
                              mock_log_error: MagicMock,
                              mock_subprocess_run: MagicMock) -> None:
        '''Tests that the function returns the expected error information when the subprocess call fails.'''
        # Setup
        source_path = '/source/2023/01 january/01/'
        dest_address = 'rsync://example.com'
        rsync_module = 'music'
        
        # Configure mock to raise an exception
        error_mock = subprocess.CalledProcessError(1, 'rsync')
        error_mock.stderr = 'Connection refused'
        mock_subprocess_run.side_effect = error_mock
        
        # Call the function
        return_code, output = sync_media_server.transfer_files(source_path, dest_address, rsync_module)
        
        # Assertions
        self.assertEqual(return_code, 1)
        self.assertEqual(output, 'Connection refused')
        mock_log_error.assert_called_once()
    
if __name__ == '__main__':
    unittest.main()