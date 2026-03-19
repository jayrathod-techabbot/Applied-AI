# ChatBot Project

## Problem Statement

Create a conversational chatbot that can:
- Have natural conversations with users
- Remember context from previous messages
- Provide helpful responses using AI

## Solution

This chatbot uses:
- **LangChain** - For building the conversation chain
- **Ollama** - As the local LLM provider (llama2 model)
- **ConversationBufferMemory** - To store chat history

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| LLM | Ollama (llama2) |
| Framework | LangChain |
| Memory | ConversationBufferMemory |

## How It Works

1. Initialize Ollama chat model
2. Create conversation memory to store history
3. Build a ConversationChain combining model + memory
4. Loop to accept user input and get AI responses
5. Display responses and maintain conversation context

## Key Concepts Learned

- Chat Models in LangChain
- Prompt Templates
- Conversation Memory
- Chain Composition

## File Structure

```
01_chatbot/
├── README.md      # Setup instructions
├── project.md     # This file
├── app.py         # Main application
└── requirements.txt
```
