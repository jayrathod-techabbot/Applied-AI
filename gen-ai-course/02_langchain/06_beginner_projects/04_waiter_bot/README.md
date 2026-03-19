# Waiter Bot - Setup Instructions

A restaurant waiter bot using LangChain and Ollama that can take food orders.

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
2. Run the bot: `python app.py`

## Usage

The waiter bot will greet you and help with:
- Taking your order
- Answering menu questions
- Providing recommendations
- Processing the bill

Example interactions:
- "I'd like to order a burger"
- "What do you recommend?"
- "What's on the menu?"
- "Can I see the bill?"
