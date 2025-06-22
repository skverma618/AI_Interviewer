"""
AI Conversation Manager for Conversational Interview System
Handles intent recognition, response generation, and conversation flow
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.llm_evaluator import LLMEvaluator

logger = logging.getLogger(__name__)

class ConversationState:
    """Tracks the state of an ongoing conversation"""
    
    def __init__(self):
        self.current_question = None
        self.awaiting_answer = True
        self.follow_up_count = 0
        self.max_follow_ups = 3
        self.conversation_history = []
        self.user_confusion_signals = []
        self.topics_covered = {}
        self.interview_context = {}
        self.start_time = datetime.now()
        self.duration_minutes = 30
        self.questions_asked = 0
        
    def add_exchange(self, user_input: str, ai_response: str, intent: str = None):
        """Add a conversation exchange to history"""
        exchange = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'ai_response': ai_response,
            'intent': intent,
            'question_number': self.questions_asked
        }
        self.conversation_history.append(exchange)
        
    def get_remaining_time(self) -> float:
        """Get remaining interview time in minutes"""
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        return max(0, self.duration_minutes - elapsed)
        
    def get_context_summary(self) -> str:
        """Get a summary of conversation context for AI"""
        recent_exchanges = self.conversation_history[-5:] if self.conversation_history else []
        context = {
            'questions_asked': self.questions_asked,
            'follow_up_count': self.follow_up_count,
            'remaining_time': self.get_remaining_time(),
            'recent_conversation': recent_exchanges,
            'topics_covered': list(self.topics_covered.keys()),
            'current_question': self.current_question
        }
        return json.dumps(context, indent=2)

class AIConversationManager:
    """Manages AI-powered conversational interview flow"""
    
    def __init__(self, question_bank_context: List[Dict], llm_evaluator: LLMEvaluator):
        self.question_bank = question_bank_context
        self.llm = llm_evaluator
        self.conversation_state = ConversationState()
        
    def process_user_speech(self, transcript: str, session_context: Dict) -> Dict[str, Any]:
        """
        Main entry point: analyze user speech and generate appropriate response
        """
        try:
            # Update conversation state with session context
            self._update_state_from_session(session_context)
            
            # Analyze user intent
            intent = self._analyze_intent(transcript)
            logger.info(f"Detected intent: {intent} for transcript: {transcript[:50]}...")
            
            # Generate appropriate response based on intent
            if intent == "answering_question":
                response = self._handle_answer(transcript)
            elif intent == "asking_question":
                response = self._handle_user_question(transcript)
            elif intent == "seeking_clarification":
                response = self._handle_clarification_request(transcript)
            elif intent == "confused_or_stuck":
                response = self._handle_confusion(transcript)
            else:
                # Default: treat as answer
                response = self._handle_answer(transcript)
            
            # Add to conversation history
            self.conversation_state.add_exchange(transcript, response['text'], intent)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing user speech: {e}")
            return {
                'type': 'error',
                'text': "I apologize, I had trouble processing your response. Could you please repeat that?",
                'auto_play': True
            }
    
    def _update_state_from_session(self, session_context: Dict):
        """Update conversation state from session context"""
        if 'interview_duration' in session_context:
            self.conversation_state.duration_minutes = session_context['interview_duration']
        if 'topics' in session_context:
            for topic in session_context['topics']:
                if topic not in self.conversation_state.topics_covered:
                    self.conversation_state.topics_covered[topic] = 0
    
    def _analyze_intent(self, transcript: str) -> str:
        """Analyze user intent using AI"""
        prompt = f"""
        Analyze this user speech in a technical interview context:
        
        Current State:
        - Current Question: "{self.conversation_state.current_question or 'None'}"
        - Awaiting Answer: {self.conversation_state.awaiting_answer}
        - Follow-ups Asked: {self.conversation_state.follow_up_count}
        
        User Said: "{transcript}"
        
        Determine the user's intent. Choose ONE:
        - "answering_question": User is providing an answer to the current question
        - "asking_question": User is asking the interviewer a question
        - "seeking_clarification": User wants the current question clarified or repeated
        - "confused_or_stuck": User is confused, stuck, or needs help
        
        Consider:
        - Question words (what, how, why, can you) suggest "asking_question"
        - Statements about concepts suggest "answering_question"
        - "I don't understand" or "can you repeat" suggest "seeking_clarification"
        - "I'm not sure" or "I don't know" suggest "confused_or_stuck"
        
        Return ONLY the intent category.
        """
        
        try:
            intent = self.llm.generate_response_sync(prompt).strip().lower()
            # Clean up the response to match expected categories
            if "asking" in intent:
                return "asking_question"
            elif "clarification" in intent:
                return "seeking_clarification"
            elif "confused" in intent or "stuck" in intent:
                return "confused_or_stuck"
            else:
                return "answering_question"
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return "answering_question"  # Default fallback
    
    def _handle_answer(self, transcript: str) -> Dict[str, Any]:
        """Handle when user is answering a question"""
        if not self.conversation_state.current_question:
            # No current question, generate first question
            return self._generate_first_question()
        
        # Evaluate the answer
        evaluation = self._evaluate_answer(transcript)
        
        # Decide whether to follow up or ask new question
        decision = self._should_follow_up(evaluation)
        
        if decision == "follow_up" and self.conversation_state.follow_up_count < self.conversation_state.max_follow_ups:
            return self._generate_follow_up(transcript, evaluation)
        else:
            # Reset follow-up count and generate new question
            self.conversation_state.follow_up_count = 0
            return self._generate_next_question()
    
    def _handle_user_question(self, user_question: str) -> Dict[str, Any]:
        """Handle when candidate asks interviewer a question"""
        prompt = f"""
        You are an experienced technical interviewer. The candidate asked:
        "{user_question}"
        
        Interview Context:
        - Current Question: {self.conversation_state.current_question or 'Starting interview'}
        - Topics: {list(self.conversation_state.topics_covered.keys())}
        - Time Remaining: {self.conversation_state.get_remaining_time():.1f} minutes
        
        Provide a helpful, professional response that:
        - Answers their question appropriately without giving away answers
        - Maintains professional interview tone
        - Encourages them to continue
        - Smoothly transitions back to the interview
        
        Keep response concise (2-3 sentences) and end with continuing the interview.
        """
        
        try:
            response_text = self.llm.generate_response_sync(prompt)
            return {
                'type': 'guidance',
                'text': response_text,
                'auto_play': True
            }
        except Exception as e:
            logger.error(f"Error handling user question: {e}")
            return {
                'type': 'guidance',
                'text': "That's a good question. Let me continue with the interview and we can discuss that further at the end. Let's proceed with the next question.",
                'auto_play': True
            }
    
    def _handle_clarification_request(self, transcript: str) -> Dict[str, Any]:
        """Handle when user wants clarification"""
        if not self.conversation_state.current_question:
            return self._generate_first_question()
        
        prompt = f"""
        The candidate asked for clarification about this question:
        "{self.conversation_state.current_question}"
        
        They said: "{transcript}"
        
        Provide a clear, helpful clarification that:
        - Rephrases or explains the question differently
        - Gives helpful context without revealing the answer
        - Encourages them to attempt an answer
        - Maintains interview flow
        
        Keep it concise and supportive.
        """
        
        try:
            response_text = self.llm.generate_response_sync(prompt)
            return {
                'type': 'clarification',
                'text': response_text,
                'auto_play': True
            }
        except Exception as e:
            logger.error(f"Error handling clarification: {e}")
            return {
                'type': 'clarification',
                'text': f"Let me rephrase that question: {self.conversation_state.current_question}. Take your time to think about it.",
                'auto_play': True
            }
    
    def _handle_confusion(self, transcript: str) -> Dict[str, Any]:
        """Handle when user is confused or stuck"""
        prompt = f"""
        The candidate seems confused or stuck. They said:
        "{transcript}"
        
        Current question: "{self.conversation_state.current_question or 'None'}"
        
        Provide supportive guidance that:
        - Acknowledges their difficulty
        - Offers a helpful hint or different approach
        - Encourages them without giving away the answer
        - Maintains positive interview atmosphere
        
        Be empathetic and constructive.
        """
        
        try:
            response_text = self.llm.generate_response_sync(prompt)
            return {
                'type': 'guidance',
                'text': response_text,
                'auto_play': True
            }
        except Exception as e:
            logger.error(f"Error handling confusion: {e}")
            return {
                'type': 'guidance',
                'text': "That's okay, take your time. Try to think about it step by step. What's the first thing that comes to mind?",
                'auto_play': True
            }
    
    def _evaluate_answer(self, answer: str) -> Dict[str, Any]:
        """Evaluate user's answer"""
        if not self.conversation_state.current_question:
            return {'score': 5, 'feedback': 'No question to evaluate against'}
        
        # Use existing LLM evaluator
        try:
            evaluation = self.llm.evaluate_answer_sync(
                question=self.conversation_state.current_question,
                expected_answer="",  # We'll let AI determine quality
                user_answer=answer,
                topic="general",
                difficulty=3
            )
            return {
                'score': evaluation.score if evaluation else 5,
                'feedback': evaluation.feedback if evaluation else 'Answer received',
                'strengths': evaluation.strengths if evaluation else [],
                'weaknesses': evaluation.weaknesses if evaluation else []
            }
        except Exception as e:
            logger.error(f"Error evaluating answer: {e}")
            return {'score': 5, 'feedback': 'Answer received'}
    
    def _should_follow_up(self, evaluation: Dict[str, Any]) -> str:
        """Decide whether to follow up or move to next question"""
        prompt = f"""
        Decide whether to ask a follow-up question or move to a new question.
        
        Answer Evaluation:
        - Score: {evaluation.get('score', 5)}/10
        - Feedback: {evaluation.get('feedback', 'No feedback')}
        
        Context:
        - Follow-ups asked so far: {self.conversation_state.follow_up_count}
        - Time remaining: {self.conversation_state.get_remaining_time():.1f} minutes
        - Questions asked: {self.conversation_state.questions_asked}
        
        Guidelines:
        - Follow up if answer shows understanding but could go deeper
        - Follow up if answer is incomplete but promising
        - Move on if answer is complete or user seems stuck
        - Move on if already asked 2+ follow-ups
        - Consider time remaining
        
        Return ONLY: "follow_up" or "new_question"
        """
        
        try:
            decision = self.llm.generate_response_sync(prompt).strip().lower()
            return "follow_up" if "follow" in decision else "new_question"
        except Exception as e:
            logger.error(f"Error deciding follow-up: {e}")
            return "new_question"  # Default to moving on
    
    def _generate_follow_up(self, original_answer: str, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a follow-up question based on user's answer"""
        self.conversation_state.follow_up_count += 1
        
        prompt = f"""
        Generate a natural follow-up question based on the candidate's answer.
        
        Original Question: "{self.conversation_state.current_question}"
        Candidate's Answer: "{original_answer}"
        Evaluation: {evaluation.get('feedback', 'No feedback')}
        
        Create a follow-up that:
        - Explores deeper into their answer
        - Tests practical application or understanding
        - Feels natural and conversational
        - Can be answered in 2-3 minutes
        - Builds on what they said
        
        Return just the follow-up question text.
        """
        
        try:
            follow_up_text = self.llm.generate_response_sync(prompt)
            return {
                'type': 'follow_up',
                'text': follow_up_text,
                'auto_play': True
            }
        except Exception as e:
            logger.error(f"Error generating follow-up: {e}")
            return {
                'type': 'follow_up',
                'text': "Can you elaborate on that a bit more?",
                'auto_play': True
            }
    
    def _generate_first_question(self) -> Dict[str, Any]:
        """Generate the first question of the interview"""
        topics = list(self.conversation_state.topics_covered.keys())
        
        prompt = f"""
        Generate the opening question for a technical interview.
        
        Context:
        - Topics: {topics}
        - Interview Duration: {self.conversation_state.duration_minutes} minutes
        - This is the first question
        
        Question Bank Examples (for style reference):
        {json.dumps(self.question_bank[:3], indent=2)}
        
        Create a question that:
        - Is appropriate for opening an interview
        - Covers one of the selected topics
        - Is medium difficulty (3/5)
        - Can be answered in 3-5 minutes
        - Sets a welcoming tone
        
        Return just the question text.
        """
        
        try:
            question_text = self.llm.generate_response_sync(prompt)
            self.conversation_state.current_question = question_text
            self.conversation_state.questions_asked += 1
            self.conversation_state.awaiting_answer = True
            
            return {
                'type': 'question',
                'text': question_text,
                'auto_play': True
            }
        except Exception as e:
            logger.error(f"Error generating first question: {e}")
            return {
                'type': 'question',
                'text': "Let's start with a fundamental question: Can you tell me about your experience with programming and what languages you're most comfortable with?",
                'auto_play': True
            }
    
    def _generate_next_question(self) -> Dict[str, Any]:
        """Generate the next question in the interview"""
        topics = list(self.conversation_state.topics_covered.keys())
        context_summary = self.conversation_state.get_context_summary()
        
        prompt = f"""
        Generate the next question for this technical interview.
        
        Interview Context:
        {context_summary}
        
        Topics to Cover: {topics}
        
        Question Bank Examples (for style reference):
        {json.dumps(self.question_bank[:5], indent=2)}
        
        Create a question that:
        - Covers new ground not yet explored
        - Is appropriate for the remaining time
        - Builds naturally on the conversation
        - Tests different aspects of their knowledge
        - Maintains good interview flow
        
        Return just the question text.
        """
        
        try:
            question_text = self.llm.generate_response_sync(prompt)
            self.conversation_state.current_question = question_text
            self.conversation_state.questions_asked += 1
            self.conversation_state.awaiting_answer = True
            
            return {
                'type': 'question',
                'text': question_text,
                'auto_play': True
            }
        except Exception as e:
            logger.error(f"Error generating next question: {e}")
            return {
                'type': 'question',
                'text': "Let's move on to another topic. Can you explain a challenging problem you've solved recently?",
                'auto_play': True
            }
    
    def get_conversation_state(self) -> ConversationState:
        """Get current conversation state"""
        return self.conversation_state
    
    def should_end_interview(self) -> bool:
        """Check if interview should end based on time"""
        return self.conversation_state.get_remaining_time() <= 1  # End with 1 minute buffer