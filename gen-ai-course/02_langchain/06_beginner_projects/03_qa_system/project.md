# Q&A System Project

## Problem Statement

Create a system that can:
- Accept a context/document
- Answer questions based on that context
- Provide accurate, relevant answers

## Solution

This system uses:
- **LangChain** - For prompt templates and LLM chain
- **Ollama** - As the local LLM provider
- **QA Chain** - Question answering chain with context

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| LLM | Ollama (llama2) |
| Framework | LangChain |
| Chain Type | load_qa_chain |

## How It Works

1. Define the context document
2. Create a prompt that includes context + question
3. Use LangChain's `load_qa_chain`
4. Pass user question through the chain
5. Return answer based on provided context

## Key Concepts Learned

- Prompt Templates with variables
- QA Chain usage
- Context-based answering
- Document handling

## File Structure

```
03_qa_system/
├── README.md
├── project.md
├── app.py
└── requirements.txt
```
