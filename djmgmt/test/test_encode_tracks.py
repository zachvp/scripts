import unittest
import os
from unittest.mock import patch, MagicMock, call, AsyncMock
from typing import cast
from argparse import Namespace

from src import constants

# Test targets
from src import encode_tracks

# Constants
MOCK_INPUT = '/mock/input'
MOCK_OUTPUT = '/mock/output'

class TestEncodeLossless(unittest.IsolatedAsyncioTestCase):    
    @patch('os.path.getsize')
    @patch('builtins.open')
    @patch('src.encode_tracks.ffmpeg_lossless')
    @patch('src.encode_tracks.check_skip_bit_depth')
    @patch('src.encode_tracks.check_skip_sample_rate')
    @patch('os.walk')
    @patch('builtins.input')
    @patch('src.encode_tracks.setup_storage')
    async def test_success_required_arguments(self,
                                              mock_setup_storage: MagicMock,
                                              mock_input: MagicMock,
                                              mock_walk: MagicMock,
                                              mock_skip_sample_rate: MagicMock,
                                              mock_skip_bit_depth: MagicMock,
                                              mock_standardize: MagicMock,
                                              mock_open: MagicMock,
                                              mock_get_size: MagicMock) -> None:
        '''Tests that core dependent calls are made with expected parameters with only positional arguments given.'''
        # Setup mocks
        mock_walk.return_value = [(MOCK_INPUT, [], ['file_0.aif', 'file_1.wav'])]
        mock_skip_bit_depth.return_value = False
        mock_skip_sample_rate.return_value = False
        
        # Call target function, encoding to AIFF
        actual = await encode_tracks.encode_lossless(MOCK_INPUT, MOCK_OUTPUT, '.aiff')
        
        # Assert that methods depending on optional arguments are not called.
        mock_setup_storage.assert_not_called()
        mock_input.assert_not_called()
        mock_walk.assert_called_once_with(MOCK_INPUT)
        
        # Assert that bit depth and sample rate were only checked for the AIF file;
        # WAV files should always be processed without checking this data.
        self.assertTrue(mock_skip_sample_rate.call_count == 1 or mock_skip_bit_depth.call_count == 1)
        
        # Assert expected calls for each input file
        # Something in the test run adds '__iter__' calls to 'mock_standardize', filter these out. Not ideal, but saves time.
        filtered_calls = [c for c in mock_standardize.mock_calls if not len(c) or not c[0].startswith('().__')]
        
        self.assertEqual(filtered_calls, [
            call(f"{MOCK_INPUT}/file_0.aif", f"{MOCK_OUTPUT}/file_0.aiff"),
            call(f"{MOCK_INPUT}/file_1.wav", f"{MOCK_OUTPUT}/file_1.aiff"),
        ])
        
        # Assert no file was opened, as only default 'encode_lossless' arguments were used
        mock_open.assert_not_called()
        
        # Assert that getsize was called for input and output for each track
        self.assertEqual(mock_get_size.call_count, 4)
        
        # Assert the expected function output result
        self.assertEqual(actual, [
            (f"{MOCK_INPUT}/file_0.aif", f"{MOCK_OUTPUT}/file_0.aiff"),
            (f"{MOCK_INPUT}/file_1.wav", f"{MOCK_OUTPUT}/file_1.aiff"),
        ])
        
    @patch('os.path.getsize')
    @patch('builtins.open')
    @patch('src.encode_tracks.ffmpeg_lossless')
    @patch('src.encode_tracks.check_skip_bit_depth')
    @patch('src.encode_tracks.check_skip_sample_rate')
    @patch('os.walk')
    @patch('builtins.input')
    @patch('src.encode_tracks.setup_storage')
    @patch('src.encode_tracks.run_command_async')
    async def test_success_async_single_batch(self,
                                              mock_run_command_async: AsyncMock,
                                              mock_setup_storage: MagicMock,
                                              mock_input: MagicMock,
                                              mock_walk: MagicMock,
                                              mock_skip_sample_rate: MagicMock,
                                              mock_skip_bit_depth: MagicMock,
                                              mock_standardize: MagicMock,
                                              mock_open: MagicMock,
                                              mock_get_size: MagicMock) -> None:
        '''Tests that a single file can be processed asynchrounously.'''
        # Set up mocks
        mock_walk.return_value = [(MOCK_INPUT, [], ['file_0.aif'])]
        mock_skip_bit_depth.return_value = False
        mock_skip_sample_rate.return_value = False
        
        # Call target function, encoding to AIFF
        actual = await encode_tracks.encode_lossless(MOCK_INPUT, MOCK_OUTPUT, '.aiff')
        
        # Assert that methods depending on optional arguments are not called.
        mock_setup_storage.assert_not_called()
        mock_input.assert_not_called()
        mock_walk.assert_called_once_with(MOCK_INPUT)
        
        # Assert that bit depth and sample rate were only checked for the AIF file;
        # WAV files should always be processed without checking this data.
        self.assertTrue(mock_skip_sample_rate.call_count == 1 or mock_skip_bit_depth.call_count == 1)
        
        # Assert expected calls for each input file
        mock_standardize.assert_has_calls([
            call(f"{MOCK_INPUT}/file_0.aif", f"{MOCK_OUTPUT}/file_0.aiff"),
        ])
        
        # Assert no file was opened, as only default 'encode_lossless' arguments were used
        mock_open.assert_not_called()
        
        # Assert that getsize was called for input and output for each track
        self.assertEqual(mock_get_size.call_count, 2)
        
        # Assert the expected function output result
        self.assertEqual(actual, [
            (f"{MOCK_INPUT}/file_0.aif", f"{MOCK_OUTPUT}/file_0.aiff")
        ])
        
        # Async expectations
        mock_run_command_async.assert_called_once()
        
    @patch('os.path.getsize')
    @patch('builtins.open')
    @patch('src.encode_tracks.ffmpeg_lossless')
    @patch('src.encode_tracks.check_skip_bit_depth')
    @patch('src.encode_tracks.check_skip_sample_rate')
    @patch('os.walk')
    @patch('builtins.input')
    @patch('src.encode_tracks.setup_storage')
    @patch('src.encode_tracks.run_command_async')
    async def test_success_async_multiple_batches(self,
                                                  mock_run_command_async: AsyncMock,
                                                  mock_setup_storage: MagicMock,
                                                  mock_input: MagicMock,
                                                  mock_walk: MagicMock,
                                                  mock_skip_sample_rate: MagicMock,
                                                  mock_skip_bit_depth: MagicMock,
                                                  mock_standardize: MagicMock,
                                                  mock_open: MagicMock,
                                                  mock_get_size: MagicMock) -> None:
        '''Test that an amount of files exceeding the expected thread count (4) processes all files.'''
        # Set up mocks
        mock_walk.return_value = [(MOCK_INPUT, [], [f"file_{i}.aif" for i in range(5)])]
        mock_skip_bit_depth.return_value = False
        mock_skip_sample_rate.return_value = False
        
        # Call target function, encoding to AIFF
        actual = await encode_tracks.encode_lossless(MOCK_INPUT, MOCK_OUTPUT, '.aiff')
        
        # Assert that methods depending on optional arguments are not called.
        mock_setup_storage.assert_not_called()
        mock_input.assert_not_called()
        mock_walk.assert_called_once_with(MOCK_INPUT)
        
        # Assert that bit depth and sample rate were only checked for the AIF file;
        # WAV files should always be processed without checking this data.
        self.assertTrue(mock_skip_sample_rate.call_count == 5 or mock_skip_bit_depth.call_count == 5)
        
        # Assert expected calls for each input file
        mock_standardize.assert_has_calls([
            call(f"{MOCK_INPUT}/file_{i}.aif", f"{MOCK_OUTPUT}/file_{i}.aiff") for i in range(5)
        ])
        
        # Assert no file was opened, as only default 'encode_lossless' arguments were used
        mock_open.assert_not_called()
        
        # Assert that getsize was called for input and output for each track
        self.assertEqual(mock_get_size.call_count, 10)
        
        # Assert the expected function output result
        self.assertEqual(actual, [
            (f"{MOCK_INPUT}/file_{i}.aif", f"{MOCK_OUTPUT}/file_{i}.aiff") for i in range(5)
        ])
        
        # Async expectations
        # One task and command should be created for each file
        self.assertEqual(mock_run_command_async.call_count, 5)
    
    @patch('os.path.getsize')
    @patch('builtins.open')
    @patch('src.encode_tracks.ffmpeg_lossless')
    @patch('src.encode_tracks.check_skip_bit_depth')
    @patch('src.encode_tracks.check_skip_sample_rate')
    @patch('os.walk')
    @patch('builtins.input')
    @patch('src.encode_tracks.setup_storage')
    async def test_success_optional_store_path(self,
                                               mock_setup_storage: MagicMock,
                                               mock_input: MagicMock,
                                               mock_walk: MagicMock,
                                               mock_skip_sample_rate: MagicMock,
                                               mock_skip_bit_depth: MagicMock,
                                               mock_standardize: MagicMock,
                                               mock_open: MagicMock,
                                               mock_get_size: MagicMock) -> None:
        '''Tests that passing the optional store_path argument succeeds.'''
        # Setup mocks
        mock_walk.return_value = [(MOCK_INPUT, [], ['file_0.aif', 'file_1.wav'])]
        mock_skip_bit_depth.return_value = False
        mock_skip_sample_rate.return_value = False
        
        # Call target function, encoding to AIFF
        actual = await encode_tracks.encode_lossless(MOCK_INPUT, MOCK_OUTPUT, '.aiff', store_path='/mock/store/path')
        
        # Assert that storage is set up once and opened to write each file and the cumulative file size.
        mock_setup_storage.assert_called_once()
        self.assertEqual(mock_open.call_count, 3)
        
        # Ensure the argument does not disrupt other expected/unexpected calls
        mock_input.assert_not_called()
        mock_standardize.assert_called()
        mock_get_size.assert_called()
        
        # Assert the expected function output result
        self.assertEqual(actual, [
            (f"{MOCK_INPUT}/file_0.aif", f"{MOCK_OUTPUT}/file_0.aiff"),
            (f"{MOCK_INPUT}/file_1.wav", f"{MOCK_OUTPUT}/file_1.aiff"),
        ])
        
    @patch('os.path.getsize')
    @patch('builtins.open')
    @patch('src.encode_tracks.ffmpeg_lossless')
    @patch('src.encode_tracks.check_skip_bit_depth')
    @patch('src.encode_tracks.check_skip_sample_rate')
    @patch('os.walk')
    @patch('builtins.input')
    @patch('src.encode_tracks.setup_storage')
    async def test_success_optional_store_skipped(self,
                                                  mock_setup_storage: MagicMock,
                                                  mock_input: MagicMock,
                                                  mock_walk: MagicMock,
                                                  mock_skip_sample_rate: MagicMock,
                                                  mock_skip_bit_depth: MagicMock,
                                                  mock_standardize: MagicMock,
                                                  mock_open: MagicMock,
                                                  mock_get_size: MagicMock) -> None:
        '''Tests that passing the optional store_skipped argument succeeds.'''
        # Setup mocks
        mock_walk.return_value = [(MOCK_INPUT, [], ['file_0.aif', 'file_1.aiff'])]
        
        # Mock that first file needs encoding, second file does not and will be skipped
        mock_skip_bit_depth.side_effect = [False, True]
        mock_skip_sample_rate.return_value = [False, True]
        
        # Call target function, encoding to AIFF
        actual = await encode_tracks.encode_lossless(MOCK_INPUT, MOCK_OUTPUT, '.aiff', store_path='/mock/store/path', store_skipped=True)
        
        # Assert that storage is set up twice and opened to write each file and the cumulative file size.
        self.assertEqual(mock_setup_storage.call_count, 2)
        self.assertEqual(mock_open.call_count, 2)
        
        # Ensure the argument does not disrupt other expected/unexpected calls
        mock_input.assert_not_called()
        mock_standardize.assert_called()
        mock_get_size.assert_called()
        
        # Assert the expected function output result -- the second file should be skipped
        self.assertEqual(actual, [
            (f"{MOCK_INPUT}/file_0.aif", f"{MOCK_OUTPUT}/file_0.aiff")
        ])
        
    @patch('os.path.getsize')
    @patch('builtins.open')
    @patch('src.encode_tracks.ffmpeg_lossless')
    @patch('src.encode_tracks.check_skip_bit_depth')
    @patch('src.encode_tracks.check_skip_sample_rate')
    @patch('os.walk')
    @patch('builtins.input')
    @patch('src.encode_tracks.setup_storage')
    async def test_success_optional_interactive(self,
                                                mock_setup_storage: MagicMock,
                                                mock_input: MagicMock,
                                                mock_walk: MagicMock,
                                                mock_skip_sample_rate: MagicMock,
                                                mock_skip_bit_depth: MagicMock,
                                                mock_standardize: MagicMock,
                                                mock_open: MagicMock,
                                                mock_get_size: MagicMock) -> None:
        '''Tests that passing the optional interactive argument suceeds.'''
        # Setup mocks
        mock_walk.return_value = [(MOCK_INPUT, [], ['file_0.aif', 'file_1.wav'])]
        mock_skip_bit_depth.return_value = False
        mock_skip_sample_rate.return_value = False
        mock_input.return_value = 'y' # Mock user confirmation
        
        # Call target function, encoding to AIFF
        actual = await encode_tracks.encode_lossless(MOCK_INPUT, MOCK_OUTPUT, '.aiff', interactive=True)
        
        # Ensure the argument does not disrupt other expected/unexpected calls
        mock_setup_storage.assert_not_called
        mock_open.assert_not_called()
        mock_standardize.assert_called()
        mock_get_size.assert_called()
        
        # Ensure that input was requested for each input file
        self.assertEqual(mock_input.call_count, 2)
        
        # Assert the expected function output result
        self.assertEqual(actual, [
            (f"{MOCK_INPUT}/file_0.aif", f"{MOCK_OUTPUT}/file_0.aiff"),
            (f"{MOCK_INPUT}/file_1.wav", f"{MOCK_OUTPUT}/file_1.aiff"),
        ])
    
    @patch('os.path.getsize')
    @patch('builtins.open')
    @patch('subprocess.run')
    @patch('src.encode_tracks.ffmpeg_lossless')
    @patch('src.encode_tracks.check_skip_bit_depth')
    @patch('src.encode_tracks.check_skip_sample_rate')
    @patch('os.walk')
    @patch('builtins.input')
    @patch('src.encode_tracks.setup_storage')
    async def test_success_unsupported_files(self,
                                             mock_setup_storage: MagicMock,
                                             mock_input: MagicMock,
                                             mock_walk: MagicMock,
                                             mock_skip_sample_rate: MagicMock,
                                             mock_skip_bit_depth: MagicMock,
                                             mock_standardize: MagicMock,
                                             mock_run: MagicMock,
                                             mock_open: MagicMock,
                                             mock_get_size: MagicMock) -> None:
        '''Tests that unsupported files are not processed.'''
        # Setup mocks
        mock_walk.return_value = [(MOCK_INPUT, [], ['file_0.foo', 'file_1.flac', 'file_2.jpg'])]
        mock_skip_bit_depth.return_value = False
        mock_skip_sample_rate.return_value = False
        
        # Call target function, encoding to AIFF
        actual = await encode_tracks.encode_lossless(MOCK_INPUT, MOCK_OUTPUT, '.aiff')
        
        # Assert expected calls
        mock_walk.assert_called_once_with(MOCK_INPUT)
        
        # Assert unexpected calls, as most of the functionality should be skipped with unsupported files as input
        mock_setup_storage.assert_not_called()
        mock_input.assert_not_called()
        mock_skip_sample_rate.assert_not_called()
        mock_skip_bit_depth.assert_not_called()
        mock_standardize.assert_not_called()
        mock_run.assert_not_called()
        mock_open.assert_not_called()
        mock_get_size.assert_not_called()
        
        # Assert the expected function output result -- should be empty for unsupported files
        self.assertEqual(actual, [])
    
    @patch('src.encode_tracks.encode_lossless')
    def test_success_cli(self, mock_encode: MagicMock) -> None:
        '''Tests that the CLI wrapper function calls the expected core function with appropriate arguments.'''
        # Call target function
        args = encode_tracks.Namespace(input='/mock/input',
                                       output='/mock/output',
                                       extension='mock_ext',
                                       store_path='/mock/store/path',
                                       store_skipped=True,
                                       interactive=False)
        args = cast(type[encode_tracks.Namespace], args)
        encode_tracks.encode_lossless_cli(args)
        
        # Assert that the existing arguments are passed properly
        expected_args = (args.input,
                         args.output,
                         args.extension,
                         args.store_path,
                         args.store_skipped,
                         args.interactive)
        self.assertEqual(mock_encode.call_args[0][:6], expected_args)

