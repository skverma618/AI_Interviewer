"""
Test cases for Question Manager
"""
import unittest
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from question_manager import QuestionManager, Question

class TestQuestionManager(unittest.TestCase):
    """Test cases for QuestionManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.qm = QuestionManager()
    
    def test_load_questions(self):
        """Test loading questions from JSON file"""
        self.assertTrue(len(self.qm.questions) > 0)
        self.assertIsInstance(self.qm.questions[0], Question)
    
    def test_get_available_topics(self):
        """Test getting available topics"""
        topics = self.qm.get_available_topics()
        self.assertIsInstance(topics, list)
        self.assertTrue(len(topics) > 0)
    
    def test_filter_questions(self):
        """Test filtering questions by topic and difficulty"""
        # Test filtering by topic
        programming_questions = self.qm.filter_questions(topics=["programming"])
        self.assertTrue(all(q.topic == "programming" for q in programming_questions))
        
        # Test filtering by difficulty
        easy_questions = self.qm.filter_questions(difficulty=2)
        self.assertTrue(all(q.difficulty == 2 for q in easy_questions))
    
    def test_select_question(self):
        """Test selecting a question"""
        question = self.qm.select_question(topics=["programming"], difficulty=3)
        if question:  # Only test if questions are available
            self.assertEqual(question.topic, "programming")
            self.assertEqual(question.difficulty, 3)
            self.assertIn(question.id, self.qm.used_questions)
    
    def test_validate_question_bank(self):
        """Test question bank validation"""
        self.assertTrue(self.qm.validate_question_bank())

if __name__ == '__main__':
    unittest.main()