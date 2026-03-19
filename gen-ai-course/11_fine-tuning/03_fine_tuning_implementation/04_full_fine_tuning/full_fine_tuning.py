#!/usr/bin/env python3
"""
Full Fine-Tuning Implementation

This module provides a comprehensive implementation of full fine-tuning for
large language models. Full fine-tuning updates all model parameters and
typically achieves the best performance but requires more computational resources.

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
from torch.cuda.amp import autocast, GradScaler


@dataclass
class FullFineTuningConfig:
    """Configuration for full fine-tuning."""
    
    # Model configuration
    model_name: str = "microsoft/DialoGPT-medium"
    tokenizer_name: Optional[str] = None
    
    # Training configuration
    learning_rate: float = 2e-5
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
    use_gradient_checkpointing: bool = True
    use_mixed_precision: bool = True
    
    # Logging and saving
    save_steps: int = 500
    eval_steps: int = 250
    logging_steps: int = 100
    output_dir: str = "./full_fine_tuning_output"
    
    # Device configuration
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Advanced settings
    early_stopping_patience: int = 3
    early_stopping_metric: str = "eval_loss"
    save_total_limit: int = 3


class FullFineTuningDataset(Dataset):
    """Dataset class for full fine-tuning."""
    
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


class FullFineTuner:
    """Main class for full fine-tuning."""
    
    def __init__(self, config: FullFineTuningConfig):
        """
        Initialize the full fine-tuner.
        
        Args:
            config: Full fine-tuning configuration
        """
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize model and tokenizer
        self.tokenizer = self._load_tokenizer()
        self.model = self._load_model()
        
        # Setup training components
        self.optimizer = None
        self.scheduler = None
        self.train_dataloader = None
        self.eval_dataloader = None
        self.scaler = None
        
        # Training state
        self.best_metric = float('inf') if self.config.early_stopping_metric == 'eval_loss' else 0
        self.patience_counter = 0
        
        self.logger.info(f"Full fine-tuner initialized with {self.config.model_name}")
    
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
        model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            torch_dtype=torch.float16 if self.config.use_mixed_precision else torch.float32,
            device_map="auto" if self.config.device == "cuda" else None
        )
        
        # Enable gradient checkpointing for memory efficiency
        if self.config.use_gradient_checkpointing:
            model.gradient_checkpointing_enable()
        
        # Enable mixed precision training
        if self.config.use_mixed_precision:
            model = model.half()
        
        return model
    
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
        train_dataset = FullFineTuningDataset(
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
            eval_dataset = FullFineTuningDataset(
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
        
        # Setup mixed precision scaler
        if self.config.use_mixed_precision:
            self.scaler = GradScaler()
        
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
            
            # Forward pass with mixed precision
            with autocast(enabled=self.config.use_mixed_precision):
                outputs = self.model(**batch)
                loss = outputs.loss
                
                # Scale loss for gradient accumulation
                loss = loss / self.config.gradient_accumulation_steps
            
            # Backward pass
            if self.config.use_mixed_precision:
                self.scaler.scale(loss).backward()
            else:
                loss.backward()
            
            total_loss += loss.item()
            
            # Update weights
            if (step + 1) % self.config.gradient_accumulation_steps == 0:
                if self.config.use_mixed_precision:
                    # Clip gradients
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), 
                        self.config.max_grad_norm
                    )
                    
                    # Update weights
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                else:
                    # Clip gradients
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), 
                        self.config.max_grad_norm
                    )
                    
                    # Update weights
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
                
                # Forward pass with mixed precision
                with autocast(enabled=self.config.use_mixed_precision):
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
    
    def check_early_stopping(self, metrics: Dict[str, float]) -> bool:
        """
        Check if early stopping criteria are met.
        
        Args:
            metrics: Evaluation metrics
            
        Returns:
            True if early stopping criteria are met
        """
        current_metric = metrics[self.config.early_stopping_metric]
        
        if self.config.early_stopping_metric == 'eval_loss':
            if current_metric < self.best_metric:
                self.best_metric = current_metric
                self.patience_counter = 0
                return False
            else:
                self.patience_counter += 1
        else:
            if current_metric > self.best_metric:
                self.best_metric = current_metric
                self.patience_counter = 0
                return False
            else:
                self.patience_counter += 1
        
        if self.patience_counter >= self.config.early_stopping_patience:
            self.logger.info(f"Early stopping triggered after {self.patience_counter} epochs without improvement")
            return True
        
        return False
    
    def save_checkpoint(self, name: str, epoch: int, metrics: Dict[str, float]):
        """
        Save a checkpoint.
        
        Args:
            name: Name for the checkpoint
            epoch: Current epoch
            metrics: Current metrics
        """
        checkpoint_path = os.path.join(self.config.output_dir, name)
        
        # Save model and optimizer state
        torch.save({
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'best_metric': self.best_metric,
            'patience_counter': self.patience_counter,
            'config': self.config.__dict__,
            'metrics': metrics
        }, checkpoint_path)
        
        self.logger.info(f"Checkpoint saved to {checkpoint_path}")
    
    def cleanup_old_checkpoints(self):
        """Remove old checkpoints to save disk space."""
        import glob
        
        checkpoint_files = glob.glob(os.path.join(self.config.output_dir, "checkpoint_epoch_*.pt"))
        checkpoint_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Keep only the most recent checkpoints
        if len(checkpoint_files) > self.config.save_total_limit:
            for old_checkpoint in checkpoint_files[self.config.save_total_limit:]:
                os.remove(old_checkpoint)
                self.logger.info(f"Removed old checkpoint: {old_checkpoint}")
    
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
                project="full-fine-tuning",
                config=self.config.__dict__
            )
        
        # Training loop
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
                
                # Check early stopping
                if self.check_early_stopping(eval_metrics):
                    self.logger.info("Training stopped due to early stopping criteria")
                    break
                
                # Save best model
                if eval_metrics[self.config.early_stopping_metric] < self.best_metric:
                    self.save_checkpoint("best_model.pt", epoch, eval_metrics)
                
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
                self.save_checkpoint(f"checkpoint_epoch_{epoch + 1}.pt", epoch, eval_metrics if self.eval_dataloader else train_metrics)
                self.cleanup_old_checkpoints()
    
    def save_model(self, name: str):
        """
        Save the final model.
        
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
        
        # Generate with mixed precision
        with autocast(enabled=self.config.use_mixed_precision):
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
    """Main function to demonstrate full fine-tuning."""
    
    # Create output directory
    os.makedirs("./full_fine_tuning_output", exist_ok=True)
    
    # Setup configuration
    config = FullFineTuningConfig(
        model_name="microsoft/DialoGPT-small",
        learning_rate=2e-5,
        batch_size=2,
        num_epochs=2,  # Reduced for demo
        max_length=128,
        output_dir="./full_fine_tuning_output"
    )
    
    # Load sample data
    print("Loading sample data...")
    train_texts = load_sample_data()
    
    # Initialize and train
    print("Initializing full fine-tuner...")
    trainer = FullFineTuner(config)
    
    print("Starting training...")
    trainer.train(train_texts)
    
    # Test generation
    print("\nTesting generation...")
    prompt = "Hello, how are you today?"
    generated = trainer.generate_text(prompt, max_length=50)
    print(f"Prompt: {prompt}")
    print(f"Generated: {generated}")
    
    print("\nTraining complete! Model saved to ./full_fine_tuning_output")


if __name__ == "__main__":
    main()