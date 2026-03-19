# HuggingFace MLOps Fine-Tuning Implementation

This directory contains a comprehensive implementation of fine-tuning using HuggingFace's MLOps tools, including Hub integration, model versioning, experiment tracking, and deployment capabilities.

## Overview

HuggingFace MLOps provides a complete ecosystem for machine learning operations, including model hosting, experiment tracking, dataset management, and deployment. This implementation demonstrates how to leverage these tools for efficient fine-tuning workflows.

## Key Features

- **Hub Integration**: Seamless model and dataset versioning on HuggingFace Hub
- **Experiment Tracking**: Integration with Wandb for comprehensive experiment tracking
- **Model Versioning**: Automatic model versioning and artifact management
- **Collaboration**: Team collaboration features with private repositories
- **Deployment Ready**: Models ready for deployment on HuggingFace Spaces
- **Production Features**: Advanced training features with Trainer API

## Architecture

```
HuggingFace MLOps Pipeline:
1. Load Model from Hub
2. Prepare Data (Local or from Hub)
3. Configure Trainer with MLOps Features
4. Train with Experiment Tracking
5. Evaluate and Push to Hub
6. Create Model Card and Documentation
7. Deploy to Spaces (Optional)
```

## Files

- `hf_mlops_fine_tuning.py` - Main implementation with complete MLOps pipeline
- `requirements.txt` - Dependencies for HuggingFace MLOps
- `README.md` - This documentation file

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from hf_mlops_fine_tuning import HFMLOpsFineTuner, HFMLOpsConfig

# Setup configuration
config = HFMLOpsConfig(
    model_name="microsoft/DialoGPT-small",
    use_peft=True,
    peft_method="lora",
    r=8,
    learning_rate=2e-4,
    batch_size=4,
    num_epochs=3,
    hub_model_id="your-username/your-model-name",
    hub_token="your-hf-token",
    push_to_hub=True,
    log_to_wandb=True
)

# Initialize trainer
trainer = HFMLOpsFineTuner(config)

# Prepare data
train_texts = ["Your training data here..."]
trainer.prepare_data(train_texts)

# Train model
train_result = trainer.train(train_texts)

# Evaluate model
metrics = trainer.evaluate()

# Generate text
prompt = "Hello, how are you?"
generated = trainer.generate_text(prompt)
print(generated)
```

### Advanced Configuration

```python
config = HFMLOpsConfig(
    # Model settings
    model_name="microsoft/DialoGPT-medium",
    tokenizer_name=None,
    
    # PEFT settings
    use_peft=True,
    peft_method="lora",  # "lora", "qlora", "ia3"
    r=8,
    lora_alpha=16,
    lora_dropout=0.1,
    target_modules=None,
    
    # Quantization settings (for QLoRA)
    quantization_type="nf4",
    load_in_4bit=False,
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
    dataset_name=None,  # HuggingFace dataset name
    
    # HuggingFace Hub settings
    hub_model_id="your-username/your-model-name",
    hub_token="your-hf-token",
    hub_private_repo=False,
    push_to_hub=True,
    
    # Experiment tracking
    wandb_project="hf-mlops-fine-tuning",
    log_to_wandb=True,
    
    # Advanced training settings
    gradient_accumulation_steps=1,
    max_grad_norm=1.0,
    use_gradient_checkpointing=True,
    use_mixed_precision=True,
    
    # Logging and saving
    save_steps=500,
    eval_steps=250,
    logging_steps=100,
    output_dir="./hf_mlops_output",
    
    # Device settings
    device="cuda" if torch.cuda.is_available() else "cpu"
)
```

## HuggingFace Hub Integration

### Authentication

```python
# Set your HuggingFace token
import os
os.environ["HF_TOKEN"] = "your-hf-token"

# Or login programmatically
from huggingface_hub import login
login("your-hf-token")
```

### Pushing Models to Hub

```python
# Automatic push during training
config = HFMLOpsConfig(
    push_to_hub=True,
    hub_model_id="your-username/your-model-name",
    hub_token="your-hf-token"
)

# Manual push after training
trainer.trainer.push_to_hub()
```

### Loading Models from Hub

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

# Load fine-tuned model
model_name = "your-username/your-model-name"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
```

## Experiment Tracking with Wandb

### Setup

```python
# Set your Wandb API key
import os
os.environ["WANDB_API_KEY"] = "your-wandb-api-key"

# Or login programmatically
import wandb
wandb.login()
```

### Automatic Tracking

```python
config = HFMLOpsConfig(
    log_to_wandb=True,
    wandb_project="hf-mlops-fine-tuning"
)

# Training automatically logs to Wandb
train_result = trainer.train(train_texts)
```

### Custom Metrics

```python
# Add custom metrics to tracking
wandb.log({
    "custom_metric": value,
    "epoch": epoch,
    "learning_rate": lr
})
```

## Model Cards and Documentation

### Automatic Model Card Creation

```python
# Create model card after training
metrics = trainer.evaluate()
trainer.create_model_card(config.hub_model_id, metrics)
```

### Manual Model Card

```python
model_card_content = """
---
license: apache-2.0
tags:
- fine-tuning
- lora
- causal-lm
language:
- en
pipeline_tag: text-generation
---

# Your Model Name

## Model Details
...

## Usage
...

## Training Details
...
"""

# Push to Hub
from huggingface_hub import HfApi
api = HfApi()
api.create_commit(
    repo_id="your-username/your-model-name",
    operations=[{"path_or_fileobj": model_card_content.encode(), "path_in_repo": "README.md"}],
    commit_message="Add model card"
)
```

