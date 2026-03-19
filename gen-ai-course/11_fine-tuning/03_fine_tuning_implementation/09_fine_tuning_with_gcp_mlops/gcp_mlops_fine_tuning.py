#!/usr/bin/env python3
"""
GCP MLOps Fine-Tuning Implementation

This module provides a comprehensive implementation of fine-tuning using Google Cloud AI Platform
services, including Vertex AI, experiment tracking, model training, deployment, and monitoring.

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
from google.cloud import aiplatform
from google.cloud.aiplatform import hyperparameter_tuning as hpt
from google.cloud import storage
import mlflow
import mlflow.gcp
from google.oauth2 import service_account
import vertexai
from vertexai.preview.language_models import TextGenerationModel
from vertexai.preview.vision_models import ImageTextModel
import google.auth
from google.auth.transport.requests import Request


@dataclass
class GCPMLOpsConfig:
    """Configuration for GCP MLOps fine-tuning."""
    
    # GCP Configuration
    project_id: str = None
    region: str = "us-central1"
    service_account_path: Optional[str] = None
    
    # Vertex AI Configuration
    vertex_ai_location: str = "us-central1"
    vertex_ai_staging_bucket: str = None
    
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
    
    # Vertex AI Training Configuration
    training_machine_type: str = "n1-standard-4"
    accelerator_type: str = "NVIDIA_TESLA_V100"
    accelerator_count: int = 1
    replica_count: int = 1
    boot_disk_size_gb: int = 100
    
    # GCS Configuration
    gcs_bucket: str = None
    gcs_prefix: str = "fine-tuning"
    
    # Experiment configuration
    experiment_name: str = "fine-tuning-experiment"
    run_name: str = "fine-tuning-run"
    
    # Model registration
    model_display_name: str = "fine-tuned-model"
    model_description: str = "Fine-tuned model using GCP Vertex AI"
    
    # Deployment configuration
    endpoint_display_name: str = "fine-tuned-model-endpoint"
    deployed_model_display_name: str = "fine-tuned-model-deployed"
    deployment_machine_type: str = "n1-standard-2"
    min_replica_count: int = 1
    max_replica_count: int = 3
    
    # Advanced training settings
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    use_gradient_checkpointing: bool = True
    use_mixed_precision: bool = True
    
    # Logging and saving
    save_steps: int = 500
    eval_steps: int = 250
    logging_steps: int = 100
    output_dir: str = "./gcp_mlops_output"
    
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


class GCPMLOpsDataset(Dataset):
    """Dataset class for GCP MLOps fine-tuning."""
    
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


class GCPMLOpsFineTuner:
    """Main class for GCP MLOps fine-tuning."""
    
    def __init__(self, config: GCPMLOpsConfig):
        """
        Initialize the GCP MLOps fine-tuner.
        
        Args:
            config: GCP MLOps configuration
        """
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize GCP services
        self._setup_gcp_services()
        
        # Initialize Vertex AI
        self._setup_vertex_ai()
        
        # Initialize model and tokenizer
        self.tokenizer = None
        self.model = None
        self.trainer = None
        
        self.logger.info(f"GCP MLOps fine-tuner initialized with {self.config.model_name}")
    
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
    
    def _setup_gcp_services(self):
        """Setup GCP services."""
        # Setup authentication
        if self.config.service_account_path:
            credentials = service_account.Credentials.from_service_account_file(
                self.config.service_account_path
            )
            self.credentials = credentials
        else:
            # Use default credentials
            self.credentials, _ = google.auth.default()
        
        # Initialize clients
        self.storage_client = storage.Client(
            project=self.config.project_id,
            credentials=self.credentials
        )
        
        self.logger.info(f"GCP services setup complete. Project: {self.config.project_id}")
    
    def _setup_vertex_ai(self):
        """Setup Vertex AI."""
        # Initialize Vertex AI
        vertexai.init(
            project=self.config.project_id,
            location=self.config.vertex_ai_location,
            staging_bucket=self.config.vertex_ai_staging_bucket,
            credentials=self.credentials
        )
        
        self.logger.info(f"Vertex AI initialized in {self.config.vertex_ai_location}")
    
    def _get_gcs_bucket(self) -> storage.Bucket:
        """Get or create GCS bucket."""
        if self.config.gcs_bucket:
            bucket = self.storage_client.bucket(self.config.gcs_bucket)
            if not bucket.exists():
                bucket.create(location=self.config.region)
                self.logger.info(f"Created new bucket: {self.config.gcs_bucket}")
            else:
                self.logger.info(f"Using existing bucket: {self.config.gcs_bucket}")
            return bucket
        else:
            raise ValueError("GCS bucket must be specified")
    
    def _upload_data_to_gcs(self, texts: List[str], eval_texts: Optional[List[str]] = None) -> Tuple[str, str]:
        """
        Upload training and evaluation data to GCS.
        
        Args:
            texts: Training texts
            eval_texts: Evaluation texts
            
        Returns:
            Tuple of (train_data_uri, eval_data_uri)
        """
        bucket = self._get_gcs_bucket()
        
        # Prepare training data
        train_data = {"text": texts}
        train_data_path = os.path.join(self.config.output_dir, "train_data.json")
        with open(train_data_path, "w") as f:
            json.dump(train_data, f)
        
        # Upload training data
        train_blob = bucket.blob(f"{self.config.gcs_prefix}/train/train_data.json")
        train_blob.upload_from_filename(train_data_path)
        train_data_uri = f"gs://{bucket.name}/{train_blob.name}"
        
        # Prepare evaluation data
        if eval_texts:
            eval_data = {"text": eval_texts}
            eval_data_path = os.path.join(self.config.output_dir, "eval_data.json")
            with open(eval_data_path, "w") as f:
                json.dump(eval_data, f)
            
            # Upload evaluation data
            eval_blob = bucket.blob(f"{self.config.gcs_prefix}/eval/eval_data.json")
            eval_blob.upload_from_filename(eval_data_path)
            eval_data_uri = f"gs://{bucket.name}/{eval_blob.name}"
        else:
            eval_data_uri = None
        
        self.logger.info(f"Data uploaded to GCS: {train_data_uri}")
        if eval_data_uri:
            self.logger.info(f"Evaluation data uploaded to GCS: {eval_data_uri}")
        
        return train_data_uri, eval_data_uri
    
    def _create_training_script(self) -> str:
        """Create training script for Vertex AI."""
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
    
    # Vertex AI specific arguments
    parser.add_argument('--model-dir', type=str, default=os.environ.get('AIP_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('AIP_TRAINING_DATA_URI'))
    parser.add_argument('--eval', type=str, default=os.environ.get('AIP_VALIDATION_DATA_URI'))
    
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
        report_to=["none"],  # Disable default logging for Vertex AI
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
        """Create inference script for Vertex AI endpoint."""
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
        Main training loop with Vertex AI integration.
        
        Args:
            texts: Training texts
            eval_texts: Evaluation texts
        """
        # Create output directory
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # Upload data to GCS
        train_data_uri, eval_data_uri = self._upload_data_to_gcs(texts, eval_texts)
        
        # Create training script
        script_path = self._create_training_script()
        
        # Setup Vertex AI custom training job
        from google.cloud import aiplatform
        
        # Create custom training job
        job = aiplatform.CustomTrainingJob(
            display_name=self.config.run_name,
            script_path=script_path,
            container_uri="gcr.io/cloud-aiplatform/training/pytorch-gpu.1-13:latest",
            requirements=[
                "torch>=2.0.0",
                "transformers>=4.30.0",
                "datasets>=2.0.0",
                "peft>=0.4.0",
                "accelerate>=0.20.0",
                "wandb>=0.13.0",
                "tqdm>=4.64.0",
                "numpy>=1.21.0"
            ],
            model_serving_container_image_uri="gcr.io/cloud-aiplatform/prediction/pytorch-gpu.1-13:latest"
        )
        
        # Setup training arguments
        args = [
            "--model-name", self.config.model_name,
            "--learning-rate", str(self.config.learning_rate),
            "--batch-size", str(self.config.batch_size),
            "--num-epochs", str(self.config.num_epochs),
            "--warmup-steps", str(self.config.warmup_steps),
            "--weight-decay", str(self.config.weight_decay),
            "--r", str(self.config.r),
            "--lora-alpha", str(self.config.lora_alpha),
            "--lora-dropout", str(self.config.lora_dropout),
            "--use-peft", str(self.config.use_peft),
            "--peft-method", self.config.peft_method,
            "--max-length", str(self.config.max_length),
            "--gradient-accumulation-steps", str(self.config.gradient_accumulation_steps),
            "--max-grad-norm", str(self.config.max_grad_norm),
            "--use-gradient-checkpointing", str(self.config.use_gradient_checkpointing),
            "--use-mixed-precision", str(self.config.use_mixed_precision),
            "--train", train_data_uri,
        ]
        
        if eval_data_uri:
            args.extend(["--eval", eval_data_uri])
        
        # Start training
        self.logger.info("Starting training with Vertex AI...")
        model = job.run(
            args=args,
            replica_count=self.config.replica_count,
            machine_type=self.config.machine_type,
            accelerator_type=self.config.accelerator_type,
            accelerator_count=self.config.accelerator_count,
            boot_disk_size_gb=self.config.boot_disk_size_gb,
            staging_bucket=self.config.vertex_ai_staging_bucket
        )
        
        self.logger.info(f"Training completed. Model saved to: {model.resource_name}")
        
        return model
    
    def hyperparameter_tuning(self, texts: List[str], eval_texts: Optional[List[str]] = None):
        """
        Perform hyperparameter tuning using Vertex AI Hyperparameter Tuning.
        
        Args:
            texts: Training texts
            eval_texts: Evaluation texts
        """
        # Upload data to GCS
        train_data_uri, eval_data_uri = self._upload_data_to_gcs(texts, eval_texts)
        
        # Create training script
        script_path = self._create_training_script()
        
        # Setup Vertex AI hyperparameter tuning job
        from google.cloud import aiplatform
        from google.cloud.aiplatform import hyperparameter_tuning as hpt
        
        # Define hyperparameter specs
        hp_spec = {
            'learning-rate': hpt.DoubleParameterSpec(min=1e-5, max=5e-4, scale='linear'),
            'batch-size': hpt.IntegerParameterSpec(min=2, max=8, scale='linear'),
            'num-epochs': hpt.IntegerParameterSpec(min=2, max=5, scale='linear'),
            'r': hpt.CategoricalParameterSpec(values=['4', '8', '16']),
            'lora-alpha': hpt.CategoricalParameterSpec(values=['8', '16', '32'])
        }
        
        # Define metric spec
        metric_spec = {'eval_loss': 'minimize'}
        
        # Create hyperparameter tuning job
        job = aiplatform.HyperparameterTuningJob(
            display_name=f"{self.config.run_name}-hpo",
            custom_job_spec={
                'workerPoolSpecs': [{
                    'machineSpec': {
                        'machineType': self.config.machine_type,
                        'acceleratorType': self.config.accelerator_type,
                        'acceleratorCount': self.config.accelerator_count
                    },
                    'replicaCount': 1,
                    'containerSpec': {
                        'imageUri': "gcr.io/cloud-aiplatform/training/pytorch-gpu.1-13:latest",
                        'command': ['python'],
                        'args': [
                            script_path,
                            '--model-name', self.config.model_name,
                            '--max-length', str(self.config.max_length),
                            '--use-peft', str(self.config.use_peft),
                            '--peft-method', self.config.peft_method,
                            '--gradient-accumulation-steps', str(self.config.gradient_accumulation_steps),
                            '--max-grad-norm', str(self.config.max_grad_norm),
                            '--use-gradient-checkpointing', str(self.config.use_gradient_checkpointing),
                            '--use-mixed-precision', str(self.config.use_mixed_precision),
                            '--train', train_data_uri,
                        ] + (['--eval', eval_data_uri] if eval_data_uri else [])
                    }
                }]
            },
            max_trial_count=20,
            parallel_trial_count=4,
            hyperparameter_spec=hp_spec,
            metrics_spec=metric_spec
        )
        
        # Start hyperparameter tuning
        self.logger.info("Starting hyperparameter tuning...")
        job.run()
        
        # Get best trial
        best_trial = job.trials[0]  # Get the best trial
        self.logger.info(f"Best trial: {best_trial}")
        
        return job, best_trial
    
    def register_model(self, model):
        """
        Register the model in Vertex AI Model Registry.
        
        Args:
            model: Trained Vertex AI model
        """
        # Register model
        registered_model = model.register(
            display_name=self.config.model_display_name,
            description=self.config.model_description,
            labels={"fine-tuning-method": self.config.peft_method}
        )
        
        self.logger.info(f"Model registered: {registered_model.resource_name}")
        
        return registered_model
    
    def deploy_model(self, model):
        """
        Deploy the model to Vertex AI endpoint.
        
        Args:
            model: Registered Vertex AI model
        """
        # Create endpoint
        endpoint = aiplatform.Endpoint.create(
            display_name=self.config.endpoint_display_name
        )
        
        # Deploy model
        deployed_model = endpoint.deploy(
            model=model,
            deployed_model_display_name=self.config.deployed_model_display_name,
            machine_type=self.config.machine_type,
            min_replica_count=self.config.min_replica_count,
            max_replica_count=self.config.max_replica_count
        )
        
        self.logger.info(f"Model deployed to endpoint: {endpoint.resource_name}")
        
        return endpoint, deployed_model
    
    def evaluate(self, model) -> Dict[str, float]:
        """
        Evaluate the model.
        
        Args:
            model: Trained Vertex AI model
            
        Returns:
            Dictionary containing evaluation metrics
        """
        # Download metrics from GCS
        import tempfile
        import json
        
        # Get model artifacts
        model_artifacts = model.uri
        bucket_name = model_artifacts.split('/')[2]
        prefix = '/'.join(model_artifacts.split('/')[3:])
        
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(f"{prefix}/metrics.json")
        
        with tempfile.NamedTemporaryFile() as f:
            blob.download_to_filename(f.name)
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
        # Use Vertex AI endpoint for inference
        endpoint = aiplatform.Endpoint.list(
            filter=f"display_name={self.config.endpoint_display_name}"
        )[0]
        
        # Prepare input
        input_data = {
            "prompt": prompt,
            "max_length": max_length,
            **kwargs
        }
        
        # Make prediction
        response = endpoint.predict([input_data])
        
        # Extract generated text
        generated_text = response.predictions[0]["generated_text"]
        
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
    """Main function to demonstrate GCP MLOps fine-tuning."""
    
    # Create output directory
    os.makedirs("./gcp_mlops_output", exist_ok=True)
    
    # Setup configuration
    config = GCPMLOpsConfig(
        # GCP settings
        project_id="your-project-id",
        region="us-central1",
        service_account_path="path/to/service-account.json",
        
        # Vertex AI settings
        vertex_ai_location="us-central1",
        vertex_ai_staging_bucket="gs://your-staging-bucket",
        
        # Model settings
        model_name="microsoft/DialoGPT-small",
        use_peft=True,
        peft_method="lora",
        r=8,
        learning_rate=2e-4,
        batch_size=4,
        num_epochs=2,  # Reduced for demo
        max_length=128,
        output_dir="./gcp_mlops_output",
        
        # Vertex AI training settings
        training_machine_type="n1-standard-4",
        accelerator_type="NVIDIA_TESLA_V100",
        accelerator_count=1,
        replica_count=1,
        boot_disk_size_gb=100,
        
        # GCS settings
        gcs_bucket="your-gcs-bucket",
        gcs_prefix="fine-tuning",
        
        # Experiment settings
        experiment_name="dialogpt-finetuning-demo",
        run_name="dialogpt-lora-finetuning",
        
        # Model registration settings
        model_display_name="dialogpt-finetuned",
        model_description="Fine-tuned DialoGPT model for conversational AI",
        
        # Deployment settings
        endpoint_display_name="dialogpt-service",
        deployed_model_display_name="dialogpt-deployed",
        deployment_machine_type="n1-standard-2",
        min_replica_count=1,
        max_replica_count=3
    )
    
    # Load sample data
    print("Loading sample data...")
    train_texts = load_sample_data()
    
    # Initialize and train
    print("Initializing GCP MLOps fine-tuner...")
    trainer = GCPMLOpsFineTuner(config)
    
    print("Starting training...")
    model = trainer.train(train_texts)
    
    # Evaluate
    print("\nEvaluating model...")
    metrics = trainer.evaluate(model)
    
    # Register model
    print("\nRegistering model...")
    registered_model = trainer.register_model(model)
    
    # Deploy model
    print("\nDeploying model...")
    endpoint, deployed_model = trainer.deploy_model(registered_model)
    
    # Test generation
    print("\nTesting generation...")
    prompt = "Hello, how are you today?"
    generated = trainer.generate_text(prompt, max_length=50)
    print(f"Prompt: {prompt}")
    print(f"Generated: {generated}")
    
    print("\nTraining complete! Model deployed to Vertex AI endpoint.")


if __name__ == "__main__":
    main()