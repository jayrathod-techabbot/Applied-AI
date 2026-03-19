# Waiter Bot Project

## Problem Statement

Create a restaurant waiter bot that can:
- Greet customers
- Present the menu
- Take food orders
- Answer menu questions
- Calculate bills

## Solution

This bot uses:
- **LangChain** - For conversation chain and memory
- **Ollama** - As the local LLM provider
- **ConversationBufferMemory** - To remember the order

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| LLM | Ollama (llama2) |
| Framework | LangChain |
| Memory | ConversationBufferMemory |

## How It Works

1. Define system prompt with restaurant context
2. Provide the menu to the bot
3. Use ConversationChain for natural dialog
4. Track order items in memory
5. Calculate bill when requested

## Key Concepts Learned

- System prompts
- Conversation memory
- Chain composition
- Context management

## File Structure

```
04_waiter_bot/
├── README.md
├── project.md
├── app.py
└── requirements.txt
```
