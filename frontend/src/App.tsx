import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Types
interface Question {
  question_id: string;
  question_text: string;
  question_topic: string;
  question_difficulty: number;
  question_number: number;
  remaining_time_minutes: number;
  remaining_time_seconds: number;
  interview_duration: number;
}

interface EvaluationResult {
  transcript: string;
  score: number;
  feedback: string;
  suggestions: string;
  strengths: string[];
  weaknesses: string[];
  follow_up?: string;
}

interface SessionSummary {
  session_duration_minutes: number;
  questions_asked: number;
  score_statistics: {
    average: number;
    highest: number;
    lowest: number;
  };
  performance_level: string;
  topics_covered: Record<string, any>;
}

// Connection status enum
enum ConnectionStatus {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error'
}

// App sections enum
enum AppSection {
  SETUP = 'setup',
  INTERVIEW = 'interview',
  RESULTS = 'results'
}

function App() {
  // WebSocket and connection state
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(ConnectionStatus.CONNECTING);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // UI state
  const [currentSection, setCurrentSection] = useState<AppSection>(AppSection.SETUP);
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState('Processing...');
  const [error, setError] = useState<string | null>(null);

  // Setup state
  const [availableTopics, setAvailableTopics] = useState<string[]>([]);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [difficulty, setDifficulty] = useState(3);
  const [interviewDuration, setInterviewDuration] = useState(30);

  // Interview state
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState<string>('');

  // Results state
  const [sessionSummary, setSessionSummary] = useState<SessionSummary | null>(null);
  const [allEvaluations, setAllEvaluations] = useState<EvaluationResult[]>([]);

  // Audio recording
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // WebSocket connection
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      const websocket = new WebSocket('ws://localhost:8765');
      
      websocket.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus(ConnectionStatus.CONNECTED);
        setWs(websocket);
        loadTopics(websocket);
      };

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data, websocket);
      };

      websocket.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus(ConnectionStatus.DISCONNECTED);
        setWs(null);
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus(ConnectionStatus.ERROR);
        setError('Connection error. Please check if the server is running.');
      };

    } catch (error) {
      console.error('Failed to connect:', error);
      setConnectionStatus(ConnectionStatus.ERROR);
      setError('Failed to connect to server');
    }
  };

  const handleWebSocketMessage = (data: any, websocket?: WebSocket) => {
    console.log('Received message:', data);

    switch (data.type) {
      case 'topics':
        setAvailableTopics(data.topics);
        break;

      case 'session_started':
        console.log('Session started with ID:', data.session_id);
        setSessionId(data.session_id);
        setCurrentSection(AppSection.INTERVIEW);
        setLoading(false);
        // Get the first question after session starts
        setTimeout(() => {
          console.log('About to get next question, ws=', !!ws, 'sessionId=', data.session_id);
          getNextQuestionWithId(data.session_id, websocket);
        }, 100);
        break;

      case 'question':
        console.log('Received question:', data);
        setCurrentQuestion(data);
        setTranscript('');
        setLoading(false);
        break;

      case 'answer_recorded':
        setTranscript(data.transcript);
        setLoading(false);
        // Don't show evaluation during interview
        break;

      case 'interview_complete':
        finishInterview();
        break;

      case 'session_ended':
        setSessionSummary(data.summary);
        setAllEvaluations(data.evaluations || []);
        setCurrentSection(AppSection.RESULTS);
        setLoading(false);
        break;

      case 'audio':
        playAudioFromBase64(data.audio_data);
        break;

      case 'error':
        setError(data.message);
        setLoading(false);
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const loadTopics = (websocket: WebSocket) => {
    websocket.send(JSON.stringify({
      type: 'get_topics'
    }));
  };

  const startInterview = () => {
    if (!ws || selectedTopics.length === 0) {
      setError('Please select at least one topic');
      return;
    }

    console.log('Starting interview with:', { topics: selectedTopics, difficulty, interviewDuration });
    setLoading(true);
    setLoadingText('Starting interview...');

    const message = {
      type: 'start_session',
      topics: selectedTopics,
      difficulty: difficulty,
      interview_duration: interviewDuration
    };
    
    console.log('Sending message:', message);
    ws.send(JSON.stringify(message));
  };

  const getNextQuestion = () => {
    if (!ws || !sessionId) {
      console.log('Cannot get question: ws=', !!ws, 'sessionId=', sessionId);
      return;
    }

    console.log('Getting next question for session:', sessionId);
    setLoading(true);
    setLoadingText('Loading next question...');

    ws.send(JSON.stringify({
      type: 'get_question',
      session_id: sessionId
    }));

    // Don't set loading to false here - wait for response
  };

  const getNextQuestionWithId = (sessionIdParam: string, websocket?: WebSocket) => {
    const wsToUse = websocket || ws;
    if (!wsToUse || !sessionIdParam) {
      console.log('Cannot get question: ws=', !!wsToUse, 'sessionIdParam=', sessionIdParam);
      return;
    }

    console.log('Getting next question for session:', sessionIdParam);
    setLoading(true);
    setLoadingText('Loading next question...');

    wsToUse.send(JSON.stringify({
      type: 'get_question',
      session_id: sessionIdParam
    }));

    // Don't set loading to false here - wait for response
  };

  const playQuestion = async () => {
    if (!ws || !currentQuestion) return;

    setLoading(true);
    setLoadingText('Generating speech...');

    ws.send(JSON.stringify({
      type: 'text_to_speech',
      text: currentQuestion.question_text
    }));
  };

  const playAudioFromBase64 = (audioBase64: string) => {
    try {
      const audioData = atob(audioBase64);
      const arrayBuffer = new ArrayBuffer(audioData.length);
      const view = new Uint8Array(arrayBuffer);
      
      for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i);
      }

      const audioBlob = new Blob([arrayBuffer], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      audio.play().then(() => {
        setLoading(false);
      }).catch((error) => {
        console.error('Error playing audio:', error);
        setLoading(false);
      });

    } catch (error) {
      console.error('Error processing audio:', error);
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        processAudioRecording(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);

      // Auto-stop after 60 seconds
      setTimeout(() => {
        if (mediaRecorderRef.current && isRecording) {
          stopRecording();
        }
      }, 60000);

    } catch (error) {
      console.error('Error starting recording:', error);
      setError('Failed to access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudioRecording = async (audioBlob: Blob) => {
    if (!ws || !sessionId || !currentQuestion) return;

    setLoading(true);
    setLoadingText('Processing your answer...');

    try {
      const arrayBuffer = await audioBlob.arrayBuffer();
      const uint8Array = new Uint8Array(arrayBuffer);
      
      // Convert to base64 more efficiently to avoid stack overflow
      let binaryString = '';
      const chunkSize = 8192; // Process in chunks to avoid stack overflow
      
      for (let i = 0; i < uint8Array.length; i += chunkSize) {
        const chunk = uint8Array.slice(i, i + chunkSize);
        binaryString += String.fromCharCode.apply(null, Array.from(chunk));
      }
      
      const audioBase64 = btoa(binaryString);

      ws.send(JSON.stringify({
        type: 'submit_audio',
        session_id: sessionId,
        question_id: currentQuestion.question_id,
        audio_data: audioBase64
      }));

    } catch (error) {
      console.error('Error processing audio:', error);
      setError('Failed to process audio recording');
      setLoading(false);
    }
  };

  const nextQuestion = () => {
    // Check if time is up or if we should continue
    if (currentQuestion && (currentQuestion.remaining_time_minutes <= 0 && currentQuestion.remaining_time_seconds <= 0)) {
      finishInterview();
    } else {
      getNextQuestion();
    }
  };

  const finishInterview = () => {
    if (!ws || !sessionId) return;

    setLoading(true);
    setLoadingText('Generating final report...');

    ws.send(JSON.stringify({
      type: 'end_session',
      session_id: sessionId
    }));
  };

  const resetToSetup = () => {
    setCurrentSection(AppSection.SETUP);
    setSessionId(null);
    setCurrentQuestion(null);
    setTranscript('');
    setSessionSummary(null);
    setAllEvaluations([]);
    setSelectedTopics([]);
  };

  const toggleTopic = (topic: string) => {
    setSelectedTopics(prev => 
      prev.includes(topic) 
        ? prev.filter(t => t !== topic)
        : [...prev, topic]
    );
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case ConnectionStatus.CONNECTED: return 'text-green-500';
      case ConnectionStatus.CONNECTING: return 'text-yellow-500';
      case ConnectionStatus.DISCONNECTED: return 'text-red-500';
      case ConnectionStatus.ERROR: return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case ConnectionStatus.CONNECTED: return 'Connected';
      case ConnectionStatus.CONNECTING: return 'Connecting...';
      case ConnectionStatus.DISCONNECTED: return 'Disconnected';
      case ConnectionStatus.ERROR: return 'Connection Error';
      default: return 'Unknown';
    }
  };

  const formatTopicName = (topic: string) => {
    return topic.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary to-secondary">
      {/* Loading Overlay */}
      {loading && (
        <div className="loading-overlay">
          <div className="loading-content">
            <div className="spinner mb-4"></div>
            <p className="text-lg font-semibold text-gray-800">{loadingText}</p>
          </div>
        </div>
      )}

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <header className="text-center text-white mb-8">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 drop-shadow-lg">
            🎤 AI Voice Interviewer
          </h1>
          <p className="text-lg md:text-xl opacity-90">
            Intelligent voice-based technical interviews with real-time AI evaluation
          </p>
        </header>

        {/* Connection Status */}
        <div className="bg-white/10 backdrop-blur-md rounded-full px-6 py-3 mb-8 flex items-center justify-center gap-3 text-white">
          <div className={`w-3 h-3 rounded-full ${getConnectionStatusColor()}`}></div>
          <span>{getConnectionStatusText()}</span>
        </div>

        {/* Setup Section */}
        {currentSection === AppSection.SETUP && (
          <div className="bg-white rounded-2xl shadow-2xl p-8 mb-8 transform hover:scale-[1.02] transition-transform duration-300">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
              ⚙️ Interview Setup
            </h2>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Select Topics:
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {availableTopics.map((topic) => (
                    <button
                      key={topic}
                      onClick={() => toggleTopic(topic)}
                      className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                        selectedTopics.includes(topic)
                          ? 'bg-primary text-white border-primary'
                          : 'bg-gray-50 text-gray-700 border-gray-200 hover:border-primary hover:bg-blue-50'
                      }`}
                    >
                      {formatTopicName(topic)}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Difficulty Level: <span className="text-primary font-bold">{difficulty}</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={difficulty}
                  onChange={(e) => setDifficulty(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Interview Duration:
                </label>
                <select
                  value={interviewDuration}
                  onChange={(e) => setInterviewDuration(parseInt(e.target.value))}
                  className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-primary focus:outline-none"
                >
                  <option value={15}>15 Minutes</option>
                  <option value={30}>30 Minutes</option>
                  <option value={45}>45 Minutes</option>
                  <option value={60}>60 Minutes</option>
                </select>
              </div>

              <button
                onClick={startInterview}
                disabled={selectedTopics.length === 0 || connectionStatus !== ConnectionStatus.CONNECTED}
                className="w-full bg-primary hover:bg-primary/90 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-bold py-4 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 flex items-center justify-center gap-3"
              >
                ▶️ Start Interview
              </button>
            </div>
          </div>
        )}

        {/* Interview Section */}
        {currentSection === AppSection.INTERVIEW && currentQuestion && (
          <div className="bg-white rounded-2xl shadow-2xl p-8 mb-8">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                Question {currentQuestion.question_number} | Time Remaining: {currentQuestion.remaining_time_minutes}:{currentQuestion.remaining_time_seconds.toString().padStart(2, '0')}
              </h2>
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary to-secondary transition-all duration-500 ease-out"
                  style={{ width: `${((currentQuestion.interview_duration * 60 - (currentQuestion.remaining_time_minutes * 60 + currentQuestion.remaining_time_seconds)) / (currentQuestion.interview_duration * 60)) * 100}%` }}
                ></div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-xl p-6 mb-6 border-l-4 border-primary">
              <div className="text-lg leading-relaxed text-gray-800 mb-4">
                {currentQuestion.question_text}
              </div>
              
              <div className="flex flex-wrap gap-3">
                <span className="bg-primary text-white px-3 py-1 rounded-full text-sm font-semibold">
                  {formatTopicName(currentQuestion.question_topic)}
                </span>
                <span className="bg-yellow-400 text-gray-800 px-3 py-1 rounded-full text-sm font-semibold">
                  Difficulty: {currentQuestion.question_difficulty}/5
                </span>
              </div>
            </div>

            {/* Audio Controls */}
            <div className="flex flex-wrap justify-center gap-4 mb-6">
              <button
                onClick={playQuestion}
                disabled={loading}
                className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 flex items-center gap-2"
              >
                🔊 Play Question
              </button>
              
              {!isRecording ? (
                <button
                  onClick={startRecording}
                  disabled={loading}
                  className="bg-red-500 hover:bg-red-600 disabled:bg-gray-400 text-white font-bold py-4 px-8 rounded-lg transition-all duration-300 transform hover:scale-105 flex items-center gap-2"
                >
                  🎤 Record Answer
                </button>
              ) : (
                <button
                  onClick={stopRecording}
                  className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 flex items-center gap-2"
                >
                  ⏹️ Stop Recording
                </button>
              )}
              
              <button
                onClick={finishInterview}
                disabled={loading}
                className="bg-orange-500 hover:bg-orange-600 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 flex items-center gap-2"
              >
                🏁 Finish Interview
              </button>
            </div>

            {/* Recording Status */}
            {isRecording && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
                <div className="flex items-center justify-center gap-3 mb-4">
                  <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse"></div>
                  <span className="font-semibold text-yellow-800">Recording... Speak clearly</span>
                </div>
                <div className="flex justify-center items-end gap-1 h-8">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className="w-1 bg-red-500 rounded audio-bar"
                      style={{ height: '10px' }}
                    ></div>
                  ))}
                </div>
              </div>
            )}

            {/* Transcription */}
            {transcript && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
                <h3 className="text-lg font-semibold text-blue-800 mb-3 flex items-center gap-2">
                  📝 Your Answer:
                </h3>
                <div className="text-blue-700 italic text-lg leading-relaxed">
                  {transcript}
                </div>
              </div>
            )}

            {/* Simple confirmation message after answer */}
            {transcript && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                <p className="text-green-800 font-semibold text-center">
                  ✅ Answer recorded successfully!
                </p>
              </div>
            )}

            {/* Navigation */}
            {transcript && (
              <div className="flex flex-wrap justify-center gap-4">
                {currentQuestion.remaining_time_minutes > 0 || currentQuestion.remaining_time_seconds > 0 ? (
                  <>
                    <button
                      onClick={nextQuestion}
                      className="bg-primary hover:bg-primary/90 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 flex items-center gap-2"
                    >
                      ➡️ Next Question
                    </button>
                    <button
                      onClick={finishInterview}
                      className="bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 flex items-center gap-2"
                    >
                      🏁 Finish Early
                    </button>
                  </>
                ) : (
                  <button
                    onClick={finishInterview}
                    className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 flex items-center gap-2"
                  >
                    🏁 Finish Interview
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Results Section */}
        {currentSection === AppSection.RESULTS && sessionSummary && (
          <div className="bg-white rounded-2xl shadow-2xl p-8">
            <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center flex items-center justify-center gap-3">
              🏆 Interview Complete!
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              <div className="bg-gradient-to-br from-primary to-secondary text-white rounded-xl p-6 text-center">
                <h3 className="text-xl font-semibold mb-4">Overall Performance</h3>
                <div className="text-5xl font-bold mb-2">
                  <span>{sessionSummary.score_statistics.average}</span>
                  <span className="text-2xl opacity-80">/10</span>
                </div>
                <p className="text-lg opacity-90">{sessionSummary.performance_level}</p>
              </div>

              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Session Statistics</h3>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-primary">{sessionSummary.questions_asked}</div>
                    <div className="text-sm text-gray-600">Questions Asked</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-primary">{sessionSummary.session_duration_minutes}</div>
                    <div className="text-sm text-gray-600">Duration (mins)</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-primary">{sessionSummary.score_statistics.highest}</div>
                    <div className="text-sm text-gray-600">Highest Score</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-primary">{sessionSummary.score_statistics.lowest}</div>
                    <div className="text-sm text-gray-600">Lowest Score</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-primary">{sessionSummary.score_statistics.average.toFixed(2)}</div>
                    <div className="text-sm text-gray-600">Average Score</div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Topics Covered</h3>
                <ul className="list-disc list-inside space-y-2">
                  {Object.entries(sessionSummary.topics_covered).map(([topic, details]) => (
                    <li key={topic} className="text-gray-700">
                      {formatTopicName(topic)}: {details.questions_asked} questions
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Detailed Evaluations Section */}
            {allEvaluations.length > 0 && (
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-6 text-center">
                  📊 Detailed Question Analysis
                </h3>
                <div className="space-y-6">
                  {allEvaluations.map((evaluation, index) => (
                    <div key={index} className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="text-lg font-semibold text-gray-800">
                          Question {index + 1}
                        </h4>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-bold text-primary">{evaluation.score}</span>
                          <span className="text-gray-600">/10</span>
                        </div>
                      </div>
                      
                      <div className="mb-4">
                        <h5 className="font-semibold text-gray-700 mb-2">Your Answer:</h5>
                        <p className="text-gray-600 italic bg-white p-3 rounded-lg border">
                          {evaluation.transcript}
                        </p>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h5 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
                            💬 Feedback
                          </h5>
                          <p className="text-gray-600 text-sm">{evaluation.feedback}</p>
                        </div>
                        
                        <div>
                          <h5 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
                            💡 Suggestions
                          </h5>
                          <p className="text-gray-600 text-sm">{evaluation.suggestions}</p>
                        </div>
                        
                        {evaluation.strengths.length > 0 && (
                          <div>
                            <h5 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
                              👍 Strengths
                            </h5>
                            <ul className="text-gray-600 text-sm space-y-1">
                              {evaluation.strengths.map((strength, idx) => (
                                <li key={idx} className="flex items-start gap-2">
                                  <span className="text-green-500">•</span>
                                  {strength}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {evaluation.weaknesses.length > 0 && (
                          <div>
                            <h5 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
                              ⚠️ Areas to Improve
                            </h5>
                            <ul className="text-gray-600 text-sm space-y-1">
                              {evaluation.weaknesses.map((weakness, idx) => (
                                <li key={idx} className="flex items-start gap-2">
                                  <span className="text-red-500">•</span>
                                  {weakness}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="text-center">
              <button
                onClick={resetToSetup}
                className="bg-primary hover:bg-primary/90 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105"
              >
                🔄 Start New Interview
              </button>
            </div>
          </div>
        )}
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 mt-8">
            <h3 className="font-semibold mb-2">Error</h3>
            <p>{error}</p>
            <button
              onClick={() => setError(null)}
              className="mt-2 text-red-600 hover:underline"
            >
              Dismiss
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
export default App;