## Advanced Features

### Dataset Management

```python
# Load dataset from Hub
config = HFMLOpsConfig(
    dataset_name="your-username/your-dataset-name"
)

# Create dataset
from datasets import Dataset
dataset = Dataset.from_dict({"text": ["your", "data"]})
dataset.push_to_hub("your-username/your-dataset-name")
```

### Multi-GPU Training

```python
# Automatic multi-GPU support
config = HFMLOpsConfig(
    # Other settings...
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4
)

# Use Accelerate for advanced multi-GPU setups
from accelerate import Accelerator
accelerator = Accelerator()
```

### Custom Metrics

```python
def compute_custom_metrics(eval_pred):
    predictions, labels = eval_pred
    
    # Your custom metrics computation
    accuracy = compute_accuracy(predictions, labels)
    f1_score = compute_f1_score(predictions, labels)
    
    return {
        "accuracy": accuracy,
        "f1_score": f1_score,
        "perplexity": perplexity
    }

# Use in trainer setup
trainer = Trainer(
    # Other settings...
    compute_metrics=compute_custom_metrics
)
```

## Deployment Options

### HuggingFace Spaces

```python
# Deploy to Spaces
# 1. Create a Space on HuggingFace Hub
# 2. Push your model to Hub
# 3. Use Gradio or Streamlit for UI
# 4. Connect Space to your model

# Example Gradio app
import gradio as gr
from transformers import pipeline

model = pipeline("text-generation", model="your-username/your-model-name")

def generate_text(prompt):
    return model(prompt)[0]['generated_text']

interface = gr.Interface(
    fn=generate_text,
    inputs="text",
    outputs="text",
    title="Your Model Name"
)

interface.launch()
```

### API Deployment

```python
# FastAPI deployment
from fastapi import FastAPI
from transformers import pipeline

app = FastAPI()
model = pipeline("text-generation", model="your-username/your-model-name")

@app.post("/generate")
def generate(prompt: str):
    return {"generated_text": model(prompt)[0]['generated_text']}
```

## Best Practices

### Model Versioning

1. **Semantic Versioning**: Use semantic versioning for model releases
2. **Changelog**: Maintain a changelog of model improvements
3. **Backward Compatibility**: Ensure backward compatibility when possible

### Experiment Management

1. **Clear Naming**: Use clear, descriptive experiment names
2. **Tags**: Use tags to categorize experiments
3. **Notes**: Add detailed notes to experiments
4. **Comparisons**: Compare experiments systematically

### Data Management

1. **Versioning**: Version your datasets
2. **Documentation**: Document data sources and preprocessing
3. **Privacy**: Ensure data privacy and compliance
4. **Quality**: Maintain data quality standards

### Model Monitoring

1. **Performance Tracking**: Monitor model performance in production
2. **Drift Detection**: Detect data drift and model degradation
3. **Alerts**: Set up alerts for performance issues
4. **Rollback**: Implement rollback mechanisms

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Check HuggingFace token permissions
   - Verify Wandb API key
   - Ensure proper environment variables

2. **Memory Issues**
   - Use gradient checkpointing
   - Enable mixed precision
   - Reduce batch size
   - Use PEFT methods

3. **Training Issues**
   - Monitor loss curves
   - Check learning rate schedules
   - Verify data quality
   - Use appropriate metrics

### Debugging Tips

```python
# Check model parameters
print(f"Trainable parameters: {trainer.model.num_parameters()}")

# Monitor training
import wandb
wandb.watch(trainer.model)

# Debug data
print(f"Training samples: {len(trainer.train_dataset)}")
print(f"Sample: {trainer.train_dataset[0]}")
```

## Examples

### Chatbot Fine-tuning
```python
config = HFMLOpsConfig(
    model_name="microsoft/DialoGPT-medium",
    use_peft=True,
    peft_method="lora",
    hub_model_id="your-username/chatbot-model",
    # Other settings...
)

trainer = HFMLOpsFineTuner(config)
trainer.train(conversation_data)
trainer.trainer.push_to_hub()
```

### Code Generation
```python
config = HFMLOpsConfig(
    model_name="bigcode/starcoder",
    use_peft=True,
    peft_method="qlora",
    load_in_4bit=True,
    hub_model_id="your-username/code-model",
    # Other settings...
)

trainer = HFMLOpsFineTuner(config)
trainer.train(code_data)
trainer.trainer.push_to_hub()
```

### Instruction Following
```python
config = HFMLOpsConfig(
    model_name="meta-llama/Llama-2-7b-chat-hf",
    use_peft=True,
    peft_method="ia3",
    hub_model_id="your-username/instruction-model",
    # Other settings...
)

trainer = HFMLOpsFineTuner(config)
trainer.train(instruction_data)
trainer.trainer.push_to_hub()
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

- [HuggingFace Hub Documentation](https://huggingface.co/docs/hub/index)
- [Transformers Trainer Documentation](https://huggingface.co/docs/transformers/main/en/main_classes/trainer)
- [PEFT Documentation](https://huggingface.co/docs/peft/index)
- [Wandb Documentation](https://docs.wandb.ai/)
- [Datasets Documentation](https://huggingface.co/docs/datasets/index)
- [Spaces Documentation](https://huggingface.co/docs/hub/spaces)