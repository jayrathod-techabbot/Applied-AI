#!/usr/bin/env python3
"""
Unsloth Fine-Tuning Implementation

This module provides a comprehensive implementation of fine-tuning using Unsloth,
a library that optimizes LoRA training for extreme speed and memory efficiency.

Author: Applied AI Course
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    get_linear_schedule_with_warmup
)
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from dataclasses import dataclass
import json
import os
from tqdm import tqdm
import wandb
from peft import LoraConfig, get_peft_model, TaskType

# Unsloth imports
try:
    from unsloth import FastLanguageModel
    UNSLOTH_AVAILABLE = True
except ImportError:
    UNSLOTH_AVAILABLE = False
    print("Warning: Unsloth not available. Install with: pip install unsloth")


@dataclass
class UnslothConfig:
    """Configuration for Unsloth fine-tuning."""
    
    # Model configuration
    model_name: str = "microsoft/DialoGPT-small"
    tokenizer_name: Optional[str] = None
    
    # Unsloth configuration
    max_seq_length: int = 2048
    dtype: Optional[str] = None  # None for auto-detection
    load_in_4bit: bool = True
    
    # LoRA configuration
    r: int = 16  # Higher rank for better performance
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: List[str] = None
    
    # Training configuration
    learning_rate: float = 2e-4
    batch_size: int = 4
    num_epochs: int = 3
    warmup_steps: int = 10
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
    output_dir: str = "./unsloth_output"
    
    # Device configuration
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    def __post_init__(self):
        if not UNSLOTH_AVAILABLE:
            raise ImportError("Unsloth is not available. Please install it with: pip install unsloth")
        
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


class UnslothDataset(Dataset):
    """Dataset class for Unsloth fine-tuning."""
    
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


class UnslothFineTuner:
    """Main class for Unsloth fine-tuning."""
    
    def __init__(self, config: UnslothConfig):
        """
        Initialize the Unsloth fine-tuner.
        
        Args:
            config: Unsloth configuration
        """
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize model and tokenizer
        self.model = None
        self.tokenizer = None
        
        # Setup training components
        self.optimizer = None
        self.scheduler = None
        self.train_dataloader = None
        self.eval_dataloader = None
        
        self.logger.info(f"Unsloth fine-tuner initialized with {self.config.model_name}")
    
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
    
    def load_model(self):
        """Load the model using Unsloth."""
        if not UNSLOTH_AVAILABLE:
            raise ImportError("Unsloth is not available")
        
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.config.model_name,
            max_seq_length=self.config.max_seq_length,
            dtype=self.config.dtype,
            load_in_4bit=self.config.load_in_4bit,
        )
        
        # Add LoRA adapters
        self.model = FastLanguageModel.get_peft_model(
            self.model,
            r=self.config.r,
            target_modules=self.config.target_modules,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            use_gradient_checkpointing="unsloth",  # Use Unsloth's gradient checkpointing
            random_state=3407,
            use_rslora=False,  # We use regular LoRA
        )
        
        self.logger.info("Model loaded with Unsloth optimizations")
    
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
        train_dataset = UnslothDataset(
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
            eval_dataset = UnslothDataset(
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
        # Setup optimizer with Unsloth's optimized AdamW
        self.optimizer = FastLanguageModel.get_optimizer(
            self.model,
            optimizer_name="adamw_8bit",  # Use 8-bit AdamW for memory efficiency
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )
        
        # Setup scheduler
        total_steps = len(self.train_dataloader) * self.config.num_epochs
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=self.config.warmup_steps,
            num_training_steps=total_steps
        )
        
        self.logger.info("Training setup complete with Unsloth optimizations")
    
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
        # Load model
        self.load_model()
        
        # Prepare data
        self.prepare_data(texts, eval_texts)
        
        # Setup training
        self.setup_training()
        
        # Initialize wandb if configured
        if os.getenv("WANDB_API_KEY"):
            wandb.init(
                project="unsloth-fine-tuning",
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
        
        # Save model with Unsloth's optimized saving
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
        
        # Generate with Unsloth optimizations
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
    
    def benchmark_training(self, texts: List[str]) -> Dict[str, float]:
        """
        Benchmark training speed and memory usage.
        
        Args:
            texts: Training texts
            
        Returns:
            Benchmark results
        """
        import time
        import psutil
        from GPUtil import getGPUs
        
        # Prepare data
        self.prepare_data(texts)
        self.setup_training()
        
        # Benchmark
        start_time = time.time()
        initial_memory = torch.cuda.memory_allocated() if torch.cuda.is_available() else 0
        
        # Train for one batch
        batch = next(iter(self.train_dataloader))
        batch = {k: v.to(self.config.device) for k, v in batch.items()}
        
        # Forward pass
        outputs = self.model(**batch)
        loss = outputs.loss
        loss.backward()
        
        # Backward pass
        self.optimizer.step()
        self.optimizer.zero_grad()
        
        # Calculate metrics
        end_time = time.time()
        final_memory = torch.cuda.memory_allocated() if torch.cuda.is_available() else 0
        
        # Get GPU utilization
        gpus = getGPUs()
        gpu_utilization = gpus[0].load if gpus else 0
        
        return {
            "time_per_batch": end_time - start_time,
            "memory_usage_mb": (final_memory - initial_memory) / 1024 / 1024,
            "gpu_utilization": gpu_utilization * 100,
            "peak_memory_mb": torch.cuda.max_memory_allocated() / 1024 / 1024 if torch.cuda.is_available() else 0
        }


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
    """Main function to demonstrate Unsloth fine-tuning."""
    
    # Create output directory
    os.makedirs("./unsloth_output", exist_ok=True)
    
    # Setup configuration
    config = UnslothConfig(
        model_name="microsoft/DialoGPT-small",
        max_seq_length=1024,
        r=16,  # Higher rank for better performance
        lora_alpha=16,
        learning_rate=2e-4,
        batch_size=4,
        num_epochs=2,  # Reduced for demo
        max_length=512,
        output_dir="./unsloth_output"
    )
    
    # Load sample data
    print("Loading sample data...")
    train_texts = load_sample_data()
    
    # Initialize and train
    print("Initializing Unsloth fine-tuner...")
    trainer = UnslothFineTuner(config)
    
    print("Starting training...")
    trainer.train(train_texts)
    
    # Test generation
    print("\nTesting generation...")
    prompt = "Hello, how are you today?"
    generated = trainer.generate_text(prompt, max_length=50)
    print(f"Prompt: {prompt}")
    print(f"Generated: {generated}")
    
    # Benchmark
    print("\nBenchmarking...")
    benchmark_results = trainer.benchmark_training(train_texts[:100])
    print(f"Training speed: {benchmark_results['time_per_batch']:.4f}s per batch")
    print(f"Memory usage: {benchmark_results['memory_usage_mb']:.2f}MB")
    print(f"GPU utilization: {benchmark_results['gpu_utilization']:.2f}%")
    
    print("\nTraining complete! Model saved to ./unsloth_output")


if __name__ == "__main__":
    main()