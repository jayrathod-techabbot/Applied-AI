"""
Waiter Bot using LangChain and Ollama
A restaurant waiter that takes orders and helps customers
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

# Initialize Ollama model
llm = ChatOllama(model="llama3.1:8b", temperature=0.7, base_url="http://localhost:11434")

# Restaurant menu with prices
MENU = """
=== RESTAURANT MENU ===

🍔 Burgers
   - Classic Burger: $8
   - Cheese Burger: $9
   - Bacon Burger: $10
   - Veggie Burger: $7

🍕 Pizza
   - Margherita: $12
   - Pepperoni: $14
   - BBQ Chicken: $15
   - Veggie Supreme: $13

🥗 Salads
   - Caesar Salad: $8
   - Garden Salad: $6
   - Greek Salad: $9

🍟 Sides
   - French Fries: $4
   - Onion Rings: $5
   - Mozzarella Sticks: $6

🥤 Drinks
   - Soft Drink: $2
   - Fresh Juice: $4
   - Coffee: $3
   - Tea: $2

🍰 Desserts
   - Ice Cream: $5
   - Cheesecake: $6
   - Apple Pie: $5
"""

# System prompt - defines the bot's role
system_prompt = f"""You are a friendly restaurant waiter named "Alex". 

You work at a nice casual restaurant. Your job is to:
1. Greet customers warmly
2. Present the menu when asked
3. Take orders politely
4. Answer questions about the menu
5. Make recommendations
6. Calculate the bill when asked

Remember the customer's order as you take it. Be helpful and courteous!

Here's the menu:
{MENU}

When calculating the bill, add up all items and give the total.
"""

# Create chat prompt template with message history placeholder
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]
)

# Create conversation memory as a plain message list
history = []

# Build LCEL chain
chain = prompt | llm | StrOutputParser()

print("=" * 50)
print("🍽️  Waiter Bot - Type 'exit' to leave")
print("=" * 50)
print("\n🤖 Alex: Welcome! I'm Alex, your waiter today.")
print("    Please have a seat. Can I get you something?")

# Main loop
while True:
    try:
        user_input = input("\nYou: ").strip()

        # Check for exit
        if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
            print("\n🤖 Alex: Thank you for dining with us!")
            print("    Please come again. Have a great day! 👋")
            break

        # Skip empty input
        if not user_input:
            continue

        # Handle bill request
        if (
            "bill" in user_input.lower()
            or "check" in user_input.lower()
            or "total" in user_input.lower()
        ):
            # Get conversation history
            print("\n🤖 Alex: Let me check your order...")
            print("\n--- Your Order So Far ---")
            for msg in history:
                if isinstance(msg, HumanMessage):
                    print(f"You: {msg.content}")
            print("-------------------------\n")

        # Get response
        response = chain.invoke({"input": user_input, "history": history})

        # Update memory manually
        history.append(HumanMessage(content=user_input))
        history.append(AIMessage(content=response))

        print(f"\n🤖 Alex: {response}")

    except KeyboardInterrupt:
        print("\n\n👋 Session ended")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure Ollama is running")