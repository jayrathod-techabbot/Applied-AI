# Full Fine-Tuning Implementation

This directory contains a comprehensive implementation of full fine-tuning for large language models.

## Overview

Full fine-tuning is the traditional approach to fine-tuning large language models where all model parameters are updated during training. This method typically achieves the best performance but requires significant computational resources and careful optimization.

## Key Features

- **Maximum Performance**: Updates all model parameters for optimal results
- **Advanced Optimization**: Mixed precision training, gradient checkpointing, early stopping
- **Memory Efficient**: Gradient accumulation and checkpointing for large models
- **Production Ready**: Comprehensive logging, checkpointing, and evaluation
- **Flexible Configuration**: Extensive hyperparameter tuning options

## Architecture

```
Full Fine-Tuning Pipeline:
1. Load Base Model (All Parameters Trainable)
2. Prepare Training Data
3. Setup Advanced Optimization (Mixed Precision, Checkpointing)
4. Train All Model Parameters
5. Evaluate and Save Best Model
6. Generate with Fine-tuned Model
```

## Files

- `full_fine_tuning.py` - Main implementation with complete training pipeline
- `requirements.txt` - Dependencies for full fine-tuning
- `README.md` - This documentation file

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from full_fine_tuning import FullFineTuner, FullFineTuningConfig

# Setup configuration
config = FullFineTuningConfig(
    model_name="microsoft/DialoGPT-small",
    learning_rate=2e-5,
    batch_size=4,
    num_epochs=3
)

# Initialize trainer
trainer = FullFineTuner(config)

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
config = FullFineTuningConfig(
    # Model settings
    model_name="microsoft/DialoGPT-medium",
    tokenizer_name=None,
    
    # Training settings
    learning_rate=2e-5,
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
    use_gradient_checkpointing=True,
    use_mixed_precision=True,
    
    # Logging and saving
    save_steps=500,
    eval_steps=250,
    logging_steps=100,
    output_dir="./full_fine_tuning_output",
    
    # Device settings
    device="cuda" if torch.cuda.is_available() else "cpu",
    
    # Advanced settings
    early_stopping_patience=3,
    early_stopping_metric="eval_loss",
    save_total_limit=3
)
```

## Advanced Features

### Mixed Precision Training

```python
# Automatic mixed precision for faster training and reduced memory usage
config = FullFineTuningConfig(
    use_mixed_precision=True,
    # Other settings...
)
```

### Gradient Checkpointing

```python
# Memory-efficient training by trading compute for memory
config = FullFineTuningConfig(
    use_gradient_checkpointing=True,
    # Other settings...
)
```

### Gradient Accumulation

```python
# Simulate larger batch sizes with limited memory
config = FullFineTuningConfig(
    batch_size=4,
    gradient_accumulation_steps=4,  # Effective batch size = 16
    # Other settings...
)
```

### Early Stopping

```python
# Stop training when validation metrics stop improving
config = FullFineTuningConfig(
    early_stopping_patience=3,
    early_stopping_metric="eval_loss",
    # Other settings...
)
```

## Performance Optimization

### Memory Optimization

1. **Gradient Checkpointing**: Reduces memory usage by recomputing activations
2. **Mixed Precision**: Uses fp16 instead of fp32 for reduced memory and faster training
3. **Gradient Accumulation**: Allows larger effective batch sizes with limited memory
4. **Batch Size Optimization**: Find the largest batch size that fits in memory

### Speed Optimization

1. **Mixed Precision**: Faster computation with fp16
2. **Gradient Accumulation**: Better gradient estimates with larger effective batch sizes
3. **Optimized Data Loading**: Use multiple workers and pin memory
4. **Learning Rate Scheduling**: Proper warmup and decay schedules

### Quality Optimization

1. **Proper Learning Rates**: Start with recommended values and tune
2. **Weight Decay**: Regularization to prevent overfitting
3. **Early Stopping**: Prevent overfitting with validation monitoring
4. **Multiple Runs**: Average results from multiple training runs

## Training Tips

### Hardware Requirements

- **Minimum**: 16GB VRAM for 7B models
- **Recommended**: 32GB+ VRAM for 13B+ models
- **Multi-GPU**: Use for larger models or faster training

### Hyperparameter Tuning

#### Learning Rate
- **Start**: 2e-5 for most models
- **Range**: 1e-5 to 5e-5
- **Schedule**: Linear warmup + cosine decay

#### Batch Size
- **Start**: 4-8 for most setups
- **Increase**: If memory allows
- **Accumulation**: Use for larger effective batch sizes

#### Weight Decay
- **Start**: 0.01
- **Range**: 0.001 to 0.1
- **Purpose**: Regularization

### Data Preparation

1. **Quality**: Use high-quality, domain-specific data
2. **Quantity**: More data generally leads to better performance
3. **Format**: Proper tokenization and formatting
4. **Augmentation**: Consider data augmentation for better generalization

## Comparison with PEFT Methods

### Performance

| Method | Performance | Parameters | Memory | Speed |
|--------|------------|------------|--------|-------|
| Full Fine-tuning | Best | 100% | High | Medium |
| LoRA | Good | 0.1-1% | Medium | Fast |
| QLoRA | Good | 0.1-1% | Low | Fast |
| IA³ | Good | 0.05-0.5% | Low | Fast |

### When to Use Full Fine-tuning

1. **Maximum Performance Required**: When you need the best possible results
2. **Sufficient Resources**: When you have adequate GPU memory and compute
3. **Large Dataset**: When you have substantial training data
4. **No Parameter Constraints**: When parameter efficiency is not critical

### When to Use PEFT Methods

1. **Resource Constraints**: Limited GPU memory or compute
2. **Fast Iteration**: Need quick experimentation and prototyping
3. **Parameter Efficiency**: Want to preserve most of the original model
4. **Multiple Tasks**: Need to fine-tune for multiple tasks efficiently

## Advanced Training Techniques

### Multi-GPU Training

```python
# Distributed training across multiple GPUs
from torch.nn.parallel import DistributedDataParallel

