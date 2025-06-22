"""
Question Manager for AI Voice Interviewer System
Handles loading, filtering, and selecting questions from the question bank
"""
import json
import random
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from config import Config
import logging

# Set up logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class Question(BaseModel):
    """Question model with validation"""
    id: str
    text: str
    topic: str
    difficulty: int = Field(ge=1, le=5)  # Difficulty from 1-5
    expected_answer: str
    follow_up_questions: List[str] = Field(default_factory=list)

class QuestionBank(BaseModel):
    """Question bank model"""
    questions: List[Question]

class QuestionManager:
    """Manages question bank operations"""
    
    def __init__(self, question_bank_path: str = None):
        """Initialize question manager with question bank file"""
        self.question_bank_path = question_bank_path or Config.QUESTION_BANK_PATH
        self.questions: List[Question] = []
        self.used_questions: List[str] = []  # Track used question IDs
        self.load_questions()
    
    def load_questions(self) -> bool:
        """Load questions from JSON file"""
        try:
            with open(self.question_bank_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                question_bank = QuestionBank(**data)
                self.questions = question_bank.questions
                logger.info(f"Loaded {len(self.questions)} questions from {self.question_bank_path}")
                return True
        except FileNotFoundError:
            logger.error(f"Question bank file not found: {self.question_bank_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in question bank: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading questions: {e}")
            return False
    
    def get_available_topics(self) -> List[str]:
        """Get list of all available topics"""
        topics = list(set(question.topic for question in self.questions))
        
        # console topics for debugging
        print(f"Available topics: {topics}")
        return sorted(topics)
    
    def get_difficulty_range(self) -> tuple:
        """Get the range of difficulty levels available"""
        if not self.questions:
            return (1, 5)
        difficulties = [question.difficulty for question in self.questions]
        return (min(difficulties), max(difficulties))
    
    def filter_questions(self, 
                        topics: List[str] = None, 
                        difficulty: int = None,
                        exclude_used: bool = True) -> List[Question]:
        """Filter questions by topics and difficulty"""
        filtered_questions = self.questions.copy()
        
        # Filter by topics
        if topics:
            filtered_questions = [
                q for q in filtered_questions 
                if q.topic in topics
            ]
        
        # Filter by difficulty
        if difficulty is not None:
            filtered_questions = [
                q for q in filtered_questions 
                if q.difficulty == difficulty
            ]
        
        # Exclude already used questions
        if exclude_used:
            filtered_questions = [
                q for q in filtered_questions 
                if q.id not in self.used_questions
            ]
        
        logger.debug(f"Filtered to {len(filtered_questions)} questions")
        return filtered_questions
    
    def select_question(self, 
                       topics: List[str] = None, 
                       difficulty: int = None,
                       random_selection: bool = True) -> Optional[Question]:
        """Select a question based on criteria"""
        available_questions = self.filter_questions(topics, difficulty)
        
        if not available_questions:
            logger.warning("No questions available matching criteria")
            return None
        
        if random_selection:
            selected_question = random.choice(available_questions)
        else:
            # Select first available question (deterministic)
            selected_question = available_questions[0]
        
        # Mark question as used
        self.used_questions.append(selected_question.id)
        logger.info(f"Selected question {selected_question.id}: {selected_question.text[:50]}...")
        
        return selected_question
    
    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        """Get a specific question by ID"""
        for question in self.questions:
            if question.id == question_id:
                return question
        return None
    
    def reset_used_questions(self):
        """Reset the list of used questions"""
        self.used_questions = []
        logger.info("Reset used questions list")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about the current session"""
        total_questions = len(self.questions)
        used_questions = len(self.used_questions)
        remaining_questions = total_questions - used_questions
        
        topics_used = []
        difficulties_used = []
        
        for question_id in self.used_questions:
            question = self.get_question_by_id(question_id)
            if question:
                topics_used.append(question.topic)
                difficulties_used.append(question.difficulty)
        
        return {
            "total_questions": total_questions,
            "used_questions": used_questions,
            "remaining_questions": remaining_questions,
            "topics_covered": list(set(topics_used)),
            "difficulty_levels_used": list(set(difficulties_used)),
            "available_topics": self.get_available_topics(),
            "difficulty_range": self.get_difficulty_range()
        }
    
    def validate_question_bank(self) -> bool:
        """Validate the loaded question bank"""
        if not self.questions:
            logger.error("No questions loaded")
            return False
        
        # Check for duplicate IDs
        question_ids = [q.id for q in self.questions]
        if len(question_ids) != len(set(question_ids)):
            logger.error("Duplicate question IDs found")
            return False
        
        # Validate each question
        for question in self.questions:
            if not question.text.strip():
                logger.error(f"Question {question.id} has empty text")
                return False
            if not question.expected_answer.strip():
                logger.error(f"Question {question.id} has empty expected answer")
                return False
            if question.difficulty < 1 or question.difficulty > 5:
                logger.error(f"Question {question.id} has invalid difficulty: {question.difficulty}")
                return False
        
        logger.info("Question bank validation passed")
        return True

# Example usage and testing
if __name__ == "__main__":
    # Test the question manager
    qm = QuestionManager()
    
    if qm.validate_question_bank():
        print("Question bank is valid!")
        
        # Show available topics
        topics = qm.get_available_topics()
        print(f"Available topics: {topics}")
        
        # Show difficulty range
        diff_range = qm.get_difficulty_range()
        print(f"Difficulty range: {diff_range[0]} - {diff_range[1]}")
        
        # Select a programming question with difficulty 3
        question = qm.select_question(topics=["programming"], difficulty=3)
        if question:
            print(f"\nSelected question: {question.text}")
            print(f"Expected answer: {question.expected_answer[:100]}...")
            print(f"Follow-up questions: {question.follow_up_questions}")
        
        # Show session stats
        stats = qm.get_session_stats()
        print(f"\nSession stats: {stats}")
    else:
        print("Question bank validation failed!")