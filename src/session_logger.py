"""
Session Logger for AI Voice Interviewer System
Handles logging, session tracking, and data persistence
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import logging
from config import Config

# Set up logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class QuestionResponse(BaseModel):
    """Model for individual question responses"""
    question_id: str
    question_text: str
    question_topic: str
    question_difficulty: int
    user_answer: str
    transcription_confidence: Optional[float] = None
    llm_score: Optional[int] = None
    llm_feedback: Optional[str] = None
    llm_suggestions: Optional[str] = None
    llm_strengths: List[str] = Field(default_factory=list)
    llm_weaknesses: List[str] = Field(default_factory=list)
    follow_up_question: Optional[str] = None
    follow_up_answer: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    response_duration: Optional[float] = None  # Time taken to answer in seconds

class InterviewSession(BaseModel):
    """Model for complete interview session"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    questions_asked: List[QuestionResponse] = Field(default_factory=list)
    session_summary: Optional[Dict[str, Any]] = None
    total_duration: Optional[float] = None  # Total session duration in seconds

class SessionLogger:
    """Manages session logging and data persistence"""
    
    def __init__(self, session_id: str = None):
        """Initialize session logger"""
        self.session = InterviewSession()
        if session_id:
            self.session.session_id = session_id
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Set up file logging
        self._setup_file_logging()
        
        logger.info(f"Session logger initialized - Session ID: {self.session.session_id}")
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        directories = [Config.LOGS_DIR, Config.SESSIONS_DIR]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _setup_file_logging(self):
        """Set up file logging for this session"""
        log_filename = f"{Config.SESSIONS_DIR}/session_{self.session.session_id}.log"
        
        # Create file handler
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        session_logger = logging.getLogger(f"session_{self.session.session_id}")
        session_logger.addHandler(file_handler)
        session_logger.setLevel(logging.INFO)
        
        self.session_logger = session_logger
        self.session_logger.info(f"Session started - ID: {self.session.session_id}")
    
    def set_user_preferences(self, topics: List[str], difficulty: int, **kwargs):
        """Set user preferences for the session"""
        self.session.user_preferences = {
            "topics": topics,
            "difficulty": difficulty,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        
        interview_duration = kwargs.get('interview_duration', 'Not specified')
        self.session_logger.info(f"User preferences set: topics={topics}, difficulty={difficulty}, duration={interview_duration}")
        
        config_data = {
            "Topics": ", ".join(topics),
            "Difficulty Level": f"{difficulty}/5",
            "Session ID": self.session.session_id
        }
        
        if interview_duration != 'Not specified':
            config_data["Interview Duration"] = f"{interview_duration} minutes"
        
        self.log_to_console("📋 Session Configuration", config_data)
    
    def log_question_asked(self, question_id: str, question_text: str, 
                          question_topic: str, question_difficulty: int):
        """Log when a question is asked"""
        self.session_logger.info(f"Question asked - ID: {question_id}, Topic: {question_topic}")
        
        self.log_to_console("❓ Question Asked", {
            "ID": question_id,
            "Topic": question_topic,
            "Difficulty": f"{question_difficulty}/5",
            "Question": question_text[:100] + "..." if len(question_text) > 100 else question_text
        })
    
    def log_user_response(self, question_id: str, user_answer: str, 
                         transcription_confidence: float = None,
                         response_duration: float = None):
        """Log user's response to a question"""
        # Find the question response or create new one
        question_response = None
        for qr in self.session.questions_asked:
            if qr.question_id == question_id:
                question_response = qr
                break
        
        if question_response:
            question_response.user_answer = user_answer
            question_response.transcription_confidence = transcription_confidence
            question_response.response_duration = response_duration
        
        self.session_logger.info(f"User response logged - Question ID: {question_id}")
        
        self.log_to_console("🎤 User Response", {
            "Question ID": question_id,
            "Response Length": f"{len(user_answer)} characters",
            "Transcription Confidence": f"{transcription_confidence:.2f}" if transcription_confidence else "N/A",
            "Response Time": f"{response_duration:.1f}s" if response_duration else "N/A",
            "Answer Preview": user_answer[:150] + "..." if len(user_answer) > 150 else user_answer
        })
    
    def log_evaluation_result(self, question_id: str, evaluation_result):
        """Log LLM evaluation result"""
        # Find the question response
        question_response = None
        for qr in self.session.questions_asked:
            if qr.question_id == question_id:
                question_response = qr
                break
        
        if question_response and evaluation_result:
            question_response.llm_score = evaluation_result.score
            question_response.llm_feedback = evaluation_result.feedback
            question_response.llm_suggestions = evaluation_result.suggestions
            question_response.llm_strengths = evaluation_result.strengths
            question_response.llm_weaknesses = evaluation_result.weaknesses
            question_response.follow_up_question = evaluation_result.follow_up
        
        self.session_logger.info(f"Evaluation logged - Question ID: {question_id}, Score: {evaluation_result.score}/10")
        
        # Determine performance emoji
        score = evaluation_result.score
        if score >= 9:
            emoji = "🌟"
        elif score >= 7:
            emoji = "✅"
        elif score >= 5:
            emoji = "⚠️"
        else:
            emoji = "❌"
        
        self.log_to_console(f"{emoji} Evaluation Result", {
            "Question ID": question_id,
            "Score": f"{score}/10",
            "Feedback": evaluation_result.feedback[:200] + "..." if len(evaluation_result.feedback) > 200 else evaluation_result.feedback,
            "Key Strengths": ", ".join(evaluation_result.strengths[:3]) if evaluation_result.strengths else "None noted",
            "Areas for Improvement": ", ".join(evaluation_result.weaknesses[:3]) if evaluation_result.weaknesses else "None noted"
        })
        
        if evaluation_result.follow_up:
            self.log_to_console("🔄 Follow-up Question Generated", {
                "Question": evaluation_result.follow_up
            })
    
    def add_question_response(self, question_id: str, question_text: str,
                            question_topic: str, question_difficulty: int,
                            user_answer: str = "", **kwargs):
        """Add a new question response to the session"""
        question_response = QuestionResponse(
            question_id=question_id,
            question_text=question_text,
            question_topic=question_topic,
            question_difficulty=question_difficulty,
            user_answer=user_answer,
            **kwargs
        )
        
        self.session.questions_asked.append(question_response)
        return question_response
    
    def log_follow_up_response(self, question_id: str, follow_up_answer: str):
        """Log response to a follow-up question"""
        # Find the question response
        for qr in self.session.questions_asked:
            if qr.question_id == question_id:
                qr.follow_up_answer = follow_up_answer
                break
        
        self.session_logger.info(f"Follow-up response logged - Question ID: {question_id}")
        
        self.log_to_console("🔄 Follow-up Response", {
            "Question ID": question_id,
            "Answer": follow_up_answer[:150] + "..." if len(follow_up_answer) > 150 else follow_up_answer
        })
    
    def end_session(self):
        """End the current session and generate summary"""
        self.session.end_time = datetime.now()
        self.session.total_duration = (
            self.session.end_time - self.session.start_time
        ).total_seconds()
        
        # Generate session summary
        self.session.session_summary = self._generate_session_summary()
        
        # Save session data
        self._save_session_data()
        
        self.session_logger.info("Session ended")
        
        # Display final summary
        self._display_final_summary()
    
    def _generate_session_summary(self) -> Dict[str, Any]:
        """Generate comprehensive session summary"""
        questions_asked = len(self.session.questions_asked)
        
        if questions_asked == 0:
            return {"error": "No questions were asked in this session"}
        
        # Calculate scores
        scores = [qr.llm_score for qr in self.session.questions_asked if qr.llm_score is not None]
        
        if not scores:
            avg_score = 0
            score_stats = {}
        else:
            avg_score = sum(scores) / len(scores)
            score_stats = {
                "average": round(avg_score, 2),
                "highest": max(scores),
                "lowest": min(scores),
                "total_evaluated": len(scores)
            }
        
        # Topic analysis
        topics_covered = {}
        for qr in self.session.questions_asked:
            topic = qr.question_topic
            if topic not in topics_covered:
                topics_covered[topic] = {"count": 0, "avg_score": 0, "scores": []}
            topics_covered[topic]["count"] += 1
            if qr.llm_score is not None:
                topics_covered[topic]["scores"].append(qr.llm_score)
        
        # Calculate average scores per topic
        for topic_data in topics_covered.values():
            if topic_data["scores"]:
                topic_data["avg_score"] = round(sum(topic_data["scores"]) / len(topic_data["scores"]), 2)
        
        # Performance level
        if avg_score >= 8:
            performance_level = "Excellent"
        elif avg_score >= 6:
            performance_level = "Good"
        elif avg_score >= 4:
            performance_level = "Average"
        else:
            performance_level = "Needs Improvement"
        
        return {
            "session_duration_minutes": round(self.session.total_duration / 60, 2),
            "questions_asked": questions_asked,
            "questions_evaluated": len(scores),
            "score_statistics": score_stats,
            "performance_level": performance_level,
            "topics_covered": topics_covered,
            "user_preferences": self.session.user_preferences,
            "follow_ups_generated": len([qr for qr in self.session.questions_asked if qr.follow_up_question]),
            "follow_ups_answered": len([qr for qr in self.session.questions_asked if qr.follow_up_answer])
        }
    
    def _save_session_data(self):
        """Save session data to JSON file"""
        filename = f"{Config.SESSIONS_DIR}/session_{self.session.session_id}.json"
        
        try:
            # Convert to dict for JSON serialization
            session_dict = self.session.model_dump()
            
            # Convert datetime objects to ISO format strings
            def convert_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime(item) for item in obj]
                return obj
            
            session_dict = convert_datetime(session_dict)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Session data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving session data: {e}")
    
    def _display_final_summary(self):
        """Display final session summary to console"""
        summary = self.session.session_summary
        
        print("\n" + "="*60)
        print("🎯 INTERVIEW SESSION SUMMARY")
        print("="*60)
        
        print(f"📊 Session ID: {self.session.session_id}")
        print(f"⏱️  Duration: {summary['session_duration_minutes']} minutes")
        print(f"❓ Questions Asked: {summary['questions_asked']}")
        print(f"📝 Questions Evaluated: {summary['questions_evaluated']}")
        
        if summary.get('score_statistics'):
            stats = summary['score_statistics']
            print(f"📈 Average Score: {stats['average']}/10")
            print(f"🏆 Highest Score: {stats['highest']}/10")
            print(f"📉 Lowest Score: {stats['lowest']}/10")
            print(f"🎭 Performance Level: {summary['performance_level']}")
        
        print(f"\n📚 Topics Covered:")
        for topic, data in summary['topics_covered'].items():
            avg_score_text = f" (avg: {data['avg_score']}/10)" if data['avg_score'] > 0 else ""
            print(f"  • {topic.replace('_', ' ').title()}: {data['count']} questions{avg_score_text}")
        
        if summary['follow_ups_generated'] > 0:
            print(f"\n🔄 Follow-up Questions: {summary['follow_ups_generated']} generated, {summary['follow_ups_answered']} answered")
        
        print("\n" + "="*60)
        print("Thank you for using the AI Voice Interviewer!")
        print("="*60)
    
    def log_to_console(self, title: str, data: Dict[str, Any]):
        """Log formatted information to console"""
        print(f"\n{title}")
        print("-" * len(title))
        for key, value in data.items():
            print(f"{key}: {value}")
    
    def get_session_data(self) -> InterviewSession:
        """Get current session data"""
        return self.session
    
    def export_session_summary(self, format: str = "json") -> str:
        """Export session summary in specified format"""
        if format.lower() == "json":
            return json.dumps(self.session.session_summary, indent=2)
        elif format.lower() == "text":
            return self._format_text_summary()
        else:
            raise ValueError("Unsupported format. Use 'json' or 'text'")
    
    def _format_text_summary(self) -> str:
        """Format session summary as readable text"""
        summary = self.session.session_summary
        
        text_summary = f"""
AI Voice Interviewer - Session Summary
=====================================

Session ID: {self.session.session_id}
Duration: {summary['session_duration_minutes']} minutes
Questions Asked: {summary['questions_asked']}
Performance Level: {summary['performance_level']}

Score Statistics:
- Average Score: {summary.get('score_statistics', {}).get('average', 'N/A')}/10
- Highest Score: {summary.get('score_statistics', {}).get('highest', 'N/A')}/10
- Lowest Score: {summary.get('score_statistics', {}).get('lowest', 'N/A')}/10

Topics Covered:
"""
        
        for topic, data in summary['topics_covered'].items():
            text_summary += f"- {topic.replace('_', ' ').title()}: {data['count']} questions"
            if data['avg_score'] > 0:
                text_summary += f" (avg: {data['avg_score']}/10)"
            text_summary += "\n"
        
        return text_summary

# Example usage and testing
if __name__ == "__main__":
    # Test the session logger
    logger_test = SessionLogger()
    
    # Set user preferences
    logger_test.set_user_preferences(["programming", "algorithms"], 3)
    
    # Add a question response
    qr = logger_test.add_question_response(
        question_id="q001",
        question_text="What is object-oriented programming?",
        question_topic="programming",
        question_difficulty=3,
        user_answer="OOP is about creating classes and objects..."
    )
    
    # Log evaluation (mock result)
    class MockEvaluation:
        score = 7
        feedback = "Good understanding of basic concepts"
        suggestions = "Add more examples"
        strengths = ["Clear explanation"]
        weaknesses = ["Could be more detailed"]
        follow_up = "Can you give an example?"
    
    logger_test.log_evaluation_result("q001", MockEvaluation())
    
    # End session
    logger_test.end_session()
    
    print("Session logger test completed!")