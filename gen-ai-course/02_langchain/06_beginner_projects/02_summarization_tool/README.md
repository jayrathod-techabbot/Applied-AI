# Summarization Tool - Setup Instructions

A text summarization tool using LangChain and Ollama.

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
2. Run the tool: `python app.py`

## Usage

1. Enter or paste text to summarize
2. Press Enter to get the summary
3. Type `exit` to quit

## Example Input

```
The Industrial Revolution, which took place from the 18th to 19th centuries, was a period during which predominantly agrarian, rural societies in Europe and America became industrial and more urban. Prior to the Industrial Revolution, which began in Britain in the late 1700s, manufacturing was often done in people's homes, using hand tools or basic machines. Industrialization marked a shift to powered, special-purpose machinery, factories and mass production.
```

The tool will produce a concise summary of the input text.
