#!/usr/bin/env python3
"""
PEFT (Parameter-Efficient Fine-Tuning) Implementation

This module provides a comprehensive implementation of various PEFT methods
for fine-tuning large language models. PEFT includes LoRA, QLoRA, IA³, and
other parameter-efficient techniques.

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
    BitsAndBytesConfig
)
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
import logging
from dataclasses import dataclass
import json
import os
from tqdm import tqdm
import wandb
from peft import (
    LoraConfig, 
    IA3Config, 
    AdaLoraConfig,
    PrefixTuningConfig,
    PromptTuningConfig,
    get_peft_model, 
    TaskType, 
    prepare_model_for_kbit_training,
    PeftModel
)


@dataclass
class PEFTConfig:
    """Configuration for PEFT fine-tuning."""
    
    # Model configuration
    model_name: str = "microsoft/DialoGPT-medium"
    tokenizer_name: Optional[str] = None
    
    # PEFT method configuration
    peft_method: str = "lora"  # "lora", "qlora", "ia3", "adalora", "prefix", "prompt"
    
    # Quantization configuration (for QLoRA)
    quantization_type: str = "nf4"
    load_in_4bit: bool = False
    load_in_8bit: bool = False
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True
    
    # LoRA configuration
    lora_r: int = 4
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    lora_target_modules: List[str] = None
    
    # IA³ configuration
    ia3_target_modules: List[str] = None
    ia3_feedforward_modules: List[str] = None
    
    # AdaLoRA configuration
    adalora_target_r: int = 8
    adalora_init_r: int = 12
    adalora_tinit: int = 50
    adalora_tfraction: float = 1.0
    adalora_dss_target_rank: int = 3
    
    # Prefix tuning configuration
    num_virtual_tokens: int = 10
    prefix_projection: bool = False
    
    # Prompt tuning configuration
    prompt_tuning_init: str = "TEXT"  # "TEXT" or "RANDOM"
    prompt_tuning_num_virtual_tokens: int = 10
    
    # Training configuration
    learning_rate: float = 2e-4
    batch_size: int = 4
    num_epochs: int = 3
    warmup_steps: int = 100
    weight_decay: float = 0.01
    
    # Data configuration
    max_length: int = 512
    train_split: float = 0.8
    
    # Optimization configuration
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    
    # Logging and saving
    save_steps: int = 500
    eval_steps: int = 250
    logging_steps: int = 100
    output_dir: str = "./peft_output"
    
    # Device configuration
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    def __post_init__(self):
        if self.lora_target_modules is None:
            # Default target modules for common models
            if "gpt" in self.model_name.lower():
                self.lora_target_modules = ["c_attn", "c_proj"]
            elif "llama" in self.model_name.lower():
                self.lora_target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]
            elif "mistral" in self.model_name.lower():
                self.lora_target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]
            else:
                self.lora_target_modules = ["query", "value", "key", "dense"]
        
        if self.ia3_target_modules is None:
            self.ia3_target_modules = self.lora_target_modules
        
        if self.ia3_feedforward_modules is None:
            if "gpt" in self.model_name.lower():
                self.ia3_feedforward_modules = ["c_fc", "c_proj"]
            elif "llama" in self.model_name.lower():
                self.ia3_feedforward_modules = ["gate_proj", "up_proj", "down_proj"]
            else:
                self.ia3_feedforward_modules = ["dense"]


class PEFTDataset(Dataset):
    """Dataset class for PEFT fine-tuning."""
    
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


class PEFTFineTuner:
    """Main class for PEFT fine-tuning."""
    
    def __init__(self, config: PEFTConfig):
        """
        Initialize the PEFT fine-tuner.
        
        Args:
            config: PEFT configuration
        """
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize model and tokenizer
        self.tokenizer = self._load_tokenizer()
        self.model = self._load_model()
        
        # Setup PEFT
        self._setup_peft()
        
        # Setup training components
        self.optimizer = None
        self.scheduler = None
        self.train_dataloader = None
        self.eval_dataloader = None
        
        self.logger.info(f"PEFT fine-tuner initialized with {self.config.model_name} using {self.config.peft_method}")
    
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
        if self.config.peft_method in ["qlora"]:
            # Setup quantization config for QLoRA
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=self.config.load_in_4bit,
                load_in_8bit=self.config.load_in_8bit,
                bnb_4bit_quant_type=self.config.bnb_4bit_quant_type,
                bnb_4bit_use_double_quant=self.config.bnb_4bit_use_double_quant,
                bnb_4bit_compute_dtype=getattr(torch, self.config.bnb_4bit_compute_dtype)
            )
            
            model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                quantization_config=bnb_config,
                torch_dtype=torch.float16 if self.config.device == "cuda" else torch.float32,
                device_map="auto" if self.config.device == "cuda" else None,
                trust_remote_code=True
            )
            
            # Prepare model for k-bit training
            model = prepare_model_for_kbit_training(model)
        else:
            # Standard model loading
            model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                torch_dtype=torch.float16 if self.config.device == "cuda" else torch.float32,
                device_map="auto" if self.config.device == "cuda" else None
            )
        
        # Enable gradient checkpointing for memory efficiency
        model.gradient_checkpointing_enable()
        
        return model
    
    def _setup_peft(self):
        """Setup PEFT configuration and apply to model."""
        if self.config.peft_method == "lora":
            peft_config = LoraConfig(
                r=self.config.lora_r,
                lora_alpha=self.config.lora_alpha,
                target_modules=self.config.lora_target_modules,
                lora_dropout=self.config.lora_dropout,
                bias="none",
                task_type=TaskType.CAUSAL_LM
            )
        
        elif self.config.peft_method == "qlora":
            peft_config = LoraConfig(
                r=self.config.lora_r,
                lora_alpha=self.config.lora_alpha,
                target_modules=self.config.lora_target_modules,
                lora_dropout=self.config.lora_dropout,
                bias="none",
                task_type=TaskType.CAUSAL_LM
            )
        
        elif self.config.peft_method == "ia3":
            peft_config = IA3Config(
                target_modules=self.config.ia3_target_modules,
                feedforward_modules=self.config.ia3_feedforward_modules,
                task_type=TaskType.CAUSAL_LM
            )
        
        elif self.config.peft_method == "adalora":
            peft_config = AdaLoraConfig(
                target_r=self.config.adalora_target_r,
                init_r=self.config.adalora_init_r,
                tinit=self.config.adalora_tinit,
                tfraction=self.config.adalora_tfraction,
                dss_target_rank=self.config.adalora_dss_target_rank,
                target_modules=self.config.lora_target_modules,
                task_type=TaskType.CAUSAL_LM
            )
        
        elif self.config.peft_method == "prefix":
            peft_config = PrefixTuningConfig(
                num_virtual_tokens=self.config.num_virtual_tokens,
                prefix_projection=self.config.prefix_projection,
                task_type=TaskType.CAUSAL_LM
            )
        
        elif self.config.peft_method == "prompt":
            peft_config = PromptTuningConfig(
                num_virtual_tokens=self.config.prompt_tuning_num_virtual_tokens,
                prompt_tuning_init=self.config.prompt_tuning_init,
                task_type=TaskType.CAUSAL_LM
            )
        
        else:
            raise ValueError(f"Unsupported PEFT method: {self.config.peft_method}")
        
        self.model = get_peft_model(self.model, peft_config)
        
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
        train_dataset = PEFTDataset(
            texts=texts,
            tokenizer=self.tokenizer,
            max_length=self.config.max_length
        )
        
        if eval_texts is None:
            # Split training data
            train_size = int(len(train_dataset) * self.config.train_split)
            eval_size = len(train_dataset) - train_size
            
            train_dataset, eval_dataset = torch.utils.data.random_split(
                train_dataset, [train_size, eval_size]
            )
        else:
            # Use provided evaluation data
            eval_dataset = PEFTDataset(
                texts=eval_texts,
                tokenizer=self.tokenizer,
                max_length=self.config.max_length
            )
        
        # Create data loaders
        self.train_dataloader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=4,
            pin_memory=True
        )
        
        self.eval_dataloader = DataLoader(
            eval_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=4,
            pin_memory=True
        )
        
        self.logger.info(f"Training samples: {len(train_dataset)}")
        self.logger.info(f"Evaluation samples: {len(eval_dataset)}")
    
    def setup_training(self):
        """Setup optimizer and scheduler."""
        # Setup optimizer
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )
        
        # Setup scheduler
        total_steps = len(self.train_dataloader) * self.config.num_epochs
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=self.config.warmup_steps,
            num_training_steps=total_steps
        )
        
        self.logger.info("Training setup complete")
    
    def train_epoch(self, epoch: int) -> Dict[str, float]:
        """
        Train for one epoch.
        
        Args:
            epoch: Current epoch number
            
        Returns:
            Dictionary containing training metrics
        """
        self.model.train()
        total_loss = 0
        progress_bar = tqdm(self.train_dataloader, desc=f"Epoch {epoch + 1}")
        
        for step, batch in enumerate(progress_bar):
            # Move batch to device
            batch = {k: v.to(self.config.device) for k, v in batch.items()}
            
            # Forward pass
            outputs = self.model(**batch)
            loss = outputs.loss
            
            # Scale loss for gradient accumulation
            loss = loss / self.config.gradient_accumulation_steps
            
            # Backward pass
            loss.backward()
            
            total_loss += loss.item()
            
            # Update weights
            if (step + 1) % self.config.gradient_accumulation_steps == 0:
                # Clip gradients
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), 
                    self.config.max_grad_norm
                )
                
                self.optimizer.step()
                self.scheduler.step()
                self.optimizer.zero_grad()
                
                # Logging
                if step % self.config.logging_steps == 0:
                    avg_loss = total_loss / (step + 1)
                    self.logger.info(f"Step {step}, Loss: {avg_loss:.4f}")
        
        avg_loss = total_loss / len(self.train_dataloader)
        return {"train_loss": avg_loss}
    
    def evaluate(self) -> Dict[str, float]:
        """
        Evaluate the model.
        
        Returns:
            Dictionary containing evaluation metrics
        """
        self.model.eval()
        total_loss = 0
        total_samples = 0
        
        with torch.no_grad():
            for batch in tqdm(self.eval_dataloader, desc="Evaluating"):
                batch = {k: v.to(self.config.device) for k, v in batch.items()}
                
                outputs = self.model(**batch)
                loss = outputs.loss
                
                total_loss += loss.item() * batch['input_ids'].size(0)
                total_samples += batch['input_ids'].size(0)
        
        avg_loss = total_loss / total_samples
        perplexity = torch.exp(torch.tensor(avg_loss)).item()
        
        return {
            "eval_loss": avg_loss,
            "perplexity": perplexity
        }
    
    def train(self, texts: List[str], eval_texts: Optional[List[str]] = None):
        """
        Main training loop.
        
        Args:
            texts: Training texts
            eval_texts: Evaluation texts
        """
        # Prepare data
        self.prepare_data(texts, eval_texts)
        
        # Setup training
        self.setup_training()
        
        # Initialize wandb if configured
        if os.getenv("WANDB_API_KEY"):
            wandb.init(
                project="peft-fine-tuning",
                config=self.config.__dict__
            )
        
        # Training loop
        best_eval_loss = float('inf')
        
        for epoch in range(self.config.num_epochs):
            self.logger.info(f"Starting epoch {epoch + 1}/{self.config.num_epochs}")
            
            # Train
            train_metrics = self.train_epoch(epoch)
            
            # Evaluate
            if self.eval_dataloader:
                eval_metrics = self.evaluate()
                self.logger.info(f"Epoch {epoch + 1} - Train Loss: {train_metrics['train_loss']:.4f}, "
                               f"Eval Loss: {eval_metrics['eval_loss']:.4f}, "
                               f"Perplexity: {eval_metrics['perplexity']:.4f}")
                
                # Save best model
                if eval_metrics['eval_loss'] < best_eval_loss:
                    best_eval_loss = eval_metrics['eval_loss']
                    self.save_model("best_model")
                
                # Log to wandb
                if os.getenv("WANDB_API_KEY"):
                    wandb.log({
                        "epoch": epoch + 1,
                        **train_metrics,
                        **eval_metrics
                    })
            else:
                self.logger.info(f"Epoch {epoch + 1} - Train Loss: {train_metrics['train_loss']:.4f}")
                
                # Log to wandb
                if os.getenv("WANDB_API_KEY"):
                    wandb.log({
                        "epoch": epoch + 1,
                        **train_metrics
                    })
            
            # Save checkpoint
            if (epoch + 1) % self.config.save_steps == 0:
                self.save_model(f"checkpoint_epoch_{epoch + 1}")
    
    def save_model(self, name: str):
        """
        Save the model.
        
        Args:
            name: Name for the saved model
        """
        save_path = os.path.join(self.config.output_dir, name)
        self.model.save_pretrained(save_path)
        self.tokenizer.save_pretrained(save_path)
        
        # Save config
        config_path = os.path.join(save_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(self.config.__dict__, f, indent=2)
        
        self.logger.info(f"Model saved to {save_path}")
    
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
    
    def merge_and_save_base_model(self, base_model_path: str, merged_model_path: str):
        """
        Merge the PEFT model with the base model and save.
        
        Args:
            base_model_path: Path to the base model
            merged_model_path: Path to save the merged model
        """
        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            torch_dtype=torch.float16 if self.config.device == "cuda" else torch.float32,
            device_map="auto" if self.config.device == "cuda" else None
        )
        
        # Merge with PEFT model
        merged_model = PeftModel.from_pretrained(base_model, self.config.output_dir)
        merged_model = merged_model.merge_and_unload()
        
        # Save merged model
        merged_model.save_pretrained(merged_model_path)
        self.tokenizer.save_pretrained(merged_model_path)
        
        self.logger.info(f"Merged model saved to {merged_model_path}")


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
    """Main function to demonstrate PEFT fine-tuning."""
    
    # Create output directory
    os.makedirs("./peft_output", exist_ok=True)
    
    # Setup configuration for different PEFT methods
    methods = ["lora", "ia3", "adalora"]
    
    for method in methods:
        print(f"\n=== Training with {method.upper()} ===")
        
        # Setup configuration
        config = PEFTConfig(
            model_name="microsoft/DialoGPT-small",
            peft_method=method,
            lora_r=8 if method == "lora" else 4,
            learning_rate=2e-4,
            batch_size=2,
            num_epochs=1,  # Reduced for demo
            max_length=128,
            output_dir=f"./peft_output_{method}"
        )
        
        # Load sample data
        print("Loading sample data...")
        train_texts = load_sample_data()
        
        # Initialize and train
        print(f"Initializing {method.upper()} fine-tuner...")
        trainer = PEFTFineTuner(config)
        
        print("Starting training...")
        trainer.train(train_texts)
        
        # Test generation
        print("\nTesting generation...")
        prompt = "Hello, how are you today?"
        generated = trainer.generate_text(prompt, max_length=50)
        print(f"Prompt: {prompt}")
        print(f"Generated: {generated}")
        
        print(f"\n{method.upper()} training complete!")


if __name__ == "__main__":
    main()