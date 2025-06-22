"""
AI Voice Interviewer System - Main Application
A modular Python application for conducting voice-based interviews
"""
import asyncio
import sys
import os
from typing import List, Optional
import time

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from src.question_manager import QuestionManager
from src.audio_manager import AudioManager
from src.llm_evaluator import LLMEvaluator
from src.session_logger import SessionLogger
import logging

# Set up logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class AIVoiceInterviewer:
    """Main controller for the AI Voice Interviewer System"""
    
    def __init__(self):
        """Initialize the AI Voice Interviewer system"""
        print("🤖 Initializing AI Voice Interviewer System...")
        
        # Validate configuration
        if not Config.validate_config():
            print("❌ Configuration validation failed. Please check your .env file.")
            sys.exit(1)
        
        # Initialize components
        try:
            self.question_manager = QuestionManager()
            self.audio_manager = AudioManager()
            self.llm_evaluator = LLMEvaluator()
            self.session_logger = SessionLogger()
            
            print("✅ All components initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing components: {e}")
            logger.error(f"Initialization error: {e}")
            sys.exit(1)
    
    def display_welcome(self):
        """Display welcome message and system information"""
        print("\n" + "="*60)
        print("🎤 AI VOICE INTERVIEWER SYSTEM")
        print("="*60)
        print("Welcome to the AI-powered voice interview system!")
        print("This system will:")
        print("• Ask you technical questions based on your preferences")
        print("• Convert questions to speech and play them aloud")
        print("• Record and transcribe your spoken answers")
        print("• Evaluate your responses using AI")
        print("• Provide detailed feedback and suggestions")
        print("• Generate follow-up questions when appropriate")
        print("="*60)
    
    def get_user_preferences(self) -> tuple:
        """Get user preferences for topics and difficulty"""
        print("\n📋 INTERVIEW SETUP")
        print("-" * 20)
        
        # Get available topics
        available_topics = self.question_manager.get_available_topics()
        difficulty_range = self.question_manager.get_difficulty_range()
        
        print(f"Available topics: {', '.join(available_topics)}")
        print(f"Difficulty range: {difficulty_range[0]} - {difficulty_range[1]}")
        
        # Get topic selection
        while True:
            print(f"\nSelect topics (comma-separated) from: {', '.join(available_topics)}")
            print("Or press Enter to include all topics:")
            topic_input = input("Topics: ").strip()
            
            if not topic_input:
                selected_topics = available_topics
                break
            else:
                selected_topics = [topic.strip() for topic in topic_input.split(',')]
                invalid_topics = [t for t in selected_topics if t not in available_topics]
                
                if invalid_topics:
                    print(f"❌ Invalid topics: {', '.join(invalid_topics)}")
                    continue
                else:
                    break
        
        # Get difficulty selection
        while True:
            try:
                difficulty_input = input(f"\nSelect difficulty level ({difficulty_range[0]}-{difficulty_range[1]}): ").strip()
                if not difficulty_input:
                    selected_difficulty = 3  # Default to medium
                    break
                
                selected_difficulty = int(difficulty_input)
                if difficulty_range[0] <= selected_difficulty <= difficulty_range[1]:
                    break
                else:
                    print(f"❌ Please enter a number between {difficulty_range[0]} and {difficulty_range[1]}")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Get interview duration
        while True:
            try:
                duration_input = input(f"\nInterview duration in minutes (default: {Config.DEFAULT_INTERVIEW_DURATION}): ").strip()
                if not duration_input:
                    interview_duration = Config.DEFAULT_INTERVIEW_DURATION
                    break
                
                interview_duration = int(duration_input)
                if Config.MIN_INTERVIEW_DURATION <= interview_duration <= Config.MAX_INTERVIEW_DURATION:
                    break
                else:
                    print(f"❌ Please enter a duration between {Config.MIN_INTERVIEW_DURATION} and {Config.MAX_INTERVIEW_DURATION} minutes")
            except ValueError:
                print("❌ Please enter a valid number")
        
        return selected_topics, selected_difficulty, interview_duration
    
    async def conduct_interview(self, topics: List[str], difficulty: int, interview_duration: int):
        """Conduct the main interview session"""
        print(f"\n🎯 Starting {interview_duration}-minute interview...")
        print("Topics:", ", ".join(topics))
        print(f"Difficulty: {difficulty}/5")
        
        # Set user preferences in session logger
        self.session_logger.set_user_preferences(topics, difficulty, interview_duration=interview_duration)
        
        questions_asked = 0
        interview_start_time = time.time()
        interview_duration_seconds = interview_duration * 60
        
        try:
            while True:
                # Check if interview time has elapsed
                elapsed_time = time.time() - interview_start_time
                if elapsed_time >= interview_duration_seconds:
                    print(f"\n⏰ Interview time ({interview_duration} minutes) has elapsed!")
                    break
                
                remaining_time = interview_duration_seconds - elapsed_time
                remaining_minutes = int(remaining_time // 60)
                remaining_seconds = int(remaining_time % 60)
                
                print(f"\n{'='*60}")
                print(f"QUESTION {questions_asked + 1} | Time Remaining: {remaining_minutes}:{remaining_seconds:02d}")
                print('='*60)
                
                # Select a question
                question = self.question_manager.select_question(
                    topics=topics,
                    difficulty=difficulty
                )
                
                if not question:
                    print("❌ No more questions available with the specified criteria.")
                    break
                
                # Add question to session
                self.session_logger.add_question_response(
                    question_id=question.id,
                    question_text=question.text,
                    question_topic=question.topic,
                    question_difficulty=question.difficulty
                )
                
                # Log question asked
                self.session_logger.log_question_asked(
                    question.id, question.text, question.topic, question.difficulty
                )
                
                # Convert question to speech and play
                print("🔊 Converting question to speech...")
                await self.audio_manager.text_to_speech(
                    f"Question {questions_asked + 1}: {question.text}"
                )
                
                # Record user's answer
                print("\n🎤 Please provide your answer...")
                start_time = time.time()
                
                user_answer = self.audio_manager.record_and_transcribe(
                    "Speak your answer clearly:"
                )
                
                response_duration = time.time() - start_time
                
                if not user_answer:
                    print("❌ Failed to record or transcribe your answer. Skipping question.")
                    continue
                
                # Log user response
                self.session_logger.log_user_response(
                    question.id, user_answer, response_duration=response_duration
                )
                
                # Store evaluation for later processing (don't display now)
                print("📝 Answer recorded. Moving to next question...")
                evaluation_result = self.llm_evaluator.evaluate_answer_sync(
                    question=question.text,
                    expected_answer=question.expected_answer,
                    user_answer=user_answer,
                    topic=question.topic,
                    difficulty=question.difficulty
                )
                
                if evaluation_result:
                    # Log evaluation result (but don't display)
                    self.session_logger.log_evaluation_result(question.id, evaluation_result)
                else:
                    print("⚠️ Failed to evaluate answer, but continuing...")
                
                questions_asked += 1
                
                # Check time again before preparing next question
                elapsed_time = time.time() - interview_start_time
                if elapsed_time >= interview_duration_seconds:
                    print(f"\n⏰ Interview time has elapsed after {questions_asked} questions!")
                    break
                
                # Brief pause between questions
                print("\n⏳ Preparing next question...")
                time.sleep(2)
        
        except KeyboardInterrupt:
            print("\n\n⏹️ Interview interrupted by user.")
        except Exception as e:
            print(f"\n❌ An error occurred during the interview: {e}")
            logger.error(f"Interview error: {e}")
        
        finally:
            # End the session and generate final report
            elapsed_minutes = (time.time() - interview_start_time) / 60
            print(f"\n🏁 Interview completed! Asked {questions_asked} questions in {elapsed_minutes:.1f} minutes.")
            print("🔄 Generating comprehensive interview report...")
            self.session_logger.end_session()
    
    async def _handle_follow_up_question(self, original_question_id: str, follow_up_question: str):
        """Handle a follow-up question"""
        print(f"\n🔄 Follow-up question:")
        
        # Convert follow-up to speech and play
        await self.audio_manager.text_to_speech(follow_up_question)
        
        # Record follow-up answer
        follow_up_answer = self.audio_manager.record_and_transcribe(
            "Please answer the follow-up question:"
        )
        
        if follow_up_answer:
            # Log follow-up response
            self.session_logger.log_follow_up_response(original_question_id, follow_up_answer)
        else:
            print("❌ Failed to record follow-up answer.")
    
    def display_system_info(self):
        """Display system information and statistics"""
        print("\n📊 SYSTEM INFORMATION")
        print("-" * 25)
        
        # Question bank stats
        stats = self.question_manager.get_session_stats()
        print(f"Total questions in bank: {stats['total_questions']}")
        print(f"Available topics: {', '.join(stats['available_topics'])}")
        print(f"Difficulty range: {stats['difficulty_range'][0]}-{stats['difficulty_range'][1]}")
        
        # Audio settings
        audio_config = Config.get_audio_config()
        print(f"Audio sample rate: {audio_config['sample_rate']} Hz")
        print(f"Max recording duration: {audio_config['max_duration']} seconds")
        
        # LLM settings
        openai_config = Config.get_openai_config()
        print(f"LLM model: {openai_config['model']}")
        print(f"Session ID: {self.session_logger.session.session_id}")
    
    async def run_interactive_mode(self):
        """Run the system in interactive mode"""
        self.display_welcome()
        
        while True:
            print("\n🎯 MAIN MENU")
            print("-" * 15)
            print("1. Start Interview")
            print("2. System Information")
            print("3. Test Audio (TTS/STT)")
            print("4. Exit")
            
            choice = input("\nSelect an option (1-4): ").strip()
            
            if choice == "1":
                # Start interview
                topics, difficulty, interview_duration = self.get_user_preferences()
                await self.conduct_interview(topics, difficulty, interview_duration)
                
                # Ask if user wants to continue
                continue_choice = input("\nWould you like to start another interview? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    break
            
            elif choice == "2":
                # Show system information
                self.display_system_info()
            
            elif choice == "3":
                # Test audio
                await self._test_audio_system()
            
            elif choice == "4":
                # Exit
                print("👋 Thank you for using AI Voice Interviewer!")
                break
            
            else:
                print("❌ Invalid choice. Please select 1-4.")
    
    async def _test_audio_system(self):
        """Test the audio system (TTS and STT)"""
        print("\n🔧 AUDIO SYSTEM TEST")
        print("-" * 25)
        
        # Test TTS
        print("Testing Text-to-Speech...")
        test_text = "Hello! This is a test of the text-to-speech system. Can you hear me clearly?"
        await self.audio_manager.text_to_speech(test_text)
        
        # Test STT
        print("\nTesting Speech-to-Text...")
        transcript = self.audio_manager.record_and_transcribe(
            "Please say something to test speech recognition:"
        )
        
        if transcript:
            print(f"✅ Transcription successful: '{transcript}'")
        else:
            print("❌ Transcription failed")
        
        input("\nPress Enter to return to main menu...")

async def main():
    """Main entry point"""
    try:
        # Initialize the system
        interviewer = AIVoiceInterviewer()
        
        # Check if running with command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == "--test":
                # Run in test mode
                print("🧪 Running in test mode...")
                await interviewer._test_audio_system()
            elif sys.argv[1] == "--info":
                # Show system info and exit
                interviewer.display_system_info()
            else:
                print("Usage: python main.py [--test|--info]")
        else:
            # Run in interactive mode
            await interviewer.run_interactive_mode()
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the main application
    asyncio.run(main())