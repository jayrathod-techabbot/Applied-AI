#!/usr/bin/env python3
"""
AWS MLOps Fine-Tuning Implementation

This module provides a comprehensive implementation of fine-tuning using AWS SageMaker
services, including experiment tracking, model training, deployment, and monitoring.

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
import boto3
import sagemaker
from sagemaker.huggingface import HuggingFace
from sagemaker.pytorch import PyTorch
from sagemaker.tuner import (
    HyperparameterTuner,
    IntegerParameter,
    CategoricalParameter,
    ContinuousParameter
)
from sagemaker.model_metrics import MetricsSource, ModelMetrics
from sagemaker.model import Model
from sagemaker.predictor import Predictor
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer
import mlflow
import mlflow.sagemaker
from botocore.exceptions import ClientError


@dataclass
class AWSMLOpsConfig:
    """Configuration for AWS MLOps fine-tuning."""
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_profile: Optional[str] = None
    sagemaker_role: str = "SageMakerRole"
    
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
    dataset_name: Optional[str] = None
    
    # SageMaker Configuration
    instance_type: str = "ml.g4dn.xlarge"  # GPU instance
    instance_count: int = 1
    volume_size: int = 30  # GB
    max_run_time: int = 3600  # seconds
    
    # S3 Configuration
    s3_bucket: str = None  # Will be auto-generated
    s3_prefix: str = "fine-tuning"
    
    # Experiment configuration
    experiment_name: str = "fine-tuning-experiment"
    trial_name: str = "fine-tuning-trial"
    trial_component_display_name: str = "fine-tuning-component"
    
    # Model registration
    model_package_group_name: str = "fine-tuned-models"
    model_description: str = "Fine-tuned model using AWS SageMaker"
    approval_status: str = "PendingManualApproval"
    
    # Deployment configuration
    endpoint_name: str = "fine-tuned-model-endpoint"
    endpoint_instance_type: str = "ml.m5.large"
    endpoint_initial_instance_count: int = 1
    
    # Advanced training settings
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    use_gradient_checkpointing: bool = True
    use_mixed_precision: bool = True
    
    # Logging and saving
    save_steps: int = 500
    eval_steps: int = 250
    logging_steps: int = 100
    output_dir: str = "./aws_mlops_output"
    
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


class AWSMLOpsDataset(Dataset):
    """Dataset class for AWS MLOps fine-tuning."""
    
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


class AWSMLOpsFineTuner:
    """Main class for AWS MLOps fine-tuning."""
    
    def __init__(self, config: AWSMLOpsConfig):
        """
        Initialize the AWS MLOps fine-tuner.
        
        Args:
            config: AWS MLOps configuration
        """
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize AWS services
        self._setup_aws_services()
        
        # Initialize SageMaker session
        self.sagemaker_session = sagemaker.Session()
        
        # Initialize model and tokenizer
        self.tokenizer = None
        self.model = None
        self.trainer = None
        
        self.logger.info(f"AWS MLOps fine-tuner initialized with {self.config.model_name}")
    
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
    
    def _setup_aws_services(self):
        """Setup AWS services."""
        # Setup AWS session
        if self.config.aws_profile:
            session = boto3.Session(profile_name=self.config.aws_profile)
        else:
            session = boto3.Session()
        
        # Initialize clients
        self.s3_client = session.client('s3', region_name=self.config.aws_region)
        self.sagemaker_client = session.client('sagemaker', region_name=self.config.aws_region)
        self.sts_client = session.client('sts', region_name=self.config.aws_region)
        
        # Get account ID
        self.account_id = self.sts_client.get_caller_identity()['Account']
        
        # Setup SageMaker session
        self.sagemaker_session = sagemaker.Session(
            boto_session=session,
            default_bucket=self.config.s3_bucket
        )
        
        # Get SageMaker role
        self.role = sagemaker.get_execution_role()
        
        self.logger.info(f"AWS services setup complete. Account: {self.account_id}")
    
    def _get_s3_bucket(self) -> str:
        """Get or create S3 bucket for SageMaker."""
        if self.config.s3_bucket:
            return self.config.s3_bucket
        
        # Generate bucket name
        bucket_name = f"sagemaker-{self.config.aws_region}-{self.account_id}"
        
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=bucket_name)
            self.logger.info(f"Using existing bucket: {bucket_name}")
        except ClientError:
            # Create new bucket
            try:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.config.aws_region}
                )
                self.logger.info(f"Created new bucket: {bucket_name}")
            except ClientError as e:
                # If bucket name exists, create with timestamp
                import time
                bucket_name = f"sagemaker-{self.config.aws_region}-{self.account_id}-{int(time.time())}"
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.config.aws_region}
                )
                self.logger.info(f"Created new bucket with timestamp: {bucket_name}")
        
        return bucket_name
    
    def _upload_data_to_s3(self, texts: List[str], eval_texts: Optional[List[str]] = None) -> Tuple[str, str]:
        """
        Upload training and evaluation data to S3.
        
        Args:
            texts: Training texts
            eval_texts: Evaluation texts
            
        Returns:
            Tuple of (train_data_uri, eval_data_uri)
        """
        bucket = self._get_s3_bucket()
        
        # Prepare training data
        train_data = {"text": texts}
        train_data_path = os.path.join(self.config.output_dir, "train_data.json")
        with open(train_data_path, "w") as f:
            json.dump(train_data, f)
        
        # Upload training data
        train_key = f"{self.config.s3_prefix}/train/train_data.json"
        self.s3_client.upload_file(train_data_path, bucket, train_key)
        train_data_uri = f"s3://{bucket}/{train_key}"
        
        # Prepare evaluation data
        if eval_texts:
            eval_data = {"text": eval_texts}
            eval_data_path = os.path.join(self.config.output_dir, "eval_data.json")
            with open(eval_data_path, "w") as f:
                json.dump(eval_data, f)
            
            # Upload evaluation data
            eval_key = f"{self.config.s3_prefix}/eval/eval_data.json"
            self.s3_client.upload_file(eval_data_path, bucket, eval_key)
            eval_data_uri = f"s3://{bucket}/{eval_key}"
        else:
            eval_data_uri = None
        
        self.logger.info(f"Data uploaded to S3: {train_data_uri}")
        if eval_data_uri:
            self.logger.info(f"Evaluation data uploaded to S3: {eval_data_uri}")
        
        return train_data_uri, eval_data_uri
    
    def _create_training_script(self) -> str:
        """Create training script for SageMaker."""
        script_content = f'''
import os
import json
import torch
import torch.nn as nn
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    get_linear_schedule_with_warmup,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling
)
from datasets import Dataset as HFDataset
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data(train_data_path, eval_data_path=None):
    """Load training and evaluation data."""
    # Load training data
    with open(train_data_path, "r") as f:
        train_data = json.load(f)
    
    train_dataset = HFDataset.from_dict(train_data)
    
    # Tokenize dataset
    tokenizer = AutoTokenizer.from_pretrained("{self.config.model_name}")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            truncation=True,
            padding='max_length',
            max_length={self.config.max_length}
        )
    
    train_dataset = train_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=['text']
    )
    
    # Set format for PyTorch
    train_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'labels'])
    
    eval_dataset = None
    if eval_data_path:
        with open(eval_data_path, "r") as f:
            eval_data = json.load(f)
        
        eval_dataset = HFDataset.from_dict(eval_data)
        eval_dataset = eval_dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=['text']
        )
        eval_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'labels'])
    
    return train_dataset, eval_dataset, tokenizer

def compute_metrics(eval_pred):
    """Compute evaluation metrics."""
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
    
    return {{"perplexity": perplexity.item(), "eval_loss": loss.item()}}

def main():
    """Main training function."""
    # Get hyperparameters
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-name', type=str, default="{self.config.model_name}")
    parser.add_argument('--learning-rate', type=float, default={self.config.learning_rate})
    parser.add_argument('--batch-size', type=int, default={self.config.batch_size})
    parser.add_argument('--num-epochs', type=int, default={self.config.num_epochs})
    parser.add_argument('--warmup-steps', type=int, default={self.config.warmup_steps})
    parser.add_argument('--weight-decay', type=float, default={self.config.weight_decay})
    parser.add_argument('--r', type=int, default={self.config.r})
    parser.add_argument('--lora-alpha', type=int, default={self.config.lora_alpha})
    parser.add_argument('--lora-dropout', type=float, default={self.config.lora_dropout})
    parser.add_argument('--use-peft', type=bool, default={self.config.use_peft})
    parser.add_argument('--peft-method', type=str, default="{self.config.peft_method}")
    parser.add_argument('--max-length', type=int, default={self.config.max_length})
    parser.add_argument('--gradient-accumulation-steps', type=int, default={self.config.gradient_accumulation_steps})
    parser.add_argument('--max-grad-norm', type=float, default={self.config.max_grad_norm})
    parser.add_argument('--use-gradient-checkpointing', type=bool, default={self.config.use_gradient_checkpointing})
    parser.add_argument('--use-mixed-precision', type=bool, default={self.config.use_mixed_precision})
    
    # SageMaker specific arguments
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN'))
    parser.add_argument('--eval', type=str, default=os.environ.get('SM_CHANNEL_EVAL'))
    
    args, _ = parser.parse_known_args()
    
    # Load data
    train_data_path = os.path.join(args.train, "train_data.json")
    eval_data_path = os.path.join(args.eval, "eval_data.json") if args.eval else None
    
    train_dataset, eval_dataset, tokenizer = load_data(train_data_path, eval_data_path)
    
    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        torch_dtype=torch.float16 if args.use_mixed_precision else torch.float32
    )
    
    # Enable gradient checkpointing
    if args.use_gradient_checkpointing:
        model.gradient_checkpointing_enable()
    
    # Apply PEFT if enabled
    if args.use_peft:
        if args.peft_method == "lora":
            peft_config = LoraConfig(
                r=args.r,
                lora_alpha=args.lora_alpha,
                target_modules={self.config.target_modules},
                lora_dropout=args.lora_dropout,
                bias="none",
                task_type=TaskType.CAUSAL_LM
            )
            model = get_peft_model(model, peft_config)
        
        # Print trainable parameters
        model.print_trainable_parameters()
    
    # Setup training arguments
    training_args = TrainingArguments(
        output_dir=args.model_dir,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.num_epochs,
        weight_decay=args.weight_decay,
        evaluation_strategy="steps" if eval_dataset else "no",
        eval_steps={self.config.eval_steps} if eval_dataset else None,
        save_steps={self.config.save_steps},
        logging_steps={self.config.logging_steps},
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        gradient_checkpointing=args.use_gradient_checkpointing,
        fp16=args.use_mixed_precision,
        max_grad_norm=args.max_grad_norm,
        warmup_steps=args.warmup_steps,
        save_total_limit=3,
        load_best_model_at_end=True if eval_dataset else False,
        metric_for_best_model="eval_loss" if eval_dataset else None,
        greater_is_better=False if eval_dataset else None,
        dataloader_num_workers=4,
        remove_unused_columns=False,
        report_to=["none"],  # Disable default logging for SageMaker
    )
    
    # Setup data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics if eval_dataset else None,
    )
    
    # Train model
    logger.info("Starting training...")
    train_result = trainer.train()
    
    # Save model
    trainer.save_model()
    
    # Save tokenizer
    tokenizer.save_pretrained(args.model_dir)
    
    # Save training metrics
    metrics = train_result.metrics
    with open(os.path.join(args.model_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Training completed. Metrics: {{metrics}}")

if __name__ == "__main__":
    main()
'''
        
        # Save training script
        script_path = os.path.join(self.config.output_dir, "train.py")
        with open(script_path, "w") as f:
            f.write(script_content)
        
        return script_path
    
    def _create_inference_script(self) -> str:
        """Create inference script for SageMaker endpoint."""
        script_content = f'''
import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def model_fn(model_dir):
    """Load the model and tokenizer."""
    model = AutoModelForCausalLM.from_pretrained(model_dir)
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    
    # Set model to evaluation mode
    model.eval()
    
    return {{'model': model, 'tokenizer': tokenizer}}

def input_fn(request_body, request_content_type):
    """Parse input request."""
    if request_content_type == "application/json":
        input_data = json.loads(request_body)
        return input_data
    else:
        raise ValueError(f"Unsupported content type: {{request_content_type}}")

def predict_fn(input_data, model_objects):
    """Generate predictions."""
    model = model_objects['model']
    tokenizer = model_objects['tokenizer']
    
    prompt = input_data.get("prompt", "")
    max_length = input_data.get("max_length", 100)
    
    # Tokenize input
    inputs = tokenizer(prompt, return_tensors="pt")
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length + len(inputs['input_ids'][0]),
            do_sample=True,
            top_p=0.95,
            temperature=0.7
        )
    
    # Decode output
    generated_text = tokenizer.decode(
        outputs[0][len(inputs['input_ids'][0]):], 
        skip_special_tokens=True
    )
    
    return {{"generated_text": generated_text}}

def output_fn(prediction, response_content_type):
    """Format output response."""
    if response_content_type == "application/json":
        return json.dumps(prediction), response_content_type
    else:
        raise ValueError(f"Unsupported content type: {{response_content_type}}")
'''
        
        # Save inference script
        script_path = os.path.join(self.config.output_dir, "inference.py")
        with open(script_path, "w") as f:
            f.write(script_content)
        
        return script_path
    
    def train(self, texts: List[str], eval_texts: Optional[List[str]] = None):
        """
        Main training loop with AWS SageMaker integration.
        
        Args:
            texts: Training texts
            eval_texts: Evaluation texts
        """
        # Create output directory
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # Upload data to S3
        train_data_uri, eval_data_uri = self._upload_data_to_s3(texts, eval_texts)
        
        # Create training script
        script_path = self._create_training_script()
        
        # Setup SageMaker estimator
        estimator = PyTorch(
            entry_point=script_path,
            role=self.role,
            framework_version="2.0.0",
            py_version="py310",
            instance_count=self.config.instance_count,
            instance_type=self.config.instance_type,
            volume_size=self.config.volume_size,
            max_run=self.config.max_run_time,
            hyperparameters={
                'model-name': self.config.model_name,
                'learning-rate': self.config.learning_rate,
                'batch-size': self.config.batch_size,
                'num-epochs': self.config.num_epochs,
                'warmup-steps': self.config.warmup_steps,
                'weight-decay': self.config.weight_decay,
                'r': self.config.r,
                'lora-alpha': self.config.lora_alpha,
                'lora-dropout': self.config.lora_dropout,
                'use-peft': self.config.use_peft,
                'peft-method': self.config.peft_method,
                'max-length': self.config.max_length,
                'gradient-accumulation-steps': self.config.gradient_accumulation_steps,
                'max-grad-norm': self.config.max_grad_norm,
                'use-gradient-checkpointing': self.config.use_gradient_checkpointing,
                'use-mixed-precision': self.config.use_mixed_precision,
            },
            sagemaker_session=self.sagemaker_session
        )
        
        # Setup data channels
        data_channels = {'train': train_data_uri}
        if eval_data_uri:
            data_channels['eval'] = eval_data_uri
        
        # Start training
        self.logger.info("Starting training with SageMaker...")
        estimator.fit(data_channels)
        
        self.logger.info(f"Training completed. Model saved to: {estimator.model_data}")
        
        return estimator
    
    def hyperparameter_tuning(self, texts: List[str], eval_texts: Optional[List[str]] = None):
        """
        Perform hyperparameter tuning using SageMaker Hyperparameter Tuning.
        
        Args:
            texts: Training texts
            eval_texts: Evaluation texts
        """
        # Upload data to S3
        train_data_uri, eval_data_uri = self._upload_data_to_s3(texts, eval_texts)
        
        # Create training script
        script_path = self._create_training_script()
        
        # Setup SageMaker estimator
        estimator = PyTorch(
            entry_point=script_path,
            role=self.role,
            framework_version="2.0.0",
            py_version="py310",
            instance_count=self.config.instance_count,
            instance_type=self.config.instance_type,
            volume_size=self.config.volume_size,
            max_run=self.config.max_run_time,
            hyperparameters={
                'model-name': self.config.model_name,
                'max-length': self.config.max_length,
                'use-peft': self.config.use_peft,
                'peft-method': self.config.peft_method,
                'gradient-accumulation-steps': self.config.gradient_accumulation_steps,
                'max-grad-norm': self.config.max_grad_norm,
                'use-gradient-checkpointing': self.config.use_gradient_checkpointing,
                'use-mixed-precision': self.config.use_mixed_precision,
            },
            sagemaker_session=self.sagemaker_session
        )
        
        # Setup hyperparameter ranges
        hyperparameter_ranges = {
            'learning-rate': ContinuousParameter(1e-5, 5e-4),
            'batch-size': CategoricalParameter([2, 4, 8]),
            'num-epochs': IntegerParameter(2, 5),
            'r': CategoricalParameter([4, 8, 16]),
            'lora-alpha': CategoricalParameter([8, 16, 32])
        }
        
        # Setup objective metric
        objective_metric_name = 'eval_loss'
        objective_type = 'Minimize'
        
        # Setup hyperparameter tuner
        tuner = HyperparameterTuner(
            estimator=estimator,
            objective_metric_name=objective_metric_name,
            hyperparameter_ranges=hyperparameter_ranges,
            objective_type=objective_type,
            max_jobs=20,
            max_parallel_jobs=4,
            base_tuning_job_name='fine-tuning-hpo'
        )
        
        # Setup data channels
        data_channels = {'train': train_data_uri}
        if eval_data_uri:
            data_channels['eval'] = eval_data_uri
        
        # Start hyperparameter tuning
        self.logger.info("Starting hyperparameter tuning...")
        tuner.fit(data_channels)
        
        # Get best training job
        best_training_job = tuner.best_training_job()
        self.logger.info(f"Best training job: {best_training_job}")
        
        return tuner, best_training_job
    
    def register_model(self, estimator, model_version: str = "1.0"):
        """
        Register the model in SageMaker Model Registry.
        
        Args:
            estimator: Trained SageMaker estimator
            model_version: Model version
        """
        # Create model package group if it doesn't exist
        try:
            self.sagemaker_client.describe_model_package_group(
                ModelPackageGroupName=self.config.model_package_group_name
            )
        except self.sagemaker_client.exceptions.ClientError:
            self.sagemaker_client.create_model_package_group(
                ModelPackageGroupName=self.config.model_package_group_name,
                ModelPackageGroupDescription=self.config.model_description
            )
        
        # Create model metrics
        model_metrics = ModelMetrics(
            model_statistics=MetricsSource(
                s3_uri=f"{estimator.model_data}/metrics.json",
                content_type="application/json"
            )
        )
        
        # Register model
        model_package_arn = self.sagemaker_client.create_model_package(
            ModelPackageGroupName=self.config.model_package_group_name,
            ModelPackageDescription=self.config.model_description,
            ModelApprovalStatus=self.config.approval_status,
            InferenceSpecification={
                'Containers': [
                    {
                        'Image': estimator.image_uri,
                        'ModelDataUrl': estimator.model_data,
                        'Environment': {
                            'SAGEMAKER_PROGRAM': 'inference.py'
                        }
                    }
                ],
                'SupportedContentTypes': ['application/json'],
                'SupportedResponseMIMETypes': ['application/json']
            },
            ModelMetrics=model_metrics
        )['ModelPackageArn']
        
        self.logger.info(f"Model registered: {model_package_arn}")
        
        return model_package_arn
    
    def deploy_model(self, estimator):
        """
        Deploy the model to SageMaker endpoint.
        
        Args:
            estimator: Trained SageMaker estimator
        """
        # Create inference script
        inference_script = self._create_inference_script()
        
        # Create SageMaker model
        model = Model(
            model_data=estimator.model_data,
            image_uri=estimator.image_uri,
            role=self.role,
            entry_point=inference_script,
            sagemaker_session=self.sagemaker_session,
            name=self.config.endpoint_name
        )
        
        # Deploy model
        predictor = model.deploy(
            initial_instance_count=self.config.endpoint_initial_instance_count,
            instance_type=self.config.endpoint_instance_type,
            endpoint_name=self.config.endpoint_name
        )
        
        self.logger.info(f"Model deployed to endpoint: {self.config.endpoint_name}")
        self.logger.info(f"Endpoint URL: {predictor.endpoint_name}")
        
        return predictor
    
    def evaluate(self, estimator) -> Dict[str, float]:
        """
        Evaluate the model.
        
        Args:
            estimator: Trained SageMaker estimator
            
        Returns:
            Dictionary containing evaluation metrics
        """
        # Download metrics from S3
        import tempfile
        import boto3
        
        s3 = boto3.client('s3')
        bucket = estimator.model_data.split('/')[2]
        key = '/'.join(estimator.model_data.split('/')[3:]) + '/metrics.json'
        
        with tempfile.NamedTemporaryFile() as f:
            s3.download_file(bucket, key, f.name)
            with open(f.name, 'r') as metrics_file:
                metrics = json.load(metrics_file)
        
        self.logger.info(f"Evaluation metrics: {metrics}")
        return metrics
    
    def generate_text(self, prompt: str, max_length: int = 100, **kwargs) -> str:
        """
        Generate text using the deployed model.
        
        Args:
            prompt: Input prompt
            max_length: Maximum length of generated text
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        # Create predictor if not exists
        if not hasattr(self, 'predictor'):
            # Get existing endpoint
            self.predictor = Predictor(
                endpoint_name=self.config.endpoint_name,
                sagemaker_session=self.sagemaker_session,
                serializer=JSONSerializer(),
                deserializer=JSONDeserializer()
            )
        
        # Generate text
        input_data = {
            "prompt": prompt,
            "max_length": max_length,
            **kwargs
        }
        
        response = self.predictor.predict(input_data)
        generated_text = response["generated_text"]
        
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
    """Main function to demonstrate AWS MLOps fine-tuning."""
    
    # Create output directory
    os.makedirs("./aws_mlops_output", exist_ok=True)
    
    # Setup configuration
    config = AWSMLOpsConfig(
        # AWS settings
        aws_region="us-east-1",
        aws_profile=None,  # Use default credentials
        
        # Model settings
        model_name="microsoft/DialoGPT-small",
        use_peft=True,
        peft_method="lora",
        r=8,
        learning_rate=2e-4,
        batch_size=4,
        num_epochs=2,  # Reduced for demo
        max_length=128,
        output_dir="./aws_mlops_output",
        
        # SageMaker settings
        instance_type="ml.g4dn.xlarge",
        instance_count=1,
        volume_size=30,
        max_run_time=3600,
        
        # Experiment settings
        experiment_name="dialogpt-finetuning-demo",
        trial_name="dialogpt-lora-finetuning",
        
        # Model registration settings
        model_package_group_name="dialogpt-finetuned",
        model_description="Fine-tuned DialoGPT model for conversational AI",
        
        # Deployment settings
        endpoint_name="dialogpt-service",
        endpoint_instance_type="ml.m5.large",
        endpoint_initial_instance_count=1
    )
    
    # Load sample data
    print("Loading sample data...")
    train_texts = load_sample_data()
    
    # Initialize and train
    print("Initializing AWS MLOps fine-tuner...")
    trainer = AWSMLOpsFineTuner(config)
    
    print("Starting training...")
    estimator = trainer.train(train_texts)
    
    # Evaluate
    print("\nEvaluating model...")
    metrics = trainer.evaluate(estimator)
    
    # Register model
    print("\nRegistering model...")
    model_package_arn = trainer.register_model(estimator)
    
    # Deploy model
    predictor = trainer.deploy_model(estimator)
    
    # Test generation
    print("\nTesting generation...")
    prompt = "Hello, how are you today?"
    generated = trainer.generate_text(prompt, max_length=50)
    print(f"Prompt: {prompt}")
    print(f"Generated: {generated}")
    
    print("\nTraining complete! Model deployed to SageMaker endpoint.")


if __name__ == "__main__":
    main()    predictor = trainer.deploy_model(estimator)
    
    # Test generation
    print("\nTesting generation...")
    prompt = "Hello, how are you today?"
    generated = trainer.generate_text(prompt, max_length=50)
    print(f"Prompt: {prompt}")
    print(f"Generated: {generated}")
    
    print("\nTraining complete! Model deployed to SageMaker endpoint.")


if __name__ == "__main__":




