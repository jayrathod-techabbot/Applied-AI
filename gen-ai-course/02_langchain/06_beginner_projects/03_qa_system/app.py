"""
Q&A System using LangChain and Ollama
A beginner-friendly question answering app based on context
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Initialize Ollama model
llm = ChatOllama(model="llama3.1:8b", temperature=0.3, base_url="http://localhost:11434")

# Sample context - you can replace this with your own text
context = """
Artificial Intelligence (AI) is a branch of computer science that aims to create 
intelligent machines that can think and act like humans. AI has become increasingly 
important in today's world, with applications in various fields such as healthcare, 
finance, education, and transportation.

There are three main types of AI:
1. Narrow AI - Designed for specific tasks (like voice assistants)
2. General AI - Can perform any intellectual task that a human can do
3. Super AI - Hypothetical AI that surpasses human intelligence

Machine Learning (ML) is a subset of AI that enables systems to learn from data 
without being explicitly programmed. Deep Learning is a further subset of ML 
that uses neural networks with many layers.

The benefits of AI include increased efficiency, better decision-making, 
automation of repetitive tasks, and the ability to process large amounts of data.
However, there are also concerns about job displacement, privacy, and the ethical 
use of AI technology.
"""

# Create a Document from the context
doc = [Document(page_content=context)]

# Create custom prompt template
prompt_template = """Use the following context to answer the question at the end.

Context: {context}

Question: {question}

Provide a clear and accurate answer based only on the context above.
If the answer is not in the context, say "I don't have enough information to answer that."
"""

# Create the prompt
prompt = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

# Build QA chain using LCEL (LangChain Expression Language)
qa_chain = (
    {
        "context": RunnablePassthrough() | (lambda x: x["context"]),
        "question": RunnablePassthrough() | (lambda x: x["question"]),
    }
    | prompt
    | llm
    | StrOutputParser()
)

print("=" * 50)
print("❓ Q&A System - Type 'exit' to quit")
print("=" * 50)
print("\n📄 Context loaded. Ask questions about the content!")

# Main loop
while True:
    print("\n" + "-" * 40)
    question = input("Your question: ").strip()

    # Check for exit
    if question.lower() in ["exit", "quit"]:
        print("\n👋 Goodbye!")
        break

    # Skip empty input
    if not question:
        continue

    # Get answer
    print("⏳ Thinking...")
    try:
        result = qa_chain.invoke({
            "context": "\n".join([d.page_content for d in doc]),
            "question": question
        })

        print("\n" + "=" * 40)
        print("💡 ANSWER:")
        print("=" * 40)
        print(result)
        print("=" * 40)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure Ollama is running")