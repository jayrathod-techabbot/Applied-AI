"""
Travel Planning App using LangChain and Ollama
A travel assistant to help plan your trips
"""

from langchain_community.chat_models import ChatOllama
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate

# Initialize Ollama model
llm = ChatOllama(model="llama2", temperature=0.7, base_url="http://localhost:11434")

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

# Create chat prompt template
prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), ("human", "{{input}}")]
)

# Create conversation memory - remembers trip details
memory = ConversationBufferMemory(
    return_messages=True, human_prefix="Traveler", ai_prefix="WanderBot"
)

# Create conversation chain
conversation = ConversationChain(llm=llm, memory=memory, prompt=prompt, verbose=False)

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
        response = conversation.predict(input=user_input)
        print(f"\n🌍 WanderBot: {response}")

    except KeyboardInterrupt:
        print("\n\n✈️ Session ended")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure Ollama is running")
