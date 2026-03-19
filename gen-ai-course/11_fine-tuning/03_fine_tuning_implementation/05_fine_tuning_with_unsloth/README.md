# Unsloth Fine-Tuning Implementation

This directory contains a comprehensive implementation of fine-tuning using Unsloth, a library that optimizes LoRA training for extreme speed and memory efficiency.

## Overview

Unsloth is a library that provides optimized implementations of LoRA training, offering significant improvements in training speed and memory efficiency compared to standard implementations. It's particularly useful for fine-tuning large language models on consumer hardware.

## Key Features

- **Extreme Speed**: Up to 2-3x faster training compared to standard LoRA
- **Memory Efficient**: Optimized memory usage for larger models on limited hardware
- **Easy Integration**: Drop-in replacement for standard PEFT implementations
- **Production Ready**: Includes logging, checkpointing, and evaluation
- **Benchmarking**: Built-in performance and memory benchmarking

## Architecture

```
Unsloth Fine-Tuning Pipeline:
1. Load Model with Unsloth Optimizations
2. Apply Optimized LoRA Configuration
3. Prepare Training Data
4. Train with Optimized AdamW and Gradient Checkpointing
5. Evaluate and Save Model
6. Generate with Fine-tuned Model
```

## Files

- `unsloth_fine_tuning.py` - Main implementation with complete training pipeline
- `requirements.txt` - Dependencies for Unsloth fine-tuning
- `README.md` - This documentation file

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

**Note**: Unsloth requires specific CUDA versions. Make sure your environment is compatible.

### Basic Usage

```python
from unsloth_fine_tuning import UnslothFineTuner, UnslothConfig

# Setup configuration
config = UnslothConfig(
    model_name="microsoft/DialoGPT-small",
    max_seq_length=1024,
    r=16,  # Higher rank for better performance
    learning_rate=2e-4,
    batch_size=4,
    num_epochs=3
)

# Initialize trainer
trainer = UnslothFineTuner(config)

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
config = UnslothConfig(
    # Model settings
    model_name="microsoft/DialoGPT-medium",
    tokenizer_name=None,
    
    # Unsloth settings
    max_seq_length=2048,        # Maximum sequence length
    dtype=None,                 # Auto-detect dtype
    load_in_4bit=True,          # 4-bit quantization
    
    # LoRA settings
    r=16,                       # Rank (higher for better performance)
    lora_alpha=16,              # Alpha parameter
    lora_dropout=0.1,           # Dropout rate
    target_modules=None,        # Auto-detected based on model
    
    # Training settings
    learning_rate=2e-4,
    batch_size=4,
    num_epochs=3,
    warmup_steps=10,
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
    output_dir="./unsloth_output",
    
    # Device settings
    device="cuda" if torch.cuda.is_available() else "cpu"
)
```

## Unsloth Advantages

### Performance Improvements

| Metric | Standard LoRA | Unsloth | Improvement |
|--------|---------------|---------|-------------|
| Training Speed | 1.0x | 2.0-3.0x | 100-200% |
| Memory Usage | 100% | 60-80% | 20-40% |
| GPU Utilization | 70-80% | 90-95% | 10-15% |

### Key Optimizations

1. **Optimized Kernels**: Custom CUDA kernels for faster computation
2. **Memory Management**: Efficient memory allocation and reuse
3. **Gradient Checkpointing**: Advanced checkpointing strategies
4. **8-bit AdamW**: Memory-efficient optimizer implementation
5. **Mixed Precision**: Automatic mixed precision handling

## Supported Models

Unsloth works with various transformer models:

- **GPT Models**: GPT-2, DialoGPT, GPT-Neo, GPT-J
- **LLaMA Models**: LLaMA, Llama 2, Alpaca
- **Mistral Models**: Mistral, Mixtral
- **Other Models**: Any model supported by Transformers library

## Training Tips

### Hardware Requirements

- **Minimum**: 8GB VRAM for 7B models
- **Recommended**: 16GB VRAM for 13B models
- **High-end**: 24GB+ VRAM for 30B+ models

### Hyperparameter Tuning

#### LoRA Rank (r)
- **Small Models (7B)**: r=16-32
- **Medium Models (13B)**: r=32-64
- **Large Models (30B+)**: r=64-128

#### Learning Rate
- **Start**: 2e-4 for most models
- **Range**: 1e-4 to 5e-4
- **Adjustment**: Lower for larger models

#### Batch Size
- **Start**: 4-8 for most setups
- **Optimization**: Use gradient accumulation for larger effective batch sizes

### Data Preparation

1. **Quality**: Use high-quality, domain-specific data
2. **Format**: Proper tokenization and formatting
3. **Augmentation**: Consider data augmentation for better generalization

