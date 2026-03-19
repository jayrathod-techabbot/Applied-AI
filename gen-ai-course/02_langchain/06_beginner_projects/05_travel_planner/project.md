# Travel Planning App Project

## Problem Statement

Create a travel planning assistant that can:
- Suggest destinations
- Create trip itineraries
- Provide travel tips
- Help with budget planning
- Recommend activities

## Solution

This app uses:
- **LangChain** - For conversation chain and memory
- **Ollama** - As the local LLM provider
- **ConversationBufferMemory** - To remember trip preferences

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| LLM | Ollama (llama2) |
| Framework | LangChain |
| Memory | ConversationBufferMemory |

## How It Works

1. Define system prompt with travel expertise
2. Use ConversationChain for natural dialog
3. Remember user preferences (destination, budget, dates)
4. Provide personalized travel advice
5. Create detailed itineraries

## Key Concepts Learned

- System prompts with expertise
- Conversation memory
- Chain configuration
- Context retention

## File Structure

```
05_travel_planner/
├── README.md
├── project.md
├── app.py
└── requirements.txt
```
