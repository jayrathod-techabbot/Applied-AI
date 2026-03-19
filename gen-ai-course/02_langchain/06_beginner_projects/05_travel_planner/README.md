# Travel Planning App - Setup Instructions

A travel planning assistant using LangChain and Ollama.

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

The travel assistant can help you with:
- Planning itineraries
- Suggesting destinations
- Recommending activities
- Budget planning
- Packing tips

Example questions:
- "Plan a 3-day trip to Paris"
- "What should I pack for Japan?"
- "Suggest a beach vacation"
- "What's a good budget for Europe?"
