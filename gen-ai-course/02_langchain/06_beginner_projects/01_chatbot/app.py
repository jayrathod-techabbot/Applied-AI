from langchain_community.chat_models import ChatOllama

llm = ChatOllama(model="llama3.1:8b")

chat_history = []

while True:
    user_input = input("You: ")

    chat_history.append({"role": "user", "content": user_input})

    response = llm.invoke(chat_history)

    chat_history.append({"role": "assistant", "content": response.content})

    print("Bot:", response.content)