"""
Travel Planning App using LangChain and Ollama
A travel assistant to help plan your trips
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

# Initialize Ollama model
llm = ChatOllama(model="llama3.1:8b", temperature=0.7, base_url="http://localhost:11434")

# System prompt - defines the travel assistant role
system_prompt = """You are "WanderBot", a friendly and knowledgeable travel assistant.

Your expertise includes:
- Suggesting destinations based on interests
- Creating detailed trip itineraries
- Providing budget advice
- Recommending activities and attractions
- Giving packing tips
- Sharing local customs and culture

When planning trips, ask about:
- Destination (or let them decide)
- Travel dates
- Budget range
- Interests (adventure, relaxation, culture, food, etc.)
- Travel style (luxury, budget, backpacker)

Provide helpful, specific recommendations with reasons.
Remember their preferences for follow-up questions!

Be enthusiastic but practical. Use emojis to make responses engaging.
"""

# Create chat prompt template with message history placeholder
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]
)

# Create conversation memory as a plain message list - remembers trip details
history = []

# Build LCEL chain
chain = prompt | llm | StrOutputParser()

print("=" * 50)
print("✈️  Travel Planning App - Type 'exit' to quit")
print("=" * 50)
print("\n🌍 WanderBot: Hi! I'm your travel assistant!")
print("    I can help you plan amazing trips.")
print("    Where would you like to go?")

# Main loop
while True:
    try:
        user_input = input("\nYou: ").strip()

        # Check for exit
        if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
            print("\n🌍 WanderBot: Safe travels! Bon voyage! ✈️")
            break

        # Skip empty input
        if not user_input:
            continue

        # Get response
        response = chain.invoke({"input": user_input, "history": history})

        # Update memory manually
        history.append(HumanMessage(content=user_input))
        history.append(AIMessage(content=response))

        print(f"\n🌍 WanderBot: {response}")

    except KeyboardInterrupt:
        print("\n\n✈️ Session ended")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure Ollama is running")