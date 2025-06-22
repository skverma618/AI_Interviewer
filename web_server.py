"""
WebSocket Server for AI Voice Interviewer System
Handles real-time audio streaming and interview management
"""
import asyncio
import websockets
import json
import base64
import logging
from typing import Dict, Any
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from question_manager import QuestionManager
from llm_evaluator import LLMEvaluator
from session_logger import SessionLogger
from config import Config
from deepgram import DeepgramClient, PrerecordedOptions, SpeakOptions
import io
import wave

# Set up logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class WebSocketInterviewServer:
    """WebSocket server for handling real-time interview sessions"""
    
    def __init__(self):
        """Initialize the WebSocket server"""
        self.question_manager = QuestionManager()
        self.llm_evaluator = LLMEvaluator()
        self.deepgram_client = DeepgramClient(Config.DEEPGRAM_API_KEY)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("WebSocket Interview Server initialized")
    
    async def handle_client(self, websocket):
        """Handle WebSocket client connections"""
        session_id = None
        try:
            logger.info(f"New client connected from {websocket.remote_address}")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.process_message(data, websocket)
                    
                    if response:
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            if session_id and session_id in self.active_sessions:
                # Clean up session
                del self.active_sessions[session_id]
    
    async def process_message(self, data: Dict[str, Any], websocket) -> Dict[str, Any]:
        """Process incoming WebSocket messages"""
        message_type = data.get("type")
        
        if message_type == "start_session":
            return await self.start_session(data, websocket)
        elif message_type == "get_question":
            return await self.get_question(data)
        elif message_type == "submit_audio":
            return await self.process_audio(data)
        elif message_type == "text_to_speech":
            return await self.text_to_speech(data)
        elif message_type == "get_topics":
            return await self.get_topics()
        elif message_type == "end_session":
            return await self.end_session(data)
        else:
            return {
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }
    
    async def start_session(self, data: Dict[str, Any], websocket) -> Dict[str, Any]:
        """Start a new interview session"""
        try:
            topics = data.get("topics", [])
            difficulty = data.get("difficulty", 3)
            num_questions = data.get("num_questions", 5)
            
            # Create session logger
            session_logger = SessionLogger()
            session_logger.set_user_preferences(topics, difficulty, num_questions=num_questions)
            
            # Store session data
            session_id = session_logger.session.session_id
            self.active_sessions[session_id] = {
                "logger": session_logger,
                "topics": topics,
                "difficulty": difficulty,
                "num_questions": num_questions,
                "questions_asked": 0,
                "websocket": websocket
            }
            
            logger.info(f"Started session {session_id} with topics: {topics}, difficulty: {difficulty}")
            
            return {
                "type": "session_started",
                "session_id": session_id,
                "topics": topics,
                "difficulty": difficulty,
                "num_questions": num_questions
            }
            
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return {
                "type": "error",
                "message": f"Failed to start session: {str(e)}"
            }
    
    async def get_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get the next question for the session"""
        try:
            session_id = data.get("session_id")
            session = self.active_sessions.get(session_id)
            
            if not session:
                return {
                    "type": "error",
                    "message": "Session not found"
                }
            
            # Check if we've reached the question limit
            if session["questions_asked"] >= session["num_questions"]:
                return {
                    "type": "interview_complete",
                    "message": "Interview completed"
                }
            
            # Select a question
            question = self.question_manager.select_question(
                topics=session["topics"],
                difficulty=session["difficulty"]
            )
            
            if not question:
                return {
                    "type": "error",
                    "message": "No more questions available"
                }
            
            # Add question to session
            session["logger"].add_question_response(
                question_id=question.id,
                question_text=question.text,
                question_topic=question.topic,
                question_difficulty=question.difficulty
            )
            
            session["questions_asked"] += 1
            
            return {
                "type": "question",
                "question_id": question.id,
                "question_text": question.text,
                "question_topic": question.topic,
                "question_difficulty": question.difficulty,
                "question_number": session["questions_asked"],
                "total_questions": session["num_questions"]
            }
            
        except Exception as e:
            logger.error(f"Error getting question: {e}")
            return {
                "type": "error",
                "message": f"Failed to get question: {str(e)}"
            }
    
    async def process_audio(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process audio data and return transcription and evaluation"""
        try:
            session_id = data.get("session_id")
            question_id = data.get("question_id")
            audio_data = data.get("audio_data")  # Base64 encoded
            
            session = self.active_sessions.get(session_id)
            if not session:
                return {
                    "type": "error",
                    "message": "Session not found"
                }
            
            # Decode audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Transcribe audio using Deepgram
            transcript = await self.transcribe_audio(audio_bytes)
            
            if not transcript:
                return {
                    "type": "error",
                    "message": "Failed to transcribe audio"
                }
            
            # Log user response
            session["logger"].log_user_response(question_id, transcript)
            
            # Get question details for evaluation
            question = self.question_manager.get_question_by_id(question_id)
            if not question:
                return {
                    "type": "error",
                    "message": "Question not found"
                }
            
            # Evaluate the answer
            evaluation = self.llm_evaluator.evaluate_answer_sync(
                question=question.text,
                expected_answer=question.expected_answer,
                user_answer=transcript,
                topic=question.topic,
                difficulty=question.difficulty
            )
            
            if evaluation:
                # Log evaluation result
                session["logger"].log_evaluation_result(question_id, evaluation)
                
                return {
                    "type": "evaluation",
                    "transcript": transcript,
                    "score": evaluation.score,
                    "feedback": evaluation.feedback,
                    "suggestions": evaluation.suggestions,
                    "strengths": evaluation.strengths,
                    "weaknesses": evaluation.weaknesses,
                    "follow_up": evaluation.follow_up
                }
            else:
                return {
                    "type": "evaluation",
                    "transcript": transcript,
                    "score": 0,
                    "feedback": "Unable to evaluate answer",
                    "suggestions": "Please try again",
                    "strengths": [],
                    "weaknesses": [],
                    "follow_up": None
                }
                
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return {
                "type": "error",
                "message": f"Failed to process audio: {str(e)}"
            }
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio using Deepgram"""
        try:
            logger.info(f"Transcribing audio data of length: {len(audio_data)} bytes")
            
            # Configure STT options
            options = PrerecordedOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                punctuate=True
            )
            
            # Try direct transcription first (audio_data might already be in correct format)
            try:
                response = self.deepgram_client.listen.rest.v("1").transcribe_file(
                    {"buffer": audio_data, "mimetype": "audio/webm"},
                    options
                )
                
                # Extract transcription
                if response and hasattr(response, 'results') and response.results:
                    if response.results.channels and len(response.results.channels) > 0:
                        if response.results.channels[0].alternatives and len(response.results.channels[0].alternatives) > 0:
                            transcript = response.results.channels[0].alternatives[0].transcript
                            if transcript and transcript.strip():
                                logger.info(f"Transcription successful: {transcript[:50]}...")
                                return transcript.strip()
                
                logger.warning("No transcript found in response, trying WAV conversion")
                
            except Exception as e:
                logger.warning(f"Direct transcription failed: {e}, trying WAV conversion")
            
            # Fallback: Convert to WAV format
            try:
                audio_buffer = io.BytesIO()
                with wave.open(audio_buffer, 'wb') as wf:
                    wf.setnchannels(1)  # Mono
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(16000)  # 16kHz
                    wf.writeframes(audio_data)
                
                audio_buffer.seek(0)
                wav_data = audio_buffer.read()
                
                response = self.deepgram_client.listen.rest.v("1").transcribe_file(
                    {"buffer": wav_data, "mimetype": "audio/wav"},
                    options
                )
                
                # Extract transcription
                if response and hasattr(response, 'results') and response.results:
                    if response.results.channels and len(response.results.channels) > 0:
                        if response.results.channels[0].alternatives and len(response.results.channels[0].alternatives) > 0:
                            transcript = response.results.channels[0].alternatives[0].transcript
                            if transcript and transcript.strip():
                                logger.info(f"WAV transcription successful: {transcript[:50]}...")
                                return transcript.strip()
                
                logger.error("No transcript found in WAV response either")
                
            except Exception as e:
                logger.error(f"WAV conversion transcription failed: {e}")
            
            return ""
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""
    
    async def text_to_speech(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert text to speech using Deepgram"""
        try:
            text = data.get("text", "")
            
            if not text:
                return {
                    "type": "error",
                    "message": "No text provided for speech synthesis"
                }
            
            # Configure TTS options
            options = SpeakOptions(
                model="aura-asteria-en",
                encoding="linear16",
                sample_rate=16000
            )
            
            # Generate speech using the new API
            payload = {"text": text}
            
            # Use the new REST API
            response = self.deepgram_client.speak.rest.v("1").stream_memory(
                payload,
                options
            )
            
            if response and hasattr(response, 'content'):
                audio_data = response.content
            elif response and hasattr(response, 'stream'):
                # Handle streaming response
                audio_data = b""
                for chunk in response.stream:
                    audio_data += chunk
            else:
                return {
                    "type": "error",
                    "message": "No audio data received from Deepgram"
                }
            
            if not audio_data:
                return {
                    "type": "error",
                    "message": "Empty audio data generated"
                }
            
            # Encode as base64 for transmission
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                "type": "audio",
                "audio_data": audio_base64
            }
            
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return {
                "type": "error",
                "message": f"Failed to generate speech: {str(e)}"
            }
    
    async def get_topics(self) -> Dict[str, Any]:
        """Get available topics"""
        try:
            topics = self.question_manager.get_available_topics()
            difficulty_range = self.question_manager.get_difficulty_range()
            
            return {
                "type": "topics",
                "topics": topics,
                "difficulty_range": difficulty_range
            }
            
        except Exception as e:
            logger.error(f"Error getting topics: {e}")
            return {
                "type": "error",
                "message": f"Failed to get topics: {str(e)}"
            }
    
    async def end_session(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """End the interview session"""
        try:
            session_id = data.get("session_id")
            session = self.active_sessions.get(session_id)
            
            if not session:
                return {
                    "type": "error",
                    "message": "Session not found"
                }
            
            # End the session and get summary
            session["logger"].end_session()
            summary = session["logger"].session.session_summary
            
            # Clean up
            del self.active_sessions[session_id]
            
            return {
                "type": "session_ended",
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {
                "type": "error",
                "message": f"Failed to end session: {str(e)}"
            }

async def main():
    """Start the WebSocket server"""
    server = WebSocketInterviewServer()
    
    print("🚀 Starting AI Voice Interviewer WebSocket Server...")
    print("Server will be available at: ws://localhost:8765")
    print("Web interface will be available at: http://localhost:8000")
    
    # Start WebSocket server
    start_server = websockets.serve(server.handle_client, "localhost", 8765)
    
    print("✅ WebSocket server started on ws://localhost:8765")
    print("Press Ctrl+C to stop the server")
    
    await start_server
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")