class TestEncodeLossy(unittest.IsolatedAsyncioTestCase):
    @patch('src.encode_tracks.run_command_async')
    @patch('src.encode_tracks.ffmpeg_lossy')
    @patch('src.encode_tracks.guess_cover_stream_specifier')
    @patch('src.encode_tracks.read_ffprobe_json')
    @patch('os.path.exists')
    @patch('os.makedirs')
    async def test_success_required_arguments(self,
                                              mock_makedirs: MagicMock,
                                              mock_path_exists: MagicMock,
                                              mock_read_ffprobe_json: MagicMock,
                                              mock_guess_cover: MagicMock,
                                              mock_ffmpeg_mp3: MagicMock,
                                              mock_run_command_async: AsyncMock) -> None:
        # Set up mocks
        mock_path_exists.return_value = False
        mock_guess_cover.return_value = -1
        
        # Call target function
        SOURCE_FILE = f"{MOCK_INPUT}{os.sep}file_0.aiff"
        mappings = [(SOURCE_FILE, f"{MOCK_OUTPUT}{os.sep}file_0.aiff")]
        await encode_tracks.encode_lossy(mappings, '.mp3')
        
        # Assert expectations
        ## Path does not exist, so expect makedirs to be called
        mock_makedirs.assert_called_once_with(MOCK_OUTPUT)
        
        ## Expect these calls once for the single mapping
        mock_read_ffprobe_json.assert_called_once_with(SOURCE_FILE)
        mock_guess_cover.assert_called_once_with(mock_read_ffprobe_json.return_value)
        mock_ffmpeg_mp3.assert_called_once_with(SOURCE_FILE, f"{MOCK_OUTPUT}{os.sep}file_0.mp3", map_options=f"-map 0:0")
        mock_run_command_async.assert_called_once()
    
    @patch('src.encode_tracks.encode_lossy')
    @patch('src.common.add_output_path')
    @patch('src.common.collect_paths')
    def test_success_cli(self,
                         mock_collect_paths: MagicMock,
                         mock_add_output_path: MagicMock,
                         mock_encode_lossy: MagicMock) -> None:
        
        # Call target function
        args = encode_tracks.Namespace(input=MOCK_INPUT, output=MOCK_OUTPUT, extension='.mp3')
        args = cast(type[encode_tracks.Namespace], args)
        
        encode_tracks.encode_lossy_cli(args)
        
        # Assert expectations
        mock_collect_paths.assert_called_once_with(args.input)
        mock_add_output_path.assert_called_once_with(args.output, mock_collect_paths.return_value, args.input)
        mock_encode_lossy.assert_called_once_with(mock_add_output_path.return_value, args.extension)

