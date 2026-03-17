# Generative AI - Concepts

## What is Generative AI?

Generative AI refers to artificial intelligence systems that can create new content - text, images, audio, code, and more. Unlike traditional AI that classifies or predicts, generative AI creates.

## Large Language Models (LLMs)

### Definition
LLMs are deep learning models trained on vast amounts of text data to understand and generate human-like text.

### Key Concepts

1. **Transformer Architecture**
   - The underlying architecture behind modern LLMs
   - Uses self-attention mechanisms
   - Processes input sequentially while considering context

2. **Tokenization**
   - Text is broken into tokens (words, subwords, or characters)
   - Models predict the next token based on previous tokens
   - Vocabulary size varies by model (e.g., 50K to 100K tokens)

3. **Parameters**
   - Weights learned during training
   - Modern models have billions to trillions of parameters
   - More parameters generally mean better capabilities

4. **Context Window**
   - Amount of text the model can consider at once
   - Measured in tokens (e.g., 4K, 8K, 128K tokens)
   - Affects how much history the model can reference

## How LLMs Work

### Training
1. **Pre-training**: Learn language patterns from massive text corpora
2. **Fine-tuning**: Adapt to specific tasks or domains

### Inference
1. Input text is tokenized
2. Model predicts next token probability distribution
3. Sampling or greedy selection chooses next token
4. Process repeats until end token or max length

## Types of Generative AI

1. **Text Generation** - GPT, Claude, Gemini
2. **Image Generation** - DALL-E, Midjourney, Stable Diffusion
3. **Audio Generation** - ElevenLabs, AudioLM
4. **Code Generation** - CodeLlama, Copilot

## Practical Applications

- Content creation and writing assistance
- Code generation and debugging
- Customer service chatbots
- Data analysis and insights
- Education and tutoring
- Creative writing and art

## Key Terminology

| Term | Definition |
|------|------------|
| Prompt | Input text given to the model |
| Completion | Generated output from the model |
| Temperature | Controls randomness in generation |
| Top-p sampling | Nucleus sampling method |
| Few-shot learning | Providing examples in prompt |
| Zero-shot learning | Task without examples |
