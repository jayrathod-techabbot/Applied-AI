# LoRA Fine-Tuning Implementation

This directory contains a comprehensive implementation of LoRA (Low-Rank Adaptation) fine-tuning for large language models.

## Overview

LoRA is a parameter-efficient fine-tuning method that adds trainable low-rank matrices to frozen model weights. This approach significantly reduces the number of trainable parameters while maintaining performance.

## Key Features

- **Parameter Efficient**: Only trains small low-rank matrices instead of full model weights
- **Memory Efficient**: Reduces GPU memory requirements during training
- **Fast Training**: Faster convergence compared to full model fine-tuning
- **Easy Integration**: Works with popular models and frameworks
- **Production Ready**: Includes logging, checkpointing, and evaluation

## Architecture

```
LoRA Fine-Tuning Pipeline:
1. Load Base Model (Frozen)
2. Apply LoRA Configuration
3. Prepare Training Data
4. Train LoRA Parameters
5. Evaluate and Save Model
6. Generate with Fine-tuned Model
```

## Files

- `lora_fine_tuning.py` - Main implementation with complete training pipeline
- `requirements.txt` - Dependencies for LoRA fine-tuning
- `README.md` - This documentation file

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from lora_fine_tuning import LoRAFineTuner, LoRAConfig

# Setup configuration
config = LoRAConfig(
    model_name="microsoft/DialoGPT-small",
    r=8,  # LoRA rank
    learning_rate=2e-4,
    batch_size=4,
    num_epochs=3
)

# Initialize trainer
trainer = LoRAFineTuner(config)

# Prepare data
train_texts = ["Your training data here..."]
trainer.prepare_data(train_texts)

# Train model
trainer.train(train_texts)

# Generate text
prompt = "Hello, how are you?"
generated = trainer.generate_text(prompt)
print(generated)
```

### Advanced Configuration

```python
config = LoRAConfig(
    # Model settings
    model_name="microsoft/DialoGPT-medium",
    tokenizer_name=None,
    
    # LoRA settings
    r=4,                    # Rank of low-rank matrices
    lora_alpha=32,          # Scaling factor
    lora_dropout=0.1,       # Dropout rate
    target_modules=None,    # Auto-detected based on model
    
    # Training settings
    learning_rate=2e-4,
    batch_size=4,
    num_epochs=3,
    warmup_steps=100,
    weight_decay=0.01,
    
    # Data settings
    max_length=512,
    train_split=0.8,
    
    # Optimization settings
    gradient_accumulation_steps=1,
    max_grad_norm=1.0,
    
    # Logging and saving
    save_steps=500,
    eval_steps=250,
    logging_steps=100,
    output_dir="./lora_output",
    
    # Device settings
    device="cuda" if torch.cuda.is_available() else "cpu"
)
```

## Supported Models

LoRA works with various transformer models:

- **GPT Models**: GPT-2, DialoGPT, GPT-Neo, GPT-J
- **LLaMA Models**: LLaMA, Llama 2, Alpaca
- **Mistral Models**: Mistral, Mixtral
- **Other Models**: Any model supported by Transformers library

## LoRA Configuration Guide

### Rank (r)
- **Low (2-4)**: Minimal parameters, good for small datasets
- **Medium (8-16)**: Balanced performance and efficiency
- **High (32-64)**: More expressive, better for complex tasks

### Alpha (lora_alpha)
- Controls the scaling of LoRA updates
- Common values: 16, 32, 64
- Higher values = stronger LoRA influence

### Target Modules
- **GPT Models**: `["c_attn", "c_proj"]`
- **LLaMA Models**: `["q_proj", "v_proj", "k_proj", "o_proj"]`
- **Mistral Models**: `["q_proj", "v_proj", "k_proj", "o_proj"]`

## Training Tips

### Data Preparation
- Use high-quality, domain-specific data
- Ensure proper tokenization and formatting
- Consider data augmentation for better generalization

### Hyperparameter Tuning
- Start with default LoRA settings (r=4, alpha=32)
- Adjust learning rate based on model size
- Use gradient accumulation for larger effective batch sizes

### Monitoring
- Track training and validation loss
- Monitor perplexity for language models
- Use early stopping to prevent overfitting

## Evaluation Metrics

### Perplexity
Measures how well the model predicts the next token:
```python
metrics = trainer.evaluate()
print(f"Perplexity: {metrics['perplexity']:.2f}")
```

### Custom Metrics
Implement custom evaluation functions:
```python
def custom_evaluation(model, eval_dataloader):
    # Your evaluation logic here
    return metrics
```

## Production Deployment

### Model Saving
```python
# Save the fine-tuned model
trainer.save_model("production_model")

# Load for inference
from peft import PeftModel
model = PeftModel.from_pretrained(base_model, "production_model")
```

### Inference Optimization
- Use half-precision (fp16) for faster inference
- Implement batching for multiple requests
- Consider model quantization for edge deployment

## Advanced Features

### Multi-GPU Training
```python
# Automatic device mapping
config = LoRAConfig(
    device="cuda",
    # Other settings...
)
```

### Gradient Checkpointing
```python
# Enable for memory efficiency
model.gradient_checkpointing_enable()
```

### Custom Loss Functions
```python
# Implement custom loss
class CustomLoss(nn.Module):
    def forward(self, outputs, labels):
        # Your loss computation
        return loss
```

## Troubleshooting

### Common Issues

1. **Out of Memory**
   - Reduce batch size
   - Enable gradient checkpointing
   - Use smaller LoRA rank

2. **Poor Performance**
   - Increase training data
   - Adjust LoRA rank and alpha
   - Try different learning rates

3. **Slow Training**
   - Use gradient accumulation
   - Enable mixed precision training
   - Optimize data loading

### Debugging Tips

```python
# Check trainable parameters
model.print_trainable_parameters()

# Monitor memory usage
torch.cuda.memory_summary()

# Debug gradients
for name, param in model.named_parameters():
    if param.requires_grad:
        print(f"{name}: {param.grad}")
```

## Examples

### Chatbot Fine-tuning
```python
# Fine-tune for conversational AI
config = LoRAConfig(
    model_name="microsoft/DialoGPT-medium",
    r=8,
    lora_alpha=32,
    # Training data: conversation pairs
)

# Train and deploy chatbot
trainer = LoRAFineTuner(config)
trainer.train(conversation_data)
```

### Code Generation
```python
# Fine-tune for code generation
config = LoRAConfig(
    model_name="bigcode/starcoder",
    r=16,
    lora_alpha=64,
    # Training data: code snippets
)

# Generate code
prompt = "def fibonacci(n):"
code = trainer.generate_text(prompt, max_length=200)
```

### Instruction Following
```python
# Fine-tune for instruction following
config = LoRAConfig(
    model_name="meta-llama/Llama-2-7b-chat-hf",
    r=32,
    lora_alpha=128,
    # Training data: instruction-response pairs
)

# Follow instructions
instruction = "Write a Python function to check if a number is prime"
response = trainer.generate_text(instruction)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This implementation is part of the Applied AI Course materials.

## Resources

- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [PEFT Documentation](https://huggingface.co/docs/peft/index)
- [Transformers Documentation](https://huggingface.co/docs/transformers/index)