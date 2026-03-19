# Summarization Tool Project

## Problem Statement

Create a tool that can:
- Take any text input
- Generate a concise summary
- Preserve key information

## Solution

This tool uses:
- **LangChain** - For prompt templates and LLM chain
- **Ollama** - As the local LLM provider
- **Stuff Chain** - Passes all text to the LLM at once

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| LLM | Ollama (llama2) |
| Framework | LangChain |
| Chain Type | load_summarize_chain |

## How It Works

1. Initialize Ollama chat model
2. Create a prompt template for summarization
3. Use LangChain's `load_summarize_chain` 
4. Process user input through the chain
5. Return the generated summary

## Key Concepts Learned

- Prompt Templates
- LLMChain usage
- Stuff Chain (for short documents)
- Input/output processing

## File Structure

```
02_summarization_tool/
├── README.md
├── project.md
├── app.py
└── requirements.txt
```
