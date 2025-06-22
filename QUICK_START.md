# Quick Start Guide - AI Voice Interviewer System

## 🚀 Get Started in 5 Minutes

### 1. Setup
```bash
# Run the automated setup
python setup.py
```

### 2. Get API Keys
- **Deepgram**: Sign up at [deepgram.com](https://deepgram.com/) and get your API key
- **OpenAI**: Sign up at [platform.openai.com](https://platform.openai.com/) and get your API key

### 3. Configure Environment
Edit the `.env` file with your actual API keys:
```
DEEPGRAM_API_KEY=your_actual_deepgram_key_here
OPENAI_API_KEY=your_actual_openai_key_here
```

### 4. Run the System
```bash
# Start the interactive interview system
python main.py

# Or test audio functionality
python main.py --test

# Or view system information
python main.py --info
```

## 🎯 Quick Demo Flow

1. **Launch**: `python main.py`
2. **Select**: Choose topics (e.g., "programming") and difficulty (1-5)
3. **Interview**: 
   - System asks questions via speech
   - You answer by speaking
   - Get instant AI feedback and scores
4. **Review**: See your complete session summary

## 🔧 Troubleshooting

### Common Issues
- **No audio**: Check microphone/speaker permissions
- **API errors**: Verify your API keys in `.env`
- **Import errors**: Run `pip install -r requirements.txt`

### Test Your Setup
```bash
# Run all tests
python run_tests.py

# Test specific component
python run_tests.py test_question_manager
```

## 📊 What You Get

- **Voice Questions**: AI converts questions to speech
- **Speech Recognition**: Your answers are transcribed automatically  
- **AI Evaluation**: Get detailed feedback with 1-10 scores
- **Follow-up Questions**: Dynamic follow-ups based on your answers
- **Session Reports**: Complete interview summaries and analytics

## 🎤 Tips for Best Results

- Use a quiet environment
- Speak clearly and at moderate pace
- Ensure stable internet connection
- Have microphone and speakers ready

---

**Ready to start your AI-powered interview? Run `python main.py` now!**