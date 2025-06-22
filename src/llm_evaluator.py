"""
LLM Evaluator for AI Voice Interviewer System
Handles answer evaluation using LangChain and OpenAI GPT
"""
import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
import logging
from config import Config

# Set up logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class EvaluationResult(BaseModel):
    """Model for evaluation results"""
    score: int = Field(ge=1, le=10, description="Score from 1-10")
    feedback: str = Field(description="Detailed feedback on the answer")
    suggestions: str = Field(description="Specific improvement suggestions")
    follow_up: Optional[str] = Field(default=None, description="Optional follow-up question")
    strengths: List[str] = Field(default_factory=list, description="Answer strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Areas for improvement")

class LLMEvaluator:
    """Evaluates interview answers using LangChain and OpenAI GPT"""
    
    def __init__(self):
        """Initialize the LLM evaluator"""
        self.openai_config = Config.get_openai_config()
        
        # Initialize LangChain ChatOpenAI
        self.llm = ChatOpenAI(
            api_key=self.openai_config["api_key"],
            model=self.openai_config["model"],
            temperature=self.openai_config["temperature"],
            max_tokens=self.openai_config["max_tokens"]
        )
        
        # Create evaluation prompt template
        self.evaluation_prompt = self._create_evaluation_prompt()
        
        logger.info(f"LLM Evaluator initialized with model: {self.openai_config['model']}")
    
    def _create_evaluation_prompt(self) -> ChatPromptTemplate:
        """Create the evaluation prompt template"""
        system_message = """You are an expert technical interviewer evaluating candidate responses. 
        Your role is to provide fair, constructive, and detailed feedback on interview answers.
        
        Evaluation Criteria:
        1. Accuracy: Is the answer technically correct?
        2. Completeness: Does it cover the key concepts?
        3. Clarity: Is the explanation clear and well-structured?
        4. Depth: Does it show understanding of underlying principles?
        5. Examples: Are relevant examples provided when appropriate?
        
        Scoring Guidelines:
        - 9-10: Excellent - Comprehensive, accurate, clear with good examples
        - 7-8: Good - Mostly accurate and complete with minor gaps
        - 5-6: Average - Basic understanding but missing key details
        - 3-4: Below Average - Some understanding but significant gaps
        - 1-2: Poor - Major inaccuracies or very incomplete
        
        Always provide constructive feedback and specific suggestions for improvement."""
        
        human_message = """Please evaluate the following interview answer:

        **Question:** {question}
        
        **Expected Answer:** {expected_answer}
        
        **Candidate's Answer:** {user_answer}
        
        **Question Topic:** {topic}
        **Question Difficulty:** {difficulty}/5
        
        Please provide your evaluation in the following JSON format:
        {{
            "score": <integer from 1-10>,
            "feedback": "<detailed feedback on accuracy and completeness>",
            "suggestions": "<specific improvement suggestions>",
            "follow_up": "<optional follow-up question if answer needs clarification, or null>",
            "strengths": ["<strength1>", "<strength2>"],
            "weaknesses": ["<weakness1>", "<weakness2>"]
        }}
        
        Ensure your response is valid JSON and provide constructive, helpful feedback."""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message)
        ])
    
    async def evaluate_answer(self, 
                            question: str,
                            expected_answer: str,
                            user_answer: str,
                            topic: str = "general",
                            difficulty: int = 3) -> Optional[EvaluationResult]:
        """
        Evaluate a user's answer against the expected answer
        
        Args:
            question: The interview question
            expected_answer: The expected/ideal answer
            user_answer: The candidate's actual answer
            topic: Question topic for context
            difficulty: Question difficulty level (1-5)
            
        Returns:
            EvaluationResult object or None if evaluation failed
        """
        try:
            logger.info(f"Evaluating answer for question: {question[:50]}...")
            
            # Format the prompt
            formatted_prompt = self.evaluation_prompt.format_messages(
                question=question,
                expected_answer=expected_answer,
                user_answer=user_answer,
                topic=topic,
                difficulty=difficulty
            )
            
            # Get LLM response
            response = await self.llm.ainvoke(formatted_prompt)
            response_text = response.content.strip()
            
            logger.debug(f"LLM response: {response_text}")
            
            # Parse JSON response
            try:
                evaluation_data = json.loads(response_text)
                evaluation_result = EvaluationResult(**evaluation_data)
                
                logger.info(f"Answer evaluated - Score: {evaluation_result.score}/10")
                return evaluation_result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Response text: {response_text}")
                
                # Fallback: create a basic evaluation
                return self._create_fallback_evaluation(user_answer, response_text)
                
        except Exception as e:
            logger.error(f"Error in answer evaluation: {e}")
            return None
    
    def _create_fallback_evaluation(self, user_answer: str, llm_response: str) -> EvaluationResult:
        """Create a fallback evaluation when JSON parsing fails"""
        # Basic scoring based on answer length and content
        score = min(max(len(user_answer.split()) // 5, 1), 10)  # Rough scoring
        
        return EvaluationResult(
            score=score,
            feedback=f"Evaluation completed. {llm_response[:200]}...",
            suggestions="Please provide more detailed explanations and examples.",
            follow_up=None,
            strengths=["Provided an answer"],
            weaknesses=["Could be more detailed"]
        )
    
    def evaluate_answer_sync(self, 
                           question: str,
                           expected_answer: str,
                           user_answer: str,
                           topic: str = "general",
                           difficulty: int = 3) -> Optional[EvaluationResult]:
        """
        Synchronous version of evaluate_answer for easier integration
        """
        import asyncio
        
        try:
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async evaluation
            if loop.is_running():
                # If loop is already running, create a new one
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.evaluate_answer(question, expected_answer, user_answer, topic, difficulty)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.evaluate_answer(question, expected_answer, user_answer, topic, difficulty)
                )
                
        except Exception as e:
            logger.error(f"Error in synchronous evaluation: {e}")
            return None
    
    def generate_follow_up_question(self, 
                                  original_question: str,
                                  user_answer: str,
                                  topic: str) -> Optional[str]:
        """
        Generate a follow-up question based on the user's answer
        
        Args:
            original_question: The original interview question
            user_answer: The candidate's answer
            topic: Question topic
            
        Returns:
            Follow-up question or None
        """
        try:
            follow_up_prompt = f"""Based on the following interview exchange, generate a relevant follow-up question that:
            1. Probes deeper into the topic
            2. Tests practical application
            3. Clarifies any unclear points
            4. Is appropriate for the topic: {topic}
            
            Original Question: {original_question}
            Candidate's Answer: {user_answer}
            
            Generate only the follow-up question, no additional text:"""
            
            messages = [HumanMessage(content=follow_up_prompt)]
            response = self.llm.invoke(messages)
            
            follow_up = response.content.strip()
            if follow_up and len(follow_up) > 10:  # Basic validation
                logger.info(f"Generated follow-up question: {follow_up}")
                return follow_up
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating follow-up question: {e}")
            return None
    
    def get_evaluation_summary(self, evaluations: List[EvaluationResult]) -> Dict[str, Any]:
        """
        Generate a summary of multiple evaluations
        
        Args:
            evaluations: List of evaluation results
            
        Returns:
            Summary statistics and insights
        """
        if not evaluations:
            return {"error": "No evaluations provided"}
        
        scores = [eval_result.score for eval_result in evaluations]
        
        # Calculate statistics
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        
        # Collect all strengths and weaknesses
        all_strengths = []
        all_weaknesses = []
        
        for evaluation in evaluations:
            all_strengths.extend(evaluation.strengths)
            all_weaknesses.extend(evaluation.weaknesses)
        
        # Count frequency of strengths and weaknesses
        strength_counts = {}
        weakness_counts = {}
        
        for strength in all_strengths:
            strength_counts[strength] = strength_counts.get(strength, 0) + 1
        
        for weakness in all_weaknesses:
            weakness_counts[weakness] = weakness_counts.get(weakness, 0) + 1
        
        # Performance categorization
        if avg_score >= 8:
            performance_level = "Excellent"
        elif avg_score >= 6:
            performance_level = "Good"
        elif avg_score >= 4:
            performance_level = "Average"
        else:
            performance_level = "Needs Improvement"
        
        return {
            "total_questions": len(evaluations),
            "average_score": round(avg_score, 2),
            "max_score": max_score,
            "min_score": min_score,
            "performance_level": performance_level,
            "score_distribution": {
                "excellent (9-10)": len([s for s in scores if s >= 9]),
                "good (7-8)": len([s for s in scores if 7 <= s <= 8]),
                "average (5-6)": len([s for s in scores if 5 <= s <= 6]),
                "below_average (3-4)": len([s for s in scores if 3 <= s <= 4]),
                "poor (1-2)": len([s for s in scores if s <= 2])
            },
            "common_strengths": sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "common_weaknesses": sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "recommendations": self._generate_recommendations(avg_score, weakness_counts)
        }
    
    def _generate_recommendations(self, avg_score: float, weakness_counts: Dict[str, int]) -> List[str]:
        """Generate recommendations based on performance"""
        recommendations = []
        
        if avg_score < 5:
            recommendations.append("Focus on fundamental concepts and basic understanding")
            recommendations.append("Practice explaining technical concepts clearly")
        elif avg_score < 7:
            recommendations.append("Work on providing more detailed explanations")
            recommendations.append("Include practical examples in your answers")
        else:
            recommendations.append("Continue building on your strong foundation")
            recommendations.append("Focus on advanced topics and edge cases")
        
        # Add specific recommendations based on common weaknesses
        common_weaknesses = sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        for weakness, count in common_weaknesses:
            if count > 1:  # Only include if it's a recurring issue
                recommendations.append(f"Address recurring issue: {weakness}")
        
        return recommendations

# Example usage and testing
if __name__ == "__main__":
    async def test_llm_evaluator():
        """Test the LLM evaluator functionality"""
        evaluator = LLMEvaluator()
        
        # Test evaluation
        question = "What is object-oriented programming?"
        expected_answer = "OOP is a programming paradigm based on objects containing data and methods..."
        user_answer = "Object-oriented programming is about creating classes and objects. It has inheritance and encapsulation."
        
        print("Testing answer evaluation...")
        result = await evaluator.evaluate_answer(
            question=question,
            expected_answer=expected_answer,
            user_answer=user_answer,
            topic="programming",
            difficulty=3
        )
        
        if result:
            print(f"Score: {result.score}/10")
            print(f"Feedback: {result.feedback}")
            print(f"Suggestions: {result.suggestions}")
            print(f"Strengths: {result.strengths}")
            print(f"Weaknesses: {result.weaknesses}")
            if result.follow_up:
                print(f"Follow-up: {result.follow_up}")
        else:
            print("Evaluation failed")
    
    # Run the test
    import asyncio
    asyncio.run(test_llm_evaluator())