# Setup distributed training
model = DistributedDataParallel(model)
```

### Custom Loss Functions

```python
# Implement custom loss for specific tasks
class CustomLoss(nn.Module):
    def forward(self, outputs, labels):
        # Your custom loss computation
        return loss
```

### Learning Rate Scheduling

```python
# Advanced learning rate schedules
from transformers import get_cosine_schedule_with_warmup

scheduler = get_cosine_schedule_with_warmup(
    optimizer,
    num_warmup_steps=warmup_steps,
    num_training_steps=total_steps
)
```

## Troubleshooting

### Common Issues

1. **Out of Memory**
   - Reduce batch size
   - Enable gradient checkpointing
   - Use gradient accumulation
   - Try mixed precision

2. **Poor Performance**
   - Increase training data
   - Adjust learning rate
   - Use longer training
   - Check data quality

3. **Slow Training**
   - Enable mixed precision
   - Use gradient accumulation
   - Optimize data loading
   - Check GPU utilization

### Debugging Tips

```python
# Monitor memory usage
torch.cuda.memory_summary()

# Check gradients
for name, param in model.named_parameters():
    if param.requires_grad:
        print(f"{name}: {param.grad}")

# Debug training loop
print(f"Loss: {loss.item()}")
print(f"Learning rate: {scheduler.get_last_lr()[0]}")
```

## Examples

### Chatbot Fine-tuning
```python
# Fine-tune for conversational AI
config = FullFineTuningConfig(
    model_name="microsoft/DialoGPT-medium",
    learning_rate=2e-5,
    batch_size=8,
    # Training data: conversation pairs
)

trainer = FullFineTuner(config)
trainer.train(conversation_data)
```

### Code Generation
```python
# Fine-tune for code generation
config = FullFineTuningConfig(
    model_name="bigcode/starcoder",
    learning_rate=1e-5,
    batch_size=4,
    # Training data: code snippets
)

trainer = FullFineTuner(config)
trainer.train(code_data)
```

### Instruction Following
```python
# Fine-tune for instruction following
config = FullFineTuningConfig(
    model_name="meta-llama/Llama-2-7b-chat-hf",
    learning_rate=5e-5,
    batch_size=2,
    # Training data: instruction-response pairs
)

trainer = FullFineTuner(config)
trainer.train(instruction_data)
```

## Production Deployment

### Model Saving
```python
# Save the fine-tuned model
trainer.save_model("production_model")
```

### Inference Optimization
```python
# Optimized inference
config = FullFineTuningConfig(
    use_mixed_precision=True,
    # Other inference settings...
)

# Batch inference for multiple requests
def batch_generate(prompts, max_length=100):
    inputs = tokenizer(prompts, return_tensors="pt", padding=True)
    outputs = model.generate(**inputs, max_length=max_length)
    return tokenizer.batch_decode(outputs, skip_special_tokens=True)
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

- [Transformers Documentation](https://huggingface.co/docs/transformers/index)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [Mixed Precision Training](https://pytorch.org/docs/stable/notes/amp_examples.html)
- [Gradient Checkpointing](https://pytorch.org/docs/stable/checkpoint.html)
- [DeepSpeed Integration](https://www.deepspeed.ai/)