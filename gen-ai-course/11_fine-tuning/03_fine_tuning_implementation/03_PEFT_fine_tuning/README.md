# PEFT Fine-Tuning Implementation

This directory contains a comprehensive implementation of various PEFT (Parameter-Efficient Fine-Tuning) methods for large language models.

## Overview

PEFT is a collection of parameter-efficient fine-tuning methods that allow you to fine-tune large language models with significantly fewer trainable parameters. This implementation supports multiple PEFT techniques including LoRA, QLoRA, IA³, AdaLoRA, Prefix Tuning, and Prompt Tuning.

## Supported PEFT Methods

### 1. LoRA (Low-Rank Adaptation)
- **Description**: Adds trainable low-rank matrices to frozen model weights
- **Use Case**: General-purpose fine-tuning with good performance
- **Memory Efficiency**: High
- **Training Speed**: Fast

### 2. QLoRA (Quantized LoRA)
- **Description**: Combines LoRA with 4-bit quantization
- **Use Case**: Fine-tuning large models on limited hardware
- **Memory Efficiency**: Very High
- **Training Speed**: Very Fast

### 3. IA³ (Infused Adapter by Inhibiting and Amplifying Inner Activations)
- **Description**: Learns scaling vectors for intermediate activations
- **Use Case**: When you want to preserve model weights completely
- **Memory Efficiency**: Very High
- **Training Speed**: Fast

### 4. AdaLoRA (Adaptive LoRA)
- **Description**: Dynamically adjusts LoRA ranks during training
- **Use Case**: When you want automatic rank optimization
- **Memory Efficiency**: High
- **Training Speed**: Medium

### 5. Prefix Tuning
- **Description**: Learns virtual tokens prepended to input
- **Use Case**: Task-specific adaptation with minimal parameters
- **Memory Efficiency**: Very High
- **Training Speed**: Fast

### 6. Prompt Tuning
- **Description**: Learns soft prompts for task adaptation
- **Use Case**: Zero-shot to few-shot adaptation
- **Memory Efficiency**: Very High
- **Training Speed**: Fast

## Architecture

```
PEFT Fine-Tuning Pipeline:
1. Load Base Model (Frozen or Quantized)
2. Apply PEFT Configuration
3. Prepare Training Data
4. Train PEFT Parameters
5. Evaluate and Save Model
6. Generate with Fine-tuned Model
```

## Files

- `peft_fine_tuning.py` - Main implementation with complete training pipeline
- `requirements.txt` - Dependencies for PEFT fine-tuning
- `README.md` - This documentation file

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from peft_fine_tuning import PEFTFineTuner, PEFTConfig

# Setup configuration for LoRA
config = PEFTConfig(
    model_name="microsoft/DialoGPT-small",
    peft_method="lora",
    lora_r=8,
    learning_rate=2e-4,
    batch_size=4,
    num_epochs=3
)

# Initialize trainer
trainer = PEFTFineTuner(config)

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
config = PEFTConfig(
    # Model settings
    model_name="microsoft/DialoGPT-medium",
    tokenizer_name=None,
    
    # PEFT method
    peft_method="lora",  # "lora", "qlora", "ia3", "adalora", "prefix", "prompt"
    
    # LoRA settings (for lora, qlora, adalora)
    lora_r=4,
    lora_alpha=32,
    lora_dropout=0.1,
    lora_target_modules=None,
    
    # IA³ settings (for ia3)
    ia3_target_modules=None,
    ia3_feedforward_modules=None,
    
    # AdaLoRA settings (for adalora)
    adalora_target_r=8,
    adalora_init_r=12,
    adalora_tinit=50,
    adalora_tfraction=1.0,
    adalora_dss_target_rank=3,
    
    # Prefix tuning settings (for prefix)
    num_virtual_tokens=10,
    prefix_projection=False,
    
    # Prompt tuning settings (for prompt)
    prompt_tuning_init="TEXT",  # "TEXT" or "RANDOM"
    prompt_tuning_num_virtual_tokens=10,
    
    # Quantization settings (for qlora)
    quantization_type="nf4",
    load_in_4bit=True,
    load_in_8bit=False,
    
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
    output_dir="./peft_output",
    
    # Device settings
    device="cuda" if torch.cuda.is_available() else "cpu"
)
```

## Method Comparison

### Parameter Efficiency

| Method | Trainable Parameters | Memory Usage | Training Speed |
|--------|---------------------|--------------|----------------|
| Full Fine-tuning | 100% | 100% | 1.0x |
| LoRA | 0.1-1% | 50-70% | 1.2-1.5x |
| QLoRA | 0.1-1% | 25-30% | 1.5-2.0x |
| IA³ | 0.05-0.5% | 30-50% | 1.5-2.0x |
| AdaLoRA | 0.1-1% | 40-60% | 1.3-1.7x |
| Prefix Tuning | 0.01-0.1% | 20-40% | 2.0-3.0x |
| Prompt Tuning | 0.01-0.1% | 20-40% | 2.0-3.0x |

### Use Case Recommendations

- **LoRA**: General-purpose fine-tuning, good balance of performance and efficiency
- **QLoRA**: Large models on limited hardware, extreme memory efficiency
- **IA³**: Complete weight preservation, very parameter efficient
- **AdaLoRA**: Automatic rank optimization, adaptive training
- **Prefix Tuning**: Task-specific adaptation with minimal parameters
- **Prompt Tuning**: Zero-shot to few-shot adaptation

## Training Tips

### Method Selection

1. **Start with LoRA** for general-purpose fine-tuning
2. **Use QLoRA** if you have memory constraints
3. **Try IA³** if you want maximum parameter efficiency
4. **Use AdaLoRA** for automatic rank optimization
5. **Choose Prefix/Prompt** for task-specific adaptation

### Hyperparameter Tuning

#### LoRA/QLoRA
- **Rank (r)**: Start with 4-8, increase for complex tasks
- **Alpha**: Set to 16-32 times the rank
- **Dropout**: 0.1 for regularization

#### IA³
- **Target Modules**: Usually attention and feedforward layers
- **Feedforward Modules**: Usually intermediate layers

#### AdaLoRA
- **Target R**: Target rank (8-16)
- **Init R**: Initial rank (12-24)
- **Tinit**: Warmup steps (50-200)

#### Prefix Tuning
- **Virtual Tokens**: 10-100 tokens
- **Projection**: Use for large models

#### Prompt Tuning
- **Virtual Tokens**: 10-50 tokens
- **Init**: "TEXT" for meaningful prompts

## Advanced Features

### Multi-Method Comparison

```python
# Compare different PEFT methods
methods = ["lora", "ia3", "adalora", "prefix", "prompt"]

for method in methods:
    config = PEFTConfig(
        model_name="microsoft/DialoGPT-small",
        peft_method=method,
        # Other settings...
    )
    
    trainer = PEFTFineTuner(config)
    trainer.train(train_texts)
    # Evaluate and compare results
```

### Model Merging

```python
# Merge PEFT model with base model
trainer.merge_and_save_base_model(
    base_model_path="./base_model",
    merged_model_path="./merged_model"
)
```

### Custom PEFT Configurations

```python
# Custom LoRA configuration
lora_config = LoraConfig(
    r=16,
    lora_alpha=64,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

# Apply custom config
trainer.model = get_peft_model(trainer.model, lora_config)
```

## Performance Optimization

### Memory Optimization
- Use gradient checkpointing
- Enable mixed precision training
- Use gradient accumulation
- Choose appropriate batch size

### Speed Optimization
- Use larger batch sizes when possible
- Enable gradient accumulation
- Use mixed precision training
- Optimize data loading

### Quality Optimization
- Use appropriate learning rates
- Implement early stopping
- Use validation sets
- Monitor training metrics

## Troubleshooting

### Common Issues

1. **Out of Memory**
   - Reduce batch size
   - Use smaller PEFT rank
   - Enable gradient checkpointing
   - Try different PEFT method

2. **Poor Performance**
   - Increase training data
   - Adjust PEFT parameters
   - Try different PEFT method
   - Use longer training

3. **Slow Training**
   - Use gradient accumulation
   - Enable mixed precision
   - Optimize data loading
   - Check GPU utilization

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
config = PEFTConfig(
    model_name="microsoft/DialoGPT-medium",
    peft_method="lora",
    lora_r=8,
    # Training data: conversation pairs
)

trainer = PEFTFineTuner(config)
trainer.train(conversation_data)
```

### Code Generation
```python
# Fine-tune for code generation
config = PEFTConfig(
    model_name="bigcode/starcoder",
    peft_method="ia3",
    # Training data: code snippets
)

trainer = PEFTFineTuner(config)
trainer.train(code_data)
```

### Instruction Following
```python
# Fine-tune for instruction following
config = PEFTConfig(
    model_name="meta-llama/Llama-2-7b-chat-hf",
    peft_method="adalora",
    # Training data: instruction-response pairs
)

trainer = PEFTFineTuner(config)
trainer.train(instruction_data)
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

- [PEFT Documentation](https://huggingface.co/docs/peft/index)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
- [IA³ Paper](https://arxiv.org/abs/2106.05945)
- [AdaLoRA Paper](https://arxiv.org/abs/2303.10512)
- [Prefix Tuning Paper](https://arxiv.org/abs/2101.00190)
- [Prompt Tuning Paper](https://arxiv.org/abs/2104.08691)
- [Transformers Documentation](https://huggingface.co/docs/transformers/index)