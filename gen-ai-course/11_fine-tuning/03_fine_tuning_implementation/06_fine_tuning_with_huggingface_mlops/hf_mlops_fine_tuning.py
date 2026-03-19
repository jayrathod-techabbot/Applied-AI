#!/usr/bin/env python3
"""
HuggingFace MLOps Fine-Tuning Implementation

This module provides a comprehensive implementation of fine-tuning using HuggingFace's
MLOps tools including Hub integration, model versioning, experiment tracking, and
deployment capabilities.

Author: Applied AI Course
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    get_linear_schedule_with_warmup,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling
)
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from dataclasses import dataclass
import json
import os
from tqdm import tqdm
import wandb
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from huggingface_hub import HfApi, login
import evaluate
from datasets import Dataset as HFDataset, load_dataset, concatenate_datasets


@dataclass
class HFMLOpsConfig:
    """Configuration for HuggingFace MLOps fine-tuning."""
    
    # Model configuration
    model_name: str = "microsoft/DialoGPT-small"
    tokenizer_name: Optional[str] = None
    
    # PEFT configuration
    use_peft: bool = True
    peft_method: str = "lora"  # "lora", "qlora", "ia3"
    r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: List[str] = None
    
    # Quantization configuration (for QLoRA)
    quantization_type: str = "nf4"
    load_in_4bit: bool = False
    load_in_8bit: bool = False
    
    # Training configuration
    learning_rate: float = 2e-4
    batch_size: int = 4
    num_epochs: int = 3
    warmup_steps: int = 100
    weight_decay: float = 0.01
    
    # Data configuration
    max_length: int = 512
    train_split: float = 0.8
    dataset_name: Optional[str] = None  # HuggingFace dataset name
    
    # HuggingFace Hub configuration
    hub_model_id: Optional[str] = None
    hub_token: Optional[str] = None
    hub_private_repo: bool = False
    push_to_hub: bool = True
    
    # Experiment tracking
    wandb_project: str = "hf-mlops-fine-tuning"
    log_to_wandb: bool = True
    
    # Advanced training settings
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    use_gradient_checkpointing: bool = True
    use_mixed_precision: bool = True
    
    # Logging and saving
    save_steps: int = 500
    eval_steps: int = 250
    logging_steps: int = 100
    output_dir: str = "./hf_mlops_output"
    
    # Device configuration
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    def __post_init__(self):
        if self.target_modules is None:
            # Default target modules for common models
            if "gpt" in self.model_name.lower():
                self.target_modules = ["c_attn", "c_proj"]
            elif "llama" in self.model_name.lower():
                self.target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]
            elif "mistral" in self.model_name.lower():
                self.target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]
            else:
                self.target_modules = ["query", "value", "key", "dense"]


class HFMLOpsDataset(Dataset):
    """Dataset class for HuggingFace MLOps fine-tuning."""
    
    def __init__(
        self, 
        texts: List[str], 
        tokenizer: AutoTokenizer, 
        max_length: int = 512
    ):
        """
        Initialize the dataset.
        
        Args:
            texts: List of text samples
            tokenizer: Pretrained tokenizer
            max_length: Maximum sequence length
        """
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        
        # Tokenize the text
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].squeeze()
        attention_mask = encoding['attention_mask'].squeeze()
        
        # For causal language modeling, labels are the same as input_ids
        labels = input_ids.clone()
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'labels': labels
        }


class HFMLOpsFineTuner:
    """Main class for HuggingFace MLOps fine-tuning."""
    
    def __init__(self, config: HFMLOpsConfig):
        """
        Initialize the HuggingFace MLOps fine-tuner.
        
        Args:
            config: HuggingFace MLOps configuration
        """
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize HuggingFace Hub
        self._setup_hf_hub()
        
        # Initialize model and tokenizer
        self.tokenizer = self._load_tokenizer()
        self.model = self._load_model()
        
        # Setup training components
        self.trainer = None
        self.train_dataset = None
        self.eval_dataset = None
        
        self.logger.info(f"HF MLOps fine-tuner initialized with {self.config.model_name}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(self.config.output_dir, 'training.log')),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def _setup_hf_hub(self):
        """Setup HuggingFace Hub integration."""
        if self.config.hub_token:
            login(self.config.hub_token)
            self.hf_api = HfApi()
        else:
            self.hf_api = None
            self.logger.warning("No HuggingFace Hub token provided. Push to hub will be disabled.")
    
    def _load_tokenizer(self) -> AutoTokenizer:
        """Load the tokenizer."""
        tokenizer_name = self.config.tokenizer_name or self.config.model_name
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        
        # Add padding token if not present
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        return tokenizer
    
    def _load_model(self) -> AutoModelForCausalLM:
        """Load the base model."""
        if self.config.peft_method == "qlora" and self.config.load_in_4bit:
            from transformers import BitsAndBytesConfig
            from peft import prepare_model_for_kbit_training
            
            # Setup quantization config
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=self.config.load_in_4bit,
                load_in_8bit=self.config.load_in_8bit,
                bnb_4bit_quant_type=self.config.quantization_type,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.float16
            )
            
            model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                quantization_config=bnb_config,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            # Prepare model for k-bit training
            model = prepare_model_for_kbit_training(model)
        else:
            model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                torch_dtype=torch.float16 if self.config.use_mixed_precision else torch.float32,
                device_map="auto"
            )
        
        # Enable gradient checkpointing for memory efficiency
        if self.config.use_gradient_checkpointing:
            model.gradient_checkpointing_enable()
        
        # Apply PEFT if enabled
        if self.config.use_peft:
            self._apply_peft(model)
        
        return model
    
    def _apply_peft(self, model: AutoModelForCausalLM):
        """Apply PEFT configuration to the model."""
        if self.config.peft_method == "lora":
            peft_config = LoraConfig(
                r=self.config.r,
                lora_alpha=self.config.lora_alpha,
                target_modules=self.config.target_modules,
                lora_dropout=self.config.lora_dropout,
                bias="none",
                task_type=TaskType.CAUSAL_LM
            )
        elif self.config.peft_method == "ia3":
            from peft import IA3Config
            peft_config = IA3Config(
                target_modules=self.config.target_modules,
                task_type=TaskType.CAUSAL_LM
            )
        else:
            raise ValueError(f"Unsupported PEFT method: {self.config.peft_method}")
        
        self.model = get_peft_model(model, peft_config)
        
        # Print trainable parameters
        self.logger.info("Trainable parameters:")
        self.model.print_trainable_parameters()
    
    def prepare_data(
        self, 
        texts: List[str], 
        eval_texts: Optional[List[str]] = None
    ) -> None:
        """
        Prepare training and evaluation datasets.
        
        Args:
            texts: Training texts
            eval_texts: Evaluation texts (if None, split from training data)
        """
        # Create training dataset
        if self.config.dataset_name:
            # Load from HuggingFace Hub
            dataset = load_dataset(self.config.dataset_name)
            if 'train' in dataset:
                self.train_dataset = dataset['train']
            else:
                self.train_dataset = dataset
        else:
            # Create from local texts
            self.train_dataset = HFDataset.from_dict({
                'text': texts
            })
        
        # Tokenize the dataset
        def tokenize_function(examples):
            return self.tokenizer(
                examples['text'],
                truncation=True,
                padding='max_length',
                max_length=self.config.max_length
            )
        
        self.train_dataset = self.train_dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=['text'] if 'text' in self.train_dataset.column_names else None
        )
        
        # Prepare evaluation dataset
        if eval_texts is None:
            # Split training data
            split_dataset = self.train_dataset.train_test_split(test_size=1-self.config.train_split)
            self.train_dataset = split_dataset['train']
            self.eval_dataset = split_dataset['test']
        else:
            # Use provided evaluation data
            eval_dataset = HFDataset.from_dict({
                'text': eval_texts
            })
            self.eval_dataset = eval_dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=['text'] if 'text' in eval_dataset.column_names else None
            )
        
        # Set format for PyTorch
        self.train_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'labels'])
        self.eval_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'labels'])
        
        self.logger.info(f"Training samples: {len(self.train_dataset)}")
        self.logger.info(f"Evaluation samples: {len(self.eval_dataset)}")
    
    def setup_trainer(self):
        """Setup HuggingFace Trainer with MLOps features."""
        # Setup training arguments
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            learning_rate=self.config.learning_rate,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            num_train_epochs=self.config.num_epochs,
            weight_decay=self.config.weight_decay,
            evaluation_strategy="steps",
            eval_steps=self.config.eval_steps,
            save_steps=self.config.save_steps,
            logging_steps=self.config.logging_steps,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            gradient_checkpointing=self.config.use_gradient_checkpointing,
            fp16=self.config.use_mixed_precision,
            max_grad_norm=self.config.max_grad_norm,
            warmup_steps=self.config.warmup_steps,
            save_total_limit=3,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            dataloader_num_workers=4,
            remove_unused_columns=False,
            push_to_hub=self.config.push_to_hub and self.config.hub_token is not None,
            hub_model_id=self.config.hub_model_id,
            hub_private_repo=self.config.hub_private_repo,
            report_to="wandb" if self.config.log_to_wandb else "none",
        )
        
        # Setup data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # Setup metrics
        def compute_metrics(eval_pred):
            predictions, labels = eval_pred
            
            # Calculate perplexity
            predictions = predictions[0] if isinstance(predictions, tuple) else predictions
            
            # Shift so that tokens < n predict n
            shift_logits = predictions[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            
            # Flatten the tokens
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
            perplexity = torch.exp(loss)
            
            return {"perplexity": perplexity.item(), "eval_loss": loss.item()}
        
        # Initialize trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
            tokenizer=self.tokenizer,
            data_collator=data_collator,
            compute_metrics=compute_metrics,
        )
        
        self.logger.info("Trainer setup complete with MLOps features")
    
    def train(self, texts: List[str], eval_texts: Optional[List[str]] = None):
        """
        Main training loop with MLOps features.
        
        Args:
            texts: Training texts
            eval_texts: Evaluation texts
        """
        # Prepare data
        self.prepare_data(texts, eval_texts)
        
        # Setup trainer
        self.setup_trainer()
        
        # Initialize wandb if configured
        if self.config.log_to_wandb and os.getenv("WANDB_API_KEY"):
            wandb.init(
                project=self.config.wandb_project,
                config=self.config.__dict__
            )
        
        # Train model
        self.logger.info("Starting training with MLOps features...")
        train_result = self.trainer.train()
        
        # Save model
        self.trainer.save_model()
        
        # Push to Hub if configured
        if self.config.push_to_hub and self.config.hub_token:
            self.logger.info("Pushing model to HuggingFace Hub...")
            self.trainer.push_to_hub()
        
        # Log training results
        self.logger.info(f"Training completed. Results: {train_result}")
        
        return train_result
    
    def evaluate(self) -> Dict[str, float]:
        """
        Evaluate the model.
        
        Returns:
            Dictionary containing evaluation metrics
        """
        if self.trainer is None:
            raise ValueError("Trainer not initialized. Call train() first.")
        
        self.logger.info("Evaluating model...")
        eval_result = self.trainer.evaluate()
        
        self.logger.info(f"Evaluation results: {eval_result}")
        return eval_result
    
    def generate_text(self, prompt: str, max_length: int = 100, **kwargs) -> str:
        """
        Generate text using the fine-tuned model.
        
        Args:
            prompt: Input prompt
            max_length: Maximum length of generated text
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        self.model.eval()
        
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.config.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length + len(inputs['input_ids'][0]),
                do_sample=True,
                top_p=0.95,
                temperature=0.7,
                **kwargs
            )
        
        # Decode output
        generated_text = self.tokenizer.decode(
            outputs[0][len(inputs['input_ids'][0]):], 
            skip_special_tokens=True
        )
        
        return generated_text
    
    def create_model_card(self, model_id: str, metrics: Dict[str, float]):
        """
        Create a model card for the fine-tuned model.
        
        Args:
            model_id: Model identifier
            metrics: Evaluation metrics
        """
        if not self.hf_api:
            self.logger.warning("HuggingFace Hub not configured. Skipping model card creation.")
            return
        
        model_card_content = f"""
---
license: apache-2.0
tags:
- fine-tuning
- {self.config.peft_method if self.config.use_peft else 'full-fine-tuning'}
- {self.config.model_name.split('/')[-1]}
- causal-lm
language:
- en
pipeline_tag: text-generation
---

# Fine-tuned Model: {model_id}

This model was fine-tuned using HuggingFace MLOps tools.

## Model Details

- **Base Model**: {self.config.model_name}
- **Fine-tuning Method**: {self.config.peft_method if self.config.use_peft else 'Full Fine-tuning'}
- **Training Data**: Custom dataset
- **Training Configuration**:
  - Learning Rate: {self.config.learning_rate}
  - Batch Size: {self.config.batch_size}
  - Epochs: {self.config.num_epochs}
  - Max Length: {self.config.max_length}

## Evaluation Metrics

- **Perplexity**: {metrics.get('perplexity', 'N/A'):.2f}
- **Evaluation Loss**: {metrics.get('eval_loss', 'N/A'):.4f}

## Usage

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("{model_id}")
model = AutoModelForCausalLM.from_pretrained("{model_id}")

prompt = "Your prompt here"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_length=100)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Training Details

This model was trained using:
- HuggingFace Transformers
- PEFT (Parameter Efficient Fine-Tuning)
- Wandb for experiment tracking
- HuggingFace Hub for model versioning

## License

Apache 2.0
"""
        
        # Create model card
        self.hf_api.create_commit(
            repo_id=model_id,
            operations=[
                {"path_or_fileobj": model_card_content.encode(), "path_in_repo": "README.md"}
            ],
            commit_message="Add model card"
        )
        
        self.logger.info(f"Model card created for {model_id}")
    
    def log_to_hub(self, metrics: Dict[str, float]):
        """
        Log metrics and artifacts to HuggingFace Hub.
        
        Args:
            metrics: Evaluation metrics
        """
        if not self.hf_api:
            return
        
        # Create metrics file
        metrics_content = json.dumps(metrics, indent=2)
        
        # Commit metrics
        self.hf_api.create_commit(
            repo_id=self.config.hub_model_id,
            operations=[
                {"path_or_fileobj": metrics_content.encode(), "path_in_repo": "metrics.json"}
            ],
            commit_message="Add evaluation metrics"
        )
        
        self.logger.info("Metrics logged to HuggingFace Hub")


def load_sample_data() -> List[str]:
    """
    Load sample data for demonstration.
    
    Returns:
        List of sample text samples
    """
    # Sample dialog data
    sample_texts = [
        "Hello, how are you today?",
        "I'm doing well, thank you for asking. How about you?",
        "I'm good too. What have you been up to?",
        "Not much, just working on some projects. How's your day going?",
        "It's been pretty busy, but productive. Thanks for checking in!",
        "You're welcome! Always happy to chat.",
        "What kind of projects are you working on?",
        "I'm learning about machine learning and artificial intelligence.",
        "That sounds fascinating! What specifically interests you about AI?",
        "I'm particularly interested in natural language processing and how models can understand human language.",
        "That's really cool. Do you think AI will change how we communicate?",
        "Absolutely! I think it will make communication more accessible and help break down language barriers.",
        "I agree. Technology has already done so much for global communication.",
        "Definitely. It's exciting to think about what's coming next!",
        "What do you think will be the next big breakthrough in AI?",
        "I think we'll see major advances in understanding context and generating more natural conversations.",
        "That would be amazing. Imagine having conversations that feel completely natural with AI.",
        "Exactly! It could revolutionize customer service, education, and so many other fields.",
        "I can't wait to see what the future holds!",
        "Me neither! The possibilities are endless."
    ]
    
    return sample_texts * 100  # Repeat for more training data


