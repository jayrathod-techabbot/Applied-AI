# Embeddings & Chunking - References

## Official Documentation

1. **OpenAI Embeddings**
   - https://platform.openai.com/docs/guides/embeddings
   - Official guide to using OpenAI embeddings

2. **LangChain Text Splitters**
   - https://python.langchain.com/docs/modules/data_connection/document_transformers/
   - Built-in text chunking implementations

3. **LlamaIndex Node Parsers**
   - https://docs.llamaindex.ai/en/latest/api_reference/node_parsers.html
   - Alternative chunking approaches

## Embedding Models

### Commercial APIs
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **Cohere Embeddings**: https://cohere.com/embeddings
- **Google Gemini Embeddings**: https://ai.google.dev/docs

### Open Source
- **Sentence Transformers**: https://sbert.net/
- **HuggingFace Transformers**: https://huggingface.co/models
- **FastText**: https://fasttext.cc/

## Tutorials

1. **LangChain Text Splitting Guide**
   - https://python.langchain.com/docs/extras/guides/development/splitting

2. **Chunking Strategies for Production RAG**
   - https://www.pinecone.io/learn/chunking-strategies/

3. **Choosing Chunk Sizes**
   - https://docs.llamaindex.ai/en/latest/optimizing/production_tips.html

## Research Papers

1. **"Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks"**
   - Reimers and Gurevych, 2019
   - https://arxiv.org/abs/1908.10084

2. **"Optimizing Semantic Chunking for RAG"**
   - Various industry papers on chunking optimization

## Tools and Libraries

1. **LangChain**: Document transformation and chunking
2. **LlamaIndex**: Advanced node parsing
3. **Unstructured**: Intelligent document parsing
4. **PDFPlumber**: PDF text extraction
5. **PyMuPDF**: Another PDF processing library

## Best Practices

### Chunk Size Selection
- Start with 500-1000 characters
- Adjust based on your use case
- Consider your LLM's context window
- Test with real queries

### Embedding Selection
- Match model to your language requirements
- Consider dimension vs quality tradeoff
- Test different models for your domain
- Consider multilingual needs

### Overlap Guidelines
- Use 10-20% overlap for most cases
- More overlap for technical content
- Less overlap for simple prose
