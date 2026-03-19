# Q&A System - Setup Instructions

A Question-Answering system using LangChain and Ollama that answers questions based on provided context.

## Prerequisites

1. **Install Ollama**
   - Download from: https://ollama.ai
   - Run: `ollama pull llama2`

2. **Install Dependencies**

```bash
pip install langchain langchain-community
```

Or:
```bash
pip install -r requirements.txt
```

## Setup

1. Start Ollama: `ollama serve`
2. Run the app: `python app.py`

## Usage

1. The system loads a sample context document automatically
2. Ask questions about the context
3. The system will answer based on the provided information

## Example Context

The system includes a sample article about Artificial Intelligence. You can ask questions like:
- "What is AI?"
- "What are the main types of AI?"
- "What are the benefits of AI?"

## Custom Context

To use your own context, edit the `context` variable in `app.py` with your own text.