## Benchmarking

Unsloth includes built-in benchmarking capabilities:

```python
# Benchmark training performance
benchmark_results = trainer.benchmark_training(train_texts[:100])

print(f"Training speed: {benchmark_results['time_per_batch']:.4f}s per batch")
print(f"Memory usage: {benchmark_results['memory_usage_mb']:.2f}MB")
print(f"GPU utilization: {benchmark_results['gpu_utilization']:.2f}%")
print(f"Peak memory: {benchmark_results['peak_memory_mb']:.2f}MB")
```

## Advanced Features

### Custom Optimizers

```python
# Use different optimizers
self.optimizer = FastLanguageModel.get_optimizer(
    self.model,
    optimizer_name="adamw_8bit",  # or "adamw_32bit"
    learning_rate=self.config.learning_rate,
    weight_decay=self.config.weight_decay,
)
```

### Gradient Checkpointing

```python
# Enable Unsloth's optimized gradient checkpointing
self.model = FastLanguageModel.get_peft_model(
    self.model,
    use_gradient_checkpointing="unsloth",  # Use Unsloth's checkpointing
    # Other settings...
)
```

### Mixed Precision

```python
# Automatic mixed precision
config = UnslothConfig(
    dtype=None,  # Auto-detect optimal dtype
    # Other settings...
)
```

## Performance Optimization

### Memory Optimization

1. **4-bit Quantization**: Use `load_in_4bit=True`
2. **Gradient Checkpointing**: Enable Unsloth's checkpointing
3. **8-bit Optimizers**: Use 8-bit AdamW
4. **Batch Size**: Optimize for available memory

### Speed Optimization

1. **Sequence Length**: Use optimal sequence lengths
2. **LoRA Rank**: Balance rank with performance
3. **Mixed Precision**: Enable automatic mixed precision
4. **Data Loading**: Optimize data pipeline

### Quality Optimization

1. **LoRA Rank**: Use higher ranks for better performance
2. **Training Data**: Use high-quality, diverse data
3. **Learning Rate**: Proper scheduling and warmup
4. **Regularization**: Appropriate dropout and weight decay

## Troubleshooting

### Common Issues

1. **CUDA Compatibility**
   - Ensure CUDA version compatibility
   - Check Unsloth installation
   - Verify GPU drivers

2. **Memory Issues**
   - Reduce batch size
   - Enable 4-bit quantization
   - Use gradient accumulation

3. **Performance Issues**
   - Check GPU utilization
   - Verify Unsloth optimizations
   - Monitor memory usage

### Debugging Tips

```python
# Check Unsloth availability
try:
    from unsloth import FastLanguageModel
    print("Unsloth available")
except ImportError:
    print("Unsloth not available")

# Monitor GPU usage
import GPUtil
gpus = GPUtil.getGPUs()
for gpu in gpus:
    print(f"GPU {gpu.id}: {gpu.load*100:.1f}% utilization")

# Check memory usage
import torch
print(f"Memory allocated: {torch.cuda.memory_allocated() / 1024**3:.2f}GB")
print(f"Memory cached: {torch.cuda.memory_reserved() / 1024**3:.2f}GB")
```

## Examples

### Chatbot Fine-tuning
```python
# Fine-tune for conversational AI
config = UnslothConfig(
    model_name="microsoft/DialoGPT-medium",
    max_seq_length=1024,
    r=32,
    # Training data: conversation pairs
)

trainer = UnslothFineTuner(config)
trainer.train(conversation_data)
```

### Code Generation
```python
# Fine-tune for code generation
config = UnslothConfig(
    model_name="bigcode/starcoder",
    max_seq_length=2048,
    r=64,
    # Training data: code snippets
)

trainer = UnslothFineTuner(config)
trainer.train(code_data)
```

### Instruction Following
```python
# Fine-tune for instruction following
config = UnslothConfig(
    model_name="meta-llama/Llama-2-7b-chat-hf",
    max_seq_length=2048,
    r=32,
    # Training data: instruction-response pairs
)

trainer = UnslothFineTuner(config)
trainer.train(instruction_data)
```

## Production Deployment

### Model Saving
```python
# Save the fine-tuned model
trainer.save_model("production_model")

# Load for inference
from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained("production_model")
```

### Inference Optimization
```python
# Optimized inference
def optimized_generate(prompt, max_length=100):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            do_sample=True,
            top_p=0.95,
            temperature=0.7
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
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

- [Unsloth Documentation](https://github.com/unslothai/unsloth)
- [Unsloth GitHub](https://github.com/unslothai/unsloth)
- [PEFT Documentation](https://huggingface.co/docs/peft/index)
- [Transformers Documentation](https://huggingface.co/docs/transformers/index)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)