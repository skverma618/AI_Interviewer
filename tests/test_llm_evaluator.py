"""
Test cases for LLM Evaluator
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_evaluator import LLMEvaluator, EvaluationResult

class TestLLMEvaluator(unittest.TestCase):
    """Test cases for LLMEvaluator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the ChatOpenAI to avoid API calls during testing
        with patch('llm_evaluator.ChatOpenAI'):
            self.evaluator = LLMEvaluator()
    
    @patch('llm_evaluator.ChatOpenAI')
    def test_initialization(self, mock_openai):
        """Test LLMEvaluator initialization"""
        evaluator = LLMEvaluator()
        self.assertIsNotNone(evaluator.llm)
        self.assertIsNotNone(evaluator.evaluation_prompt)
    
    def test_evaluation_result_model(self):
        """Test EvaluationResult model validation"""
        # Test valid evaluation result
        result = EvaluationResult(
            score=8,
            feedback="Good answer with clear explanation",
            suggestions="Add more examples",
            strengths=["Clear explanation", "Good structure"],
            weaknesses=["Missing examples"]
        )
        
        self.assertEqual(result.score, 8)
        self.assertEqual(result.feedback, "Good answer with clear explanation")
        self.assertEqual(len(result.strengths), 2)
        self.assertEqual(len(result.weaknesses), 1)
    
    def test_evaluation_result_validation(self):
        """Test EvaluationResult score validation"""
        # Test invalid score (too high)
        with self.assertRaises(ValueError):
            EvaluationResult(
                score=15,  # Invalid: > 10
                feedback="Test feedback",
                suggestions="Test suggestions"
            )
        
        # Test invalid score (too low)
        with self.assertRaises(ValueError):
            EvaluationResult(
                score=0,  # Invalid: < 1
                feedback="Test feedback",
                suggestions="Test suggestions"
            )
    
    @patch('llm_evaluator.ChatOpenAI')
    async def test_evaluate_answer_success(self, mock_openai):
        """Test successful answer evaluation"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = '''
        {
            "score": 7,
            "feedback": "Good understanding of the concept",
            "suggestions": "Add more practical examples",
            "follow_up": null,
            "strengths": ["Clear explanation"],
            "weaknesses": ["Could be more detailed"]
        }
        '''
        
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        
        evaluator = LLMEvaluator()
        evaluator.llm = mock_llm
        
        result = await evaluator.evaluate_answer(
            question="What is OOP?",
            expected_answer="Object-oriented programming...",
            user_answer="OOP is about classes and objects",
            topic="programming",
            difficulty=3
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.score, 7)
        self.assertEqual(result.feedback, "Good understanding of the concept")
    
    def test_create_fallback_evaluation(self):
        """Test fallback evaluation creation"""
        evaluator = LLMEvaluator()
        
        result = evaluator._create_fallback_evaluation(
            "This is a test answer with multiple words",
            "LLM response that couldn't be parsed"
        )
        
        self.assertIsInstance(result, EvaluationResult)
        self.assertGreaterEqual(result.score, 1)
        self.assertLessEqual(result.score, 10)
        self.assertIn("Evaluation completed", result.feedback)
    
    def test_get_evaluation_summary(self):
        """Test evaluation summary generation"""
        evaluator = LLMEvaluator()
        
        # Create test evaluations
        evaluations = [
            EvaluationResult(
                score=8, feedback="Good", suggestions="Test",
                strengths=["Clear"], weaknesses=["Brief"]
            ),
            EvaluationResult(
                score=6, feedback="Average", suggestions="Test",
                strengths=["Accurate"], weaknesses=["Incomplete"]
            ),
            EvaluationResult(
                score=9, feedback="Excellent", suggestions="Test",
                strengths=["Comprehensive"], weaknesses=[]
            )
        ]
        
        summary = evaluator.get_evaluation_summary(evaluations)
        
        self.assertEqual(summary["total_questions"], 3)
        self.assertAlmostEqual(summary["average_score"], 7.67, places=1)
        self.assertEqual(summary["max_score"], 9)
        self.assertEqual(summary["min_score"], 6)
        self.assertEqual(summary["performance_level"], "Good")

if __name__ == '__main__':
    unittest.main()