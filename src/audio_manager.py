"""
Audio Manager for AI Voice Interviewer System
Handles TTS, STT, audio recording and playback using Deepgram
"""
import asyncio
import pyaudio
import wave
import io
import time
import threading
from typing import Optional, Callable, Any
from deepgram import DeepgramClient, PrerecordedOptions, SpeakOptions
import logging
from config import Config

# Set up logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class AudioManager:
    """Manages all audio operations including TTS, STT, recording, and playback"""
    
    def __init__(self):
        """Initialize audio manager with Deepgram client"""
        self.deepgram_client = DeepgramClient(Config.DEEPGRAM_API_KEY)
        self.audio_config = Config.get_audio_config()
        self.pyaudio_instance = pyaudio.PyAudio()
        self.is_recording = False
        self.recording_thread = None
        self.recorded_audio = None
        
        logger.info("Audio Manager initialized")
    
    def __del__(self):
        """Cleanup PyAudio instance"""
        if hasattr(self, 'pyaudio_instance'):
            self.pyaudio_instance.terminate()
    
    async def text_to_speech(self, text: str, play_immediately: bool = True) -> Optional[bytes]:
        """
        Convert text to speech using Deepgram TTS
        
        Args:
            text: Text to convert to speech
            play_immediately: Whether to play the audio immediately
            
        Returns:
            Audio bytes if successful, None otherwise
        """
        try:
            logger.info(f"Converting text to speech: {text[:50]}...")
            
            # Configure TTS options
            options = SpeakOptions(
                model="aura-asteria-en",  # High-quality English voice
                encoding="linear16",
                sample_rate=self.audio_config["sample_rate"]
            )
            
            # Generate speech using the correct Deepgram API format
            payload = {"text": text}
            response = self.deepgram_client.speak.v("1").stream(payload, options)
            
            # Collect audio data from the stream
            audio_data = b""
            for chunk in response:
                audio_data += chunk
            
            if play_immediately:
                self.play_audio_from_bytes(audio_data)
            
            logger.info("Text-to-speech conversion completed")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return None
    
    def play_audio_from_bytes(self, audio_data: bytes):
        """Play audio from bytes data"""
        try:
            # Create a BytesIO object from audio data
            audio_stream = io.BytesIO(audio_data)
            
            # Open the audio stream as a wave file
            with wave.open(audio_stream, 'rb') as wf:
                # Get audio parameters
                frames = wf.getnframes()
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                
                # Open PyAudio stream for playback
                stream = self.pyaudio_instance.open(
                    format=self.pyaudio_instance.get_format_from_width(sample_width),
                    channels=channels,
                    rate=sample_rate,
                    output=True
                )
                
                # Read and play audio in chunks
                chunk_size = 1024
                data = wf.readframes(chunk_size)
                
                while data:
                    stream.write(data)
                    data = wf.readframes(chunk_size)
                
                # Close the stream
                stream.stop_stream()
                stream.close()
                
            logger.info("Audio playback completed")
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    def start_recording(self, callback: Optional[Callable] = None) -> bool:
        """
        Start recording audio from microphone
        
        Args:
            callback: Optional callback function to call when recording stops
            
        Returns:
            True if recording started successfully, False otherwise
        """
        if self.is_recording:
            logger.warning("Recording already in progress")
            return False
        
        try:
            self.is_recording = True
            self.recorded_audio = []
            
            # Start recording in a separate thread
            self.recording_thread = threading.Thread(
                target=self._record_audio_thread,
                args=(callback,)
            )
            self.recording_thread.start()
            
            logger.info("Audio recording started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            self.is_recording = False
            return False
    
    def stop_recording(self) -> Optional[bytes]:
        """
        Stop recording and return recorded audio
        
        Returns:
            Recorded audio as bytes, or None if no recording
        """
        if not self.is_recording:
            logger.warning("No recording in progress")
            return None
        
        self.is_recording = False
        
        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join()
        
        if self.recorded_audio:
            # Convert recorded frames to bytes
            audio_data = b''.join(self.recorded_audio)
            logger.info(f"Recording stopped, captured {len(audio_data)} bytes")
            return audio_data
        
        return None
    
    def _record_audio_thread(self, callback: Optional[Callable] = None):
        """Internal method to handle audio recording in a separate thread"""
        try:
            # Open audio stream for recording
            stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.audio_config["channels"],
                rate=self.audio_config["sample_rate"],
                input=True,
                frames_per_buffer=self.audio_config["chunk_size"]
            )
            
            silence_counter = 0
            silence_threshold_frames = int(
                self.audio_config["silence_threshold"] * 
                self.audio_config["sample_rate"] / 
                self.audio_config["chunk_size"]
            )
            
            max_frames = int(
                self.audio_config["max_duration"] * 
                self.audio_config["sample_rate"] / 
                self.audio_config["chunk_size"]
            )
            
            frame_count = 0
            
            logger.info("Recording audio... (speak now)")
            
            while self.is_recording and frame_count < max_frames:
                try:
                    data = stream.read(self.audio_config["chunk_size"], exception_on_overflow=False)
                    self.recorded_audio.append(data)
                    frame_count += 1
                    
                    # Simple silence detection (basic amplitude check)
                    # Convert bytes to integers for amplitude calculation
                    import struct
                    audio_samples = struct.unpack(f'{len(data)//2}h', data)
                    amplitude = max(abs(sample) for sample in audio_samples) if audio_samples else 0
                    
                    if amplitude < 1000:  # Adjust threshold as needed
                        silence_counter += 1
                    else:
                        silence_counter = 0
                    
                    # Stop recording if silence detected for too long
                    if silence_counter > silence_threshold_frames:
                        logger.info("Silence detected, stopping recording")
                        break
                        
                except Exception as e:
                    logger.error(f"Error reading audio data: {e}")
                    break
            
            # Close the stream
            stream.stop_stream()
            stream.close()
            
            self.is_recording = False
            
            if callback:
                callback()
                
        except Exception as e:
            logger.error(f"Error in recording thread: {e}")
            self.is_recording = False
    
    async def speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """
        Convert audio to text using Deepgram STT
        
        Args:
            audio_data: Audio data as bytes
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            logger.info("Converting speech to text...")
            
            # Create a BytesIO buffer from audio data
            audio_buffer = io.BytesIO()
            
            # Create a proper WAV file in memory
            with wave.open(audio_buffer, 'wb') as wf:
                wf.setnchannels(self.audio_config["channels"])
                wf.setsampwidth(2)  # 16-bit audio
                wf.setframerate(self.audio_config["sample_rate"])
                wf.writeframes(audio_data)
            
            # Reset buffer position
            audio_buffer.seek(0)
            
            # Configure STT options
            options = PrerecordedOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                punctuate=True,
                diarize=False
            )
            
            # Transcribe audio
            response = self.deepgram_client.listen.prerecorded.v("1").transcribe_file(
                {"buffer": audio_buffer.read(), "mimetype": "audio/wav"},
                options
            )
            
            # Extract transcription
            if response.results and response.results.channels:
                transcript = response.results.channels[0].alternatives[0].transcript
                confidence = response.results.channels[0].alternatives[0].confidence
                
                logger.info(f"Transcription completed with confidence: {confidence:.2f}")
                logger.info(f"Transcribed text: {transcript}")
                
                return transcript.strip() if transcript else None
            else:
                logger.warning("No transcription results received")
                return None
                
        except Exception as e:
            logger.error(f"Error in speech-to-text: {e}")
            return None
    
    def record_and_transcribe(self, prompt_text: str = "Please speak your answer:") -> Optional[str]:
        """
        Record audio and transcribe it in one operation
        
        Args:
            prompt_text: Text to display/announce before recording
            
        Returns:
            Transcribed text or None if failed
        """
        print(f"\n{prompt_text}")
        print("Recording will start in 2 seconds...")
        time.sleep(2)
        
        # Start recording
        recording_complete = threading.Event()
        
        def on_recording_complete():
            recording_complete.set()
        
        if not self.start_recording(callback=on_recording_complete):
            return None
        
        print("🎤 Recording... (speak now, will auto-stop after silence)")
        print("Press Ctrl+C to stop recording manually")
        
        try:
            # Wait for recording to complete (either by silence or manual stop)
            recording_complete.wait()
        except KeyboardInterrupt:
            print("\nStopping recording...")
            self.stop_recording()
        
        # Get recorded audio
        audio_data = self.stop_recording()
        if not audio_data:
            print("No audio recorded")
            return None
        
        print("🔄 Transcribing audio...")
        
        # Transcribe audio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            transcript = loop.run_until_complete(self.speech_to_text(audio_data))
            return transcript
        finally:
            loop.close()

# Example usage and testing
if __name__ == "__main__":
    async def test_audio_manager():
        """Test the audio manager functionality"""
        audio_manager = AudioManager()
        
        # Test TTS
        print("Testing Text-to-Speech...")
        test_text = "Hello! This is a test of the text-to-speech functionality."
        await audio_manager.text_to_speech(test_text)
        
        # Test recording and transcription
        print("\nTesting Speech-to-Text...")
        transcript = audio_manager.record_and_transcribe("Please say something for testing:")
        
        if transcript:
            print(f"You said: {transcript}")
        else:
            print("Failed to transcribe audio")
    
    # Run the test
    asyncio.run(test_audio_manager())