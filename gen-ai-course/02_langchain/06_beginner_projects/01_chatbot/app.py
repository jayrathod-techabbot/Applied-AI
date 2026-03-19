"""
Simple ChatBot using LangChain and Ollama
A beginner-friendly conversational AI bot with memory
"""

from langchain_community.chat_models import ChatOllama
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Initialize the Ollama model (using llama2)
# You can change to other models like: mistral, codellama, etc.
llm = ChatOllama(
    model="llama2",  # Ollama model name
    temperature=0.7,  # Controls randomness (0-1)
    base_url="http://localhost:11434",  # Default Ollama URL
)

# Create conversation memory - stores chat history
memory = ConversationBufferMemory(return_messages=True)  # Return as message objects

# Create the conversation chain
conversation = ConversationChain(
    llm=llm, memory=memory, verbose=False  # Set True to see debug info
)

print("=" * 50)
print("🤖 ChatBot - Type 'exit' or 'quit' to stop")
print("=" * 50)

# Main chat loop
while True:
    try:
        # Get user input
        user_input = input("\nYou: ").strip()

        # Check for exit commands
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\n👋 Goodbye! Have a great day!")
            break

        # Skip empty input
        if not user_input:
            continue

        # Get AI response
        response = conversation.predict(input=user_input)

        # Display response
        print(f"\nBot: {response}")

    except KeyboardInterrupt:
        print("\n\n👋 Chat ended by user")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure Ollama is running (ollama serve)")