class TestMissingArtCLI(unittest.TestCase):
    @patch('src.common.write_paths')
    @patch('src.encode_tracks.find_missing_art_xml')
    def test_success_xml(self,
                         mock_find_missing_art_xml: MagicMock,
                         mock_write_paths: MagicMock) -> None:
        '''Tests that the missing art XML function is called properly and the missing art paths are written.'''
        # Set up mocks
        mock_paths = MagicMock()
        mock_find_missing_art_xml.return_value = mock_paths
        
        # Call target function
        args = encode_tracks.Namespace(function=encode_tracks.Namespace.FUNCTION_MISSING_ART,
                                       input=MOCK_INPUT,
                                       output=MOCK_OUTPUT,
                                       scan_mode=encode_tracks.Namespace.SCAN_MODE_XML)
        encode_tracks.missing_art_cli(args) # type: ignore
        
        # Assert expectations
        mock_find_missing_art_xml.assert_called_once_with(args.input, constants.XPATH_COLLECTION, constants.XPATH_PRUNED, threads=72)
        mock_write_paths.assert_called_once_with(mock_paths, args.output)
        
    @patch('src.common.write_paths')
    @patch('src.encode_tracks.find_missing_art_os')
    def test_success_os(self,
                        mock_find_missing_art_os: MagicMock,
                        mock_write_paths: MagicMock) -> None:
        '''Tests that the missing art OS function is called properly and the missing art paths are written.'''
        # Set up mocks
        mock_paths = MagicMock()
        mock_find_missing_art_os.return_value = mock_paths
        
        # Call target function
        args = Namespace(function=encode_tracks.Namespace.FUNCTION_MISSING_ART,
                         input=MOCK_INPUT,
                         output=MOCK_OUTPUT,
                         scan_mode=encode_tracks.Namespace.SCAN_MODE_OS)
        encode_tracks.missing_art_cli(args) # type: ignore
        
        # Assert expectations
        mock_find_missing_art_os.assert_called_once_with(args.input, threads=72)
        mock_write_paths.assert_called_once_with(mock_paths, args.output)
