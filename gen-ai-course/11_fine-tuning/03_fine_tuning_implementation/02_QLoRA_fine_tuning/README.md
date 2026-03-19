# QLoRA Fine-Tuning Implementation

This directory contains a comprehensive implementation of QLoRA (Quantized LoRA) fine-tuning for large language models.

## Overview

QLoRA is an advanced parameter-efficient fine-tuning method that combines LoRA with quantization to achieve extreme memory efficiency while maintaining high performance. It enables fine-tuning of large models on consumer-grade hardware.

## Key Features

- **Extreme Memory Efficiency**: 4-bit quantization reduces memory usage by ~75%
- **Parameter Efficient**: Only trains small low-rank matrices
- **High Performance**: Maintains performance close to full fine-tuning
- **Hardware Accessible**: Can run on consumer GPUs with limited VRAM
- **Production Ready**: Includes logging, checkpointing, and evaluation

## Architecture

```
QLoRA Fine-Tuning Pipeline:
1. Load Base Model (4-bit Quantized)
2. Apply LoRA Configuration
3. Prepare Training Data
4. Train LoRA Parameters
5. Evaluate and Save Model
6. Generate with Fine-tuned Model
```

## Files

- `qlora_fine_tuning.py` - Main implementation with complete training pipeline
- `requirements.txt` - Dependencies for QLoRA fine-tuning
- `README.md` - This documentation file

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from qlora_fine_tuning import QLoRAFineTuner, QLoRAConfig

# Setup configuration
config = QLoRAConfig(
    model_name="microsoft/DialoGPT-small",
    quantization_type="nf4",
    load_in_4bit=True,
    r=8,  # LoRA rank
    learning_rate=2e-4,
    batch_size=4,
    num_epochs=3
)

# Initialize trainer
trainer = QLoRAFineTuner(config)

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
config = QLoRAConfig(
    # Model settings
    model_name="microsoft/DialoGPT-medium",
    tokenizer_name=None,
    
    # Quantization settings
    quantization_type="nf4",           # "nf4" or "fp4"
    load_in_4bit=True,                 # Enable 4-bit quantization
    load_in_8bit=False,                # Disable 8-bit quantization
    bnb_4bit_compute_dtype="float16",  # Compute dtype
    bnb_4bit_quant_type="nf4",         # Quantization type
    bnb_4bit_use_double_quant=True,    # Double quantization
    
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
    output_dir="./qlora_output",
    
    # Device settings
    device="cuda" if torch.cuda.is_available() else "cpu"
)
```

## Quantization Guide

### 4-bit Quantization
- **NF4**: Normal Float 4-bit (recommended for most cases)
- **FP4**: Floating Point 4-bit
- **Benefits**: 75% memory reduction, faster inference

### 8-bit Quantization
- **Use Case**: When 4-bit causes quality degradation
- **Benefits**: 50% memory reduction, good performance

### Double Quantization
- **Purpose**: Further reduces memory usage
- **Trade-off**: Slight performance impact

## Supported Models

QLoRA works with various transformer models:

- **GPT Models**: GPT-2, DialoGPT, GPT-Neo, GPT-J
- **LLaMA Models**: LLaMA, Llama 2, Alpaca
- **Mistral Models**: Mistral, Mixtral
- **Other Models**: Any model supported by Transformers library

## Memory Requirements

### Before QLoRA
- LLaMA 7B: ~14GB VRAM
- LLaMA 13B: ~26GB VRAM
- LLaMA 30B: ~60GB VRAM

### After QLoRA
- LLaMA 7B: ~3.5GB VRAM
- LLaMA 13B: ~6.5GB VRAM
- LLaMA 30B: ~15GB VRAM

## Training Tips

### Hardware Requirements
- **Minimum**: 8GB VRAM for 7B models
- **Recommended**: 16GB VRAM for 13B models
- **High-end**: 24GB+ VRAM for 30B+ models

### Hyperparameter Tuning
- Start with default QLoRA settings
- Adjust LoRA rank based on available memory
- Use gradient accumulation for larger effective batch sizes
- Monitor memory usage during training

### Data Preparation
- Use high-quality, domain-specific data
- Ensure proper tokenization and formatting
- Consider data augmentation for better generalization

## Performance Comparison

### Memory Usage
```
Full Fine-tuning: 100% VRAM usage
LoRA: 50-70% VRAM usage
QLoRA: 25-30% VRAM usage
```

### Training Speed
```
Full Fine-tuning: 1.0x baseline
LoRA: 1.2-1.5x faster
QLoRA: 1.5-2.0x faster
```

### Model Quality
```
Full Fine-tuning: 100% quality
LoRA: 95-98% quality
QLoRA: 90-95% quality
```

## Advanced Features

### Multi-GPU Training
```python
# Automatic device mapping
config = QLoRAConfig(
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

### Mixed Precision Training
```python
# Automatic mixed precision
from torch.cuda.amp import autocast

with autocast():
    outputs = model(**batch)
    loss = outputs.loss
```

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   - Reduce batch size
   - Enable gradient checkpointing
   - Use smaller LoRA rank
   - Try 8-bit instead of 4-bit

2. **Poor Performance**
   - Increase training data
   - Adjust LoRA rank and alpha
   - Try different quantization types
   - Use higher precision compute

3. **Slow Training**
   - Use gradient accumulation
   - Enable mixed precision training
   - Optimize data loading
   - Check GPU utilization

### Debugging Tips

```python
# Check memory usage
torch.cuda.memory_summary()

# Monitor quantization
print(f"Model dtype: {model.dtype}")
print(f"Quantization config: {model.config.quantization_config}")

# Debug gradients
for name, param in model.named_parameters():
    if param.requires_grad:
        print(f"{name}: {param.grad}")
```

## Examples

### Chatbot Fine-tuning
```python
# Fine-tune for conversational AI
config = QLoRAConfig(
    model_name="microsoft/DialoGPT-medium",
    quantization_type="nf4",
    load_in_4bit=True,
    r=8,
    lora_alpha=32,
    # Training data: conversation pairs
)

# Train and deploy chatbot
trainer = QLoRAFineTuner(config)
trainer.train(conversation_data)
```

### Code Generation
```python
# Fine-tune for code generation
config = QLoRAConfig(
    model_name="bigcode/starcoder",
    quantization_type="nf4",
    load_in_4bit=True,
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
config = QLoRAConfig(
    model_name="meta-llama/Llama-2-7b-chat-hf",
    quantization_type="nf4",
    load_in_4bit=True,
    r=32,
    lora_alpha=128,
    # Training data: instruction-response pairs
)

# Follow instructions
instruction = "Write a Python function to check if a number is prime"
response = trainer.generate_text(instruction)
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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This implementation is part of the Applied AI Course materials.

## Resources

- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
- [BitsAndBytes Documentation](https://github.com/TimDettmers/bitsandbytes)
- [PEFT Documentation](https://huggingface.co/docs/peft/index)
- [Transformers Documentation](https://huggingface.co/docs/transformers/index)