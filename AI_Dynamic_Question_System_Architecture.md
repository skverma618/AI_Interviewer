# AI Dynamic Question System Architecture

## Overview
Enhanced AI Voice Interviewer system with hybrid question generation that uses the question bank as a foundation but can dynamically generate new questions using AI when needed.

## System Architecture

### Core Components

#### 1. AI Question Generator (`src/ai_question_generator.py`)
- **Purpose**: Generate contextual questions using LLM when question bank is exhausted
- **Features**:
  - Dynamic question generation based on topics and difficulty
  - Context-aware follow-up questions
  - Cross-topic question generation
  - Performance-adaptive questioning

#### 2. Enhanced Question Manager (`src/question_manager.py`)
- **Hybrid Selection Logic**:
  1. First priority: Select from question bank
  2. Fallback: Generate AI questions when bank is exhausted
  3. Context-aware: Generate follow-ups based on previous answers

#### 3. Interview Context Tracker (`src/interview_context.py`)
- **Track Interview State**:
  - Questions asked and answers given
  - Topics covered and depth of coverage
  - User performance patterns
  - Time remaining and pacing

#### 4. Enhanced Web Server (`web_server.py`)
- **Smart Question Flow**:
  - Integrate AI question generation
  - Handle follow-up question logic
  - Manage interview context state

## Implementation Plan

### Phase 1: AI Question Generator
```python
class AIQuestionGenerator:
    def generate_question(self, topics, difficulty, context)
    def generate_follow_up(self, original_question, user_answer, context)
    def generate_cross_topic_question(self, topics, difficulty, context)
```

### Phase 2: Enhanced Question Manager
```python
class QuestionManager:
    def select_question_hybrid(self, topics, difficulty, context)
    def should_generate_follow_up(self, evaluation_result, context)
    def get_next_question_strategy(self, context)
```

### Phase 3: Interview Context System
```python
class InterviewContext:
    def add_question_answer_pair(self, question, answer, evaluation)
    def get_coverage_analysis(self)
    def suggest_next_topic(self)
    def calculate_remaining_time_strategy(self)
```

## Key Features

### 1. Hybrid Question Selection
- **Question Bank First**: Use predefined questions when available
- **AI Generation**: Generate new questions when bank is exhausted
- **Context Awareness**: Consider previous Q&A for relevance

### 2. Dynamic Follow-up Generation
- **Based on User Answers**: Generate follow-ups from user responses
- **Depth Exploration**: Dive deeper into topics user shows strength/interest
- **Clarification Questions**: Ask for elaboration on unclear answers

### 3. Cross-Topic Questions
- **Integration Questions**: "How would you use X (from topic A) to solve Y (from topic B)?"
- **Real-world Scenarios**: Combine multiple topics in practical scenarios
- **System Design**: Ask about architecture spanning multiple domains

### 4. Adaptive Difficulty
- **Performance-based**: Adjust difficulty based on user performance
- **Time-based**: Increase complexity as interview progresses
- **Topic-based**: Different difficulty curves for different topics

### 5. Time Optimization
- **Full Utilization**: Ensure interview time is fully used
- **Pacing Control**: Adjust question complexity based on remaining time
- **Emergency Questions**: Quick questions for end-of-interview scenarios

## Technical Implementation

### AI Question Generation Prompts
```
System: You are an expert technical interviewer. Generate a {difficulty}/5 difficulty question about {topics} for a {duration}-minute interview.

Context: 
- Previous questions: {previous_questions}
- User's answers: {previous_answers}
- Topics covered: {topics_covered}
- Time remaining: {time_remaining}

Generate a question that:
1. Is appropriate for the difficulty level
2. Doesn't repeat previous questions
3. Explores new aspects of the topics
4. Can be answered in the remaining time
```

### Follow-up Generation Prompts
```
System: Generate a follow-up question based on the user's answer.

Original Question: {original_question}
User's Answer: {user_answer}
Evaluation: {evaluation_feedback}

Generate a follow-up that:
1. Explores deeper into their answer
2. Clarifies any unclear points
3. Tests practical application
4. Is appropriate for remaining time: {time_remaining}
```

## Benefits

### 1. Unlimited Question Pool
- Never run out of questions during interview time
- Fresh questions for repeat users
- Adaptive to user's specific knowledge areas

### 2. Intelligent Conversation Flow
- Natural follow-up questions
- Context-aware questioning
- Exploration of user's strengths and gaps

### 3. Full Time Utilization
- Always have questions for remaining time
- Adaptive pacing based on time constraints
- Emergency short questions for time pressure

### 4. Cross-Topic Integration
- Real-world scenario questions
- Test integration knowledge
- Holistic skill assessment

## Implementation Steps

1. **Create AI Question Generator**: Core LLM-powered question generation
2. **Enhance Question Manager**: Add hybrid selection logic
3. **Implement Interview Context**: Track conversation state
4. **Update Web Server**: Integrate new question flow
5. **Test and Refine**: Ensure smooth question transitions

## Success Metrics

- **Time Utilization**: 95%+ of interview time used effectively
- **Question Variety**: No repeated questions in same interview
- **Context Relevance**: Follow-up questions directly related to previous answers
- **Difficulty Adaptation**: Questions adjust based on user performance
- **Topic Coverage**: Balanced coverage across selected topics