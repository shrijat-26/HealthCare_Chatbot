# Emotion-Aware Healthcare Chatbot

An intelligent healthcare chatbot that uses emotion detection and LangGraph orchestration to provide empathetic, personalized medical assistance. The system processes both text and voice inputs, maintains user profiles, and adapts responses based on detected emotional states.

## Video Demo 

Demo of the prototype starts from the timestamp : 06:38

- **Google Drive Link** : https://drive.google.com/file/d/1QKsat-9PvsgWAfMUUVBRrf_WneYtvLSI/view?usp=sharing
- **Youtube Link (Unlisted)** : https://youtu.be/wzWh5iaRUzs

## Features

- **Multi-modal Input Support**: Accept both text and voice inputs
- **Emotion Detection**: Real-time emotion analysis from text and audio
- **Voice Processing**: Speech-to-text conversion with silence removal
- **Persistent Memory**: Conversation history and user profile management
- **Health Condition Tracking**: Automatic extraction and logging of health symptoms
- **Empathetic Responses**: AI responses adapted to user's emotional state
- **Web and CLI Interfaces**: Both REST API and command-line interfaces available

## Architecture

The system uses LangGraph for orchestration with the following components:

### Core Components

1. **API Server** (`api_server.py`): FastAPI-based web server handling HTTP requests
2. **Orchestrator** (`orchestrator.py`): LangGraph workflow management
3. **Emotion Detector** (`emotion_detector.py`): Multi-modal emotion analysis
4. **Profile Manager** (`profile_manager.py`): User profile and health condition tracking
5. **Main Interface** (`main.py`): CLI-based interaction

### Workflow

```
User Input (Text/Audio) → Emotion Detection → Profile Update → AI Response Generation → Response Delivery
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js and Bun (for frontend)
- Azure OpenAI API access
- Required Python packages (see installation)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/shrijat-26/HealthCare_Chatbot
   cd emotion-aware-healthcare-chatbot
   ```

2. **Install Python dependencies**
   ```bash
   pip install fastapi uvicorn numpy soundfile pydub langgraph langchain-openai langchain-community python-dotenv faster-whisper webrtcvad opensmile transformers torch torchaudio sounddevice
   ```

3. **Install Node.js dependencies**
   ```bash
   # Navigate to your frontend directory
   bun install
   ```

4. **Environment Setup**
   Create a `.env` file in the root directory:
   ```env
   AZURE_OPENAI_API_KEY=your_azure_openai_key
   AZURE_OPENAI_API_VERSION=2024-02-01
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_GPT_4o_mini=your_deployment_name
   ```

##  Running the Application

### Web Interface (Recommended)

1. **Start the API Server**
   ```bash
   uvicorn api_server:app --host 0.0.0.0 --port 8000
   ```

2. **Start the Frontend**
   ```bash
   bun dev
   ```

The API will be available at `http://localhost:8000` and the frontend at the port specified by your frontend configuration.

### CLI Interface

```bash
python main.py
```

## System Requirements

### For Different Operating Systems

#### Windows
- Install Python 3.8+ from python.org
- Install Visual Studio Build Tools for C++ compilation
- Install Node.js and Bun
- May require additional audio libraries

#### macOS
- Install Python via Homebrew: `brew install python`
- Install Node.js and Bun: `brew install node && npm install -g bun`
- Install audio dependencies: `brew install portaudio`

#### Linux (Ubuntu/Debian)
```bash
# Python and pip
sudo apt update
sudo apt install python3 python3-pip

# Audio dependencies
sudo apt install portaudio19-dev python3-pyaudio

# Node.js and Bun
curl -fsSL https://bun.sh/install | bash
```

## API Documentation

### Endpoints

#### POST `/text`
Process text input and return bot response.

**Request Body:**
```json
{
  "messages": [{"content": "Your message here"}],
  "user_id": "user_identifier"
}
```

**Response:**
```json
{
  "answer": "Bot response"
}
```

#### POST `/voice`
Process voice input and return bot response with transcript.

**Request:**
- Multipart form data with audio file
- Optional `user_id` parameter

**Response:**
```json
{
  "answer": "Bot response",
  "transcript": "Transcribed text"
}
```

## Core Functionality

### Emotion Detection

The system analyzes emotions using:
- **Text Analysis**: RoBERTa-based sentiment classification
- **Audio Analysis**: Voice activity detection + transcription + sentiment analysis
- **Emotion Labels**: Negative, Neutral, Positive with valence and arousal scores

### User Profile Management

- **Automatic Profile Creation**: New users get default profiles
- **Health Condition Extraction**: AI-powered symptom detection from conversations
- **Persistent Storage**: JSON-based profile and conversation history storage

### Memory System

- **Conversation History**: Maintains chat history per user thread
- **Profile Integration**: Incorporates user information into AI responses
- **Timestamped Logging**: All interactions and health conditions are logged

## 📁 File Structure

```
├── api_server.py          # FastAPI web server
├── orchestrator.py        # LangGraph workflow orchestration
├── emotion_detector.py    # Emotion detection logic
├── emotion_test.py        # Emotion detection utilities
├── profile_manager.py     # User profile management
├── main.py               # CLI interface
├── .env                  # Environment variables
├── user_profiles.json    # User profile storage
├── chat_memory/          # Conversation history storage
└── emotion_log.jsonl     # Emotion detection logs
```

## Security Considerations

- **CORS Configuration**: Currently set to allow all origins (`*`) - restrict in production
- **API Key Protection**: Store Azure OpenAI keys securely
- **User Data**: Consider encryption for sensitive health information
- **Rate Limiting**: Implement rate limiting for production use

## Configuration Options

### Audio Processing
- Sample rate: 16kHz (configurable in `emotion_test.py`)
- VAD aggressiveness: Level 3 (configurable in `emotion_test.py`)
- Recording duration: 5 seconds (configurable in `main.py`)

### Model Configuration
- Whisper model: "tiny" (can be upgraded to "base", "small", "medium", "large")
- Sentiment model: "cardiffnlp/twitter-roberta-base-sentiment"
- Azure OpenAI deployment: Configurable via environment variables

## Troubleshooting

### Common Issues

1. **Audio not working**: Ensure proper microphone permissions and audio drivers
2. **Azure OpenAI errors**: Verify API keys and deployment names
3. **Import errors**: Check all dependencies are installed
4. **Port conflicts**: Ensure ports 8000 and frontend port are available

### Debug Mode

Enable debug logging by adding to your `.env`:
```env
DEBUG=true
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

## Future Enhancements

- Multi-language support
- Advanced emotion recognition models
- Integration with medical databases
- Mobile app interface
- Real-time emotion monitoring dashboard