def main():
    """Main function to demonstrate HuggingFace MLOps fine-tuning."""
    
    # Create output directory
    os.makedirs("./hf_mlops_output", exist_ok=True)
    
    # Setup configuration
    config = HFMLOpsConfig(
        model_name="microsoft/DialoGPT-small",
        use_peft=True,
        peft_method="lora",
        r=8,
        learning_rate=2e-4,
        batch_size=4,
        num_epochs=2,  # Reduced for demo
        max_length=128,
        output_dir="./hf_mlops_output",
        hub_model_id="your-username/dialogpt-finetuned",  # Replace with your username
        hub_token=os.getenv("HF_TOKEN"),  # Set your HuggingFace token
        push_to_hub=False,  # Set to True if you have a valid token
        log_to_wandb=True
    )
    
    # Load sample data
    print("Loading sample data...")
    train_texts = load_sample_data()
    
    # Initialize and train
    print("Initializing HuggingFace MLOps fine-tuner...")
    trainer = HFMLOpsFineTuner(config)
    
    print("Starting training...")
    train_result = trainer.train(train_texts)
    
    # Evaluate
    print("\nEvaluating model...")
    metrics = trainer.evaluate()
    
    # Test generation
    print("\nTesting generation...")
    prompt = "Hello, how are you today?"
    generated = trainer.generate_text(prompt, max_length=50)
    print(f"Prompt: {prompt}")
    print(f"Generated: {generated}")
    
    # Create model card if pushing to hub
    if config.push_to_hub and config.hub_token:
        print("\nCreating model card...")
        trainer.create_model_card(config.hub_model_id, metrics)
        trainer.log_to_hub(metrics)
    
    print("\nTraining complete! Model saved to ./hf_mlops_output")


if __name__ == "__main__":
    main()