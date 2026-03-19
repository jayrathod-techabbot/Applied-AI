# ChatBot - Setup Instructions

A simple conversational chatbot using LangChain and Ollama with memory support.

## Prerequisites

1. **Install Ollama**
   - Download from: https://ollama.ai
   - Run: `ollama pull llama2` (or your preferred model)

2. **Install Python Dependencies**

```bash
pip install langchain langchain-community langchain-core
```

Or install from requirements:

```bash
pip install -r requirements.txt
```

## Setup

1. Make sure Ollama is running:
   ```bash
   ollama serve
   ```

2. In another terminal, run the chatbot:
   ```bash
   python app.py
   ```

## Usage

- Type your message and press Enter to chat
- Type `exit` or `quit` to end the conversation
- The bot remembers your conversation history

## Troubleshooting

- **Connection Error**: Make sure Ollama is running (`ollama serve`)
- **Model Not Found**: Pull the model first (`ollama pull llama2`)
- **Port Error**: Ollama default port is 11434
