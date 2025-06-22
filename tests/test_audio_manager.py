"""
Test cases for Audio Manager
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio_manager import AudioManager

class TestAudioManager(unittest.TestCase):
    """Test cases for AudioManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the Deepgram client to avoid API calls during testing
        with patch('audio_manager.DeepgramClient'):
            self.audio_manager = AudioManager()
    
    @patch('audio_manager.DeepgramClient')
    def test_initialization(self, mock_deepgram):
        """Test AudioManager initialization"""
        audio_manager = AudioManager()
        self.assertIsNotNone(audio_manager.deepgram_client)
        self.assertIsNotNone(audio_manager.audio_config)
    
    def test_audio_config(self):
        """Test audio configuration"""
        config = self.audio_manager.audio_config
        self.assertIn('sample_rate', config)
        self.assertIn('chunk_size', config)
        self.assertIn('channels', config)
        self.assertIn('silence_threshold', config)
        self.assertIn('max_duration', config)
    
    def test_recording_state(self):
        """Test recording state management"""
        self.assertFalse(self.audio_manager.is_recording)
        
        # Test that recording state can be set
        self.audio_manager.is_recording = True
        self.assertTrue(self.audio_manager.is_recording)
    
    @patch('builtins.open', create=True)
    @patch('wave.open')
    def test_play_audio_from_bytes(self, mock_wave, mock_open):
        """Test audio playback functionality"""
        # Mock wave file
        mock_wf = Mock()
        mock_wf.getnframes.return_value = 1000
        mock_wf.getframerate.return_value = 16000
        mock_wf.getnchannels.return_value = 1
        mock_wf.getsampwidth.return_value = 2
        mock_wf.readframes.side_effect = [b'audio_data', b'']
        
        mock_wave.return_value.__enter__.return_value = mock_wf
        
        # Mock PyAudio stream
        mock_stream = Mock()
        self.audio_manager.pyaudio_instance.open.return_value = mock_stream
        self.audio_manager.pyaudio_instance.get_format_from_width.return_value = 1
        
        # Test playback
        test_audio_data = b'test_audio_data'
        try:
            self.audio_manager.play_audio_from_bytes(test_audio_data)
            # If no exception is raised, the test passes
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"play_audio_from_bytes raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()