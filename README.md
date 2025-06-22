# AI Voice Interviewer System

A modular Python application that conducts voice-based technical interviews using AI-powered speech processing and evaluation.

## Features

- 🎤 **Voice-Based Interviews**: Converts questions to speech and records spoken answers
- 🤖 **AI-Powered Evaluation**: Uses LangChain + GPT for intelligent answer assessment
- 📊 **Detailed Feedback**: Provides scores (1-10), strengths, weaknesses, and improvement suggestions
- 🔄 **Follow-up Questions**: Generates contextual follow-up questions based on responses
- 📝 **Comprehensive Logging**: Tracks all interactions and generates session summaries
- 🎯 **Customizable**: Filter questions by topic and difficulty level
- 🔧 **Modular Design**: Easy to extend and integrate with other systems

## System Architecture

The system consists of six main components:

1. **Main Controller** (`main.py`) - Orchestrates the interview flow
2. **Question Manager** (`src/question_manager.py`) - Manages question bank and selection
3. **Audio Manager** (`src/audio_manager.py`) - Handles TTS, STT, and audio processing
4. **LLM Evaluator** (`src/llm_evaluator.py`) - Evaluates answers using AI
5. **Session Logger** (`src/session_logger.py`) - Logs interactions and generates reports
6. **Configuration** (`config.py`) - Manages settings and API keys

## Prerequisites

- Python 3.8 or higher
- Deepgram API key (for TTS/STT)
- OpenAI API key (for answer evaluation)
- Microphone and speakers/headphones
- Internet connection

## Installation

1. **Clone or download the project files**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys:**
   - Edit the `.env` file and add your API keys:
   ```
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Test your setup:**
   ```bash
   python main.py --test
   ```

## Getting API Keys

### Deepgram API Key
1. Sign up at [Deepgram](https://deepgram.com/)
2. Create a new project
3. Generate an API key
4. Add it to your `.env` file

### OpenAI API Key
1. Sign up at [OpenAI](https://platform.openai.com/)
2. Go to API Keys section
3. Create a new API key
4. Add it to your `.env` file

## Usage

### Interactive Mode (Recommended)
```bash
python main.py
```

This will start the interactive interface where you can:
- Configure interview preferences (topics, difficulty, number of questions)
- Start voice-based interviews
- View system information
- Test audio functionality

### Command Line Options
```bash
# Test audio system
python main.py --test

# Show system information
python main.py --info
```

### Interview Flow

1. **Setup**: Select topics, difficulty level, and number of questions
2. **Question Delivery**: System converts questions to speech and plays them
3. **Answer Recording**: Record your spoken response (auto-stops after silence)
4. **Transcription**: Speech is converted to text using Deepgram
5. **Evaluation**: AI evaluates your answer and provides detailed feedback
6. **Follow-up**: System may ask follow-up questions for clarification
7. **Summary**: Complete session summary with scores and recommendations

## Configuration

### Audio Settings
- **Sample Rate**: 16kHz (optimal for Deepgram)
- **Silence Threshold**: 2 seconds (auto-stop recording)
- **Max Recording Duration**: 60 seconds

### LLM Settings
- **Model**: GPT-3.5-turbo (configurable)
- **Temperature**: 0.7 (balanced creativity/consistency)
- **Max Tokens**: 500 (response length limit)

### Question Bank
Questions are stored in `data/question_bank.json` with the following structure:
```json
{
  "questions": [
    {
      "id": "q001",
      "text": "Question text here",
      "topic": "programming",
      "difficulty": 3,
      "expected_answer": "Expected answer description",
      "follow_up_questions": ["Optional follow-up questions"]
    }
  ]
}
```

## Available Topics

- Programming (OOP, algorithms, data structures)
- Web Development (HTTP/HTTPS, APIs)
- Software Engineering (version control, best practices)
- Databases (indexing, optimization)
- Machine Learning (concepts, applications)
- Cloud Computing (service models, deployment)

## Scoring System

Answers are evaluated on a 1-10 scale based on:
- **Accuracy**: Technical correctness
- **Completeness**: Coverage of key concepts
- **Clarity**: Clear explanation and structure
- **Depth**: Understanding of underlying principles
- **Examples**: Relevant examples when appropriate

### Score Ranges
- **9-10**: Excellent - Comprehensive and accurate
- **7-8**: Good - Mostly complete with minor gaps
- **5-6**: Average - Basic understanding, missing details
- **3-4**: Below Average - Significant gaps
- **1-2**: Poor - Major inaccuracies or very incomplete

## Session Logging

All interviews are automatically logged with:
- Complete transcripts of questions and answers
- Evaluation scores and feedback
- Session duration and timestamps
- Performance analytics and recommendations

Logs are saved in:
- `logs/sessions/session_[ID].log` - Detailed session log
- `logs/sessions/session_[ID].json` - Structured session data

## Troubleshooting

### Audio Issues
- **No audio playback**: Check speakers/headphones and system volume
- **Recording not working**: Verify microphone permissions and hardware
- **Poor transcription**: Speak clearly, reduce background noise

### API Issues
- **Deepgram errors**: Verify API key and internet connection
- **OpenAI errors**: Check API key and usage limits
- **Rate limiting**: Wait a moment and try again

### Common Problems
- **Import errors**: Ensure all dependencies are installed (`pip install -r requirements.txt`)
- **Permission errors**: Check file permissions for logs directory
- **Configuration errors**: Verify `.env` file format and API keys

## Extending the System

### Adding New Questions
Edit `data/question_bank.json` to add new questions with appropriate metadata.

### Custom Topics
Add new topics by including them in question definitions and updating topic filters.

### Different LLM Models
Modify `config.py` to use different OpenAI models or add support for other providers.

### UI Integration
The modular design makes it easy to integrate with web or desktop UIs by importing and using the core components.

## File Structure

```
ai_voice_interviewer/
├── main.py                     # Main application entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (API keys)
├── README.md                   # This file
├── AI_Voice_Interviewer_Architecture.md  # Detailed architecture
├── 
├── src/                        # Core modules
│   ├── __init__.py
│   ├── question_manager.py     # Question bank management
│   ├── audio_manager.py        # Audio processing (TTS/STT)
│   ├── llm_evaluator.py        # AI answer evaluation
│   └── session_logger.py       # Logging and session tracking
├── 
├── data/
│   └── question_bank.json      # Question database
├── 
└── logs/                       # Generated during runtime
    └── sessions/               # Session logs and data
```

## Performance Tips

- Use a quiet environment for better speech recognition
- Speak clearly and at a moderate pace
- Ensure stable internet connection for API calls
- Close unnecessary applications to reduce system load

## Contributing

To contribute to this project:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check the license file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the architecture documentation
3. Check API provider documentation
4. Create an issue with detailed error information

---

**Note**: This system requires active internet connection for AI processing and speech services. Ensure you have sufficient API credits for your intended usage.