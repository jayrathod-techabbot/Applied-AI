"""
Summarization Tool using LangChain and Ollama
A beginner-friendly text summarization app
"""

from langchain_community.chat_models import ChatOllama
from langchain.chains.summarize import load_summarize_chain
from langchain.schema import Document

# Initialize Ollama model
llm = ChatOllama(
    model="llama2",
    temperature=0.3,  # Lower temp for more focused output
    base_url="http://localhost:11434",
)

# Load the summarization chain
# chain_type="stuff" passes all text to LLM at once (good for short docs)
summarize_chain = load_summarize_chain(llm, chain_type="stuff", verbose=False)

print("=" * 50)
print("📝 Summarization Tool - Type 'exit' to quit")
print("=" * 50)

# Main loop
while True:
    print("\n" + "-" * 40)
    print("Paste your text below (press Enter twice to submit):")
    print("-" * 40)

    # Read multi-line input (enter twice to finish)
    lines = []
    while True:
        try:
            line = input()
            if line == "":
                # Check if we have content
                if lines:
                    break
            lines.append(line)
        except EOFError:
            break

    text = "\n".join(lines).strip()

    # Check for exit
    if text.lower() in ["exit", "quit"]:
        print("\n👋 Goodbye!")
        break

    # Skip empty input
    if not text:
        continue

    # Create Document object (LangChain uses Document format)
    doc = [Document(page_content=text)]

    # Generate summary
    print("\n⏳ Generating summary...")
    try:
        result = summarize_chain.invoke(doc)
        summary = result["output_text"]

        print("\n" + "=" * 40)
        print("📋 SUMMARY:")
        print("=" * 40)
        print(summary)
        print("=" * 40)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure Ollama is running")
