#!/usr/bin/env python3
"""
Azure MLOps Fine-Tuning Implementation

This module provides a comprehensive implementation of fine-tuning using Azure Machine Learning
services, including experiment tracking, model registration, deployment, and monitoring.

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
import azureml.core
from azureml.core import Workspace, Experiment, Environment, ComputeTarget, ScriptRunConfig
from azureml.core.compute import AmlCompute, ComputeInstance
from azureml.core.compute_target import ComputeTargetException
from azureml.core.model import Model
from azureml.train.hyperdrive import (
    BayesianParameterSampling,
    choice, 
    uniform,
    HyperDriveConfig,
    PrimaryMetricGoal
)
from azureml.core.webservice import AciWebservice, AksWebservice
from azureml.core.conda_dependencies import CondaDependencies
import mlflow
import mlflow.pytorch
from azureml.core.authentication import ServicePrincipalAuthentication


@dataclass
class AzureMLOpsConfig:
    """Configuration for Azure MLOps fine-tuning."""
    
    # Azure ML Configuration
    subscription_id: str = None
    resource_group: str = None
    workspace_name: str = None
    tenant_id: str = None
    service_principal_id: str = None
    service_principal_password: str = None
    
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
    
    # Azure ML Compute
    compute_cluster_name: str = "gpu-cluster"
    vm_size: str = "Standard_NC6"  # GPU-enabled VM
    min_nodes: int = 0
    max_nodes: int = 2
    idle_seconds_before_scaledown: int = 1200
    
    # Azure ML Environment
    conda_env_name: str = "pytorch-env"
    pip_packages: List[str] = None
    
    # Experiment configuration
    experiment_name: str = "fine-tuning-experiment"
    run_name: Optional[str] = None
    
    # Model registration
    model_name: str = "fine-tuned-model"
    model_description: str = "Fine-tuned model using Azure MLOps"
    model_tags: Dict[str, str] = None
    
    # Deployment configuration
    deployment_name: str = "fine-tuned-model-service"
    deployment_type: str = "aci"  # "aci" or "aks"
    cpu_cores: int = 1
    memory_gb: int = 2
    
    # Advanced training settings
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    use_gradient_checkpointing: bool = True
    use_mixed_precision: bool = True
    
    # Logging and saving
    save_steps: int = 500
    eval_steps: int = 250
    logging_steps: int = 100
    output_dir: str = "./azure_mlops_output"
    
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
        
        if self.pip_packages is None:
            self.pip_packages = [
                "torch>=2.0.0",
                "transformers>=4.30.0",
                "datasets>=2.0.0",
                "peft>=0.4.0",
                "accelerate>=0.20.0",
                "wandb>=0.13.0",
                "tqdm>=4.64.0",
                "numpy>=1.21.0",
                "mlflow>=2.0.0"
            ]
        
        if self.model_tags is None:
            self.model_tags = {
                "model_type": self.model_name,
                "peft_method": self.peft_method if self.use_peft else "full",
                "fine_tuning_date": str(datetime.now().date())
            }


class AzureMLOpsDataset(Dataset):
    """Dataset class for Azure MLOps fine-tuning."""
    
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


class AzureMLOpsFineTuner:
    """Main class for Azure MLOps fine-tuning."""
    
    def __init__(self, config: AzureMLOpsConfig):
        """
        Initialize the Azure MLOps fine-tuner.
        
        Args:
            config: Azure MLOps configuration
        """
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize Azure ML components
        self.workspace = None
        self.experiment = None
        self.compute_target = None
        self.environment = None
        
        # Initialize MLflow
        self._setup_mlflow()
        
        # Initialize model and tokenizer
        self.tokenizer = None
        self.model = None
        self.trainer = None
        
        self.logger.info(f"Azure MLOps fine-tuner initialized with {self.config.model_name}")
    
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
    
    def _setup_mlflow(self):
        """Setup MLflow for experiment tracking."""
        # Set MLflow tracking URI to Azure ML
        mlflow.set_tracking_uri(self.workspace.get_mlflow_tracking_uri())
        mlflow.set_experiment(self.config.experiment_name)
    
    def setup_workspace(self):
        """Setup Azure ML workspace."""
        try:
            # Try to get existing workspace
            self.workspace = Workspace.get(
                name=self.config.workspace_name,
                subscription_id=self.config.subscription_id,
                resource_group=self.config.resource_group
            )
            self.logger.info(f"Found existing workspace: {self.workspace.name}")
        except:
            # Create new workspace if not found
            self.workspace = Workspace.create(
                name=self.config.workspace_name,
                subscription_id=self.config.subscription_id,
                resource_group=self.config.resource_group,
                location="eastus"  # Choose your preferred location
            )
            self.logger.info(f"Created new workspace: {self.workspace.name}")
    
    def setup_compute(self):
        """Setup Azure ML compute target."""
        try:
            # Try to get existing compute target
            self.compute_target = ComputeTarget(workspace=self.workspace, name=self.config.compute_cluster_name)
            self.logger.info(f"Found existing compute target: {self.compute_target.name}")
        except ComputeTargetException:
            # Create new compute target
            compute_config = AmlCompute.provisioning_configuration(
                vm_size=self.config.vm_size,
                min_nodes=self.config.min_nodes,
                max_nodes=self.config.max_nodes,
                idle_seconds_before_scaledown=self.config.idle_seconds_before_scaledown
            )
            
            self.compute_target = ComputeTarget.create(
                self.workspace,
                self.config.compute_cluster_name,
                compute_config
            )
            
            self.compute_target.wait_for_completion(show_output=True)
            self.logger.info(f"Created new compute target: {self.compute_target.name}")
    
    def setup_environment(self):
        """Setup Azure ML environment."""
        # Create conda dependencies
        conda_deps = CondaDependencies()
        
        # Add pip packages
        for package in self.config.pip_packages:
            conda_deps.add_pip_package(package)
        
        # Create environment
        self.environment = Environment(name=self.config.conda_env_name)
        self.environment.python.conda_dependencies = conda_deps
        self.environment.register(workspace=self.workspace)
        
        self.logger.info(f"Created environment: {self.environment.name}")
    
    def setup_experiment(self):
        """Setup Azure ML experiment."""
        self.experiment = Experiment(workspace=self.workspace, name=self.config.experiment_name)
        self.logger.info(f"Created experiment: {self.experiment.name}")
    
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
            from datasets import load_dataset
            dataset = load_dataset(self.config.dataset_name)
            if 'train' in dataset:
                self.train_dataset = dataset['train']
            else:
                self.train_dataset = dataset
        else:
            # Create from local texts
            from datasets import Dataset as HFDataset
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
        """Setup HuggingFace Trainer with Azure ML integration."""
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
            report_to=["azure_ml", "wandb"] if self.config.log_to_wandb else ["azure_ml"],
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
        
        self.logger.info("Trainer setup complete with Azure ML integration")
    
    def train(self, texts: List[str], eval_texts: Optional[List[str]] = None):
        """
        Main training loop with Azure ML integration.
        
        Args:
            texts: Training texts
            eval_texts: Evaluation texts
        """
        # Setup Azure ML components
        self.setup_workspace()
        self.setup_compute()
        self.setup_environment()
        self.setup_experiment()
        
        # Prepare data
        self.prepare_data(texts, eval_texts)
        
        # Setup trainer
        self.setup_trainer()
        
        # Start MLflow run
        with mlflow.start_run(run_name=self.config.run_name):
            # Log parameters
            mlflow.log_params(self.config.__dict__)
            
            # Train model
            self.logger.info("Starting training with Azure ML integration...")
            train_result = self.trainer.train()
            
            # Log metrics
            mlflow.log_metrics({
                "train_loss": train_result.training_loss,
                "global_step": train_result.global_step
            })
            
            # Save model
            self.trainer.save_model()
            
            # Register model in Azure ML
            self.register_model()
            
            # Log artifacts
            mlflow.log_artifacts(self.config.output_dir)
            
            self.logger.info(f"Training completed. Results: {train_result}")
        
        return train_result
    
    def register_model(self):
        """Register the model in Azure ML."""
        # Register model
        model = Model.register(
            workspace=self.workspace,
            model_path=self.config.output_dir,
            model_name=self.config.model_name,
            description=self.config.model_description,
            tags=self.config.model_tags
        )
        
        self.logger.info(f"Model registered: {model.name}, version: {model.version}")
    
    def hyperparameter_tuning(self, texts: List[str], eval_texts: Optional[List[str]] = None):
        """
        Perform hyperparameter tuning using Azure ML HyperDrive.
        
        Args:
            texts: Training texts
            eval_texts: Evaluation texts
        """
        # Setup Azure ML components
        self.setup_workspace()
        self.setup_compute()
        self.setup_environment()
        self.setup_experiment()
        
        # Define hyperparameter search space
        param_sampling = BayesianParameterSampling({
            "learning_rate": uniform(1e-5, 5e-4),
            "batch_size": choice(2, 4, 8),
            "num_epochs": choice(2, 3, 5),
            "r": choice(4, 8, 16),
            "lora_alpha": choice(8, 16, 32)
        })
        
        # Setup script run configuration
        src = ScriptRunConfig(
            source_directory=".",
            script="azure_mlops_fine_tuning.py",
            arguments=[
                "--model_name", self.config.model_name,
                "--use_peft", str(self.config.use_peft),
                "--peft_method", self.config.peft_method,
                "--train_texts", " ".join(texts),
                "--eval_texts", " ".join(eval_texts) if eval_texts else "",
                "--output_dir", self.config.output_dir
            ],
            compute_target=self.compute_target,
            environment=self.environment
        )
        
        # Setup hyperdrive configuration
        hyperdrive_config = HyperDriveConfig(
            run_config=src,
            hyperparameter_sampling=param_sampling,
            primary_metric_name="eval_loss",
            primary_metric_goal=PrimaryMetricGoal.MINIMIZE,
            max_total_runs=20,
            max_concurrent_runs=4
        )
        
        # Submit hyperdrive run
        hyperdrive_run = self.experiment.submit(hyperdrive_config)
        hyperdrive_run.wait_for_completion(show_output=True)
        
        # Get best run
        best_run = hyperdrive_run.get_best_run_by_primary_metric()
        best_run_metrics = best_run.get_metrics()
        
        self.logger.info(f"Best run: {best_run.id}")
        self.logger.info(f"Best metrics: {best_run_metrics}")
        
        return best_run, best_run_metrics
    
    def deploy_model(self, model_name: str, model_version: int):
        """
        Deploy the model to Azure.
        
        Args:
            model_name: Name of the registered model
            model_version: Version of the model to deploy
        """
        # Get the model
        model = Model(workspace=self.workspace, name=model_name, version=model_version)
        
        # Define inference configuration
        from azureml.core.model import InferenceConfig
        
        inference_config = InferenceConfig(
            entry_script="score.py",
            environment=self.environment
        )
        
        # Define deployment configuration
        if self.config.deployment_type == "aci":
            deployment_config = AciWebservice.deploy_configuration(
                cpu_cores=self.config.cpu_cores,
                memory_gb=self.config.memory_gb,
                description=self.config.model_description
            )
        elif self.config.deployment_type == "aks":
            # Setup AKS compute (if not already done)
            try:
                aks_target = ComputeTarget(workspace=self.workspace, name="aks-cluster")
            except ComputeTargetException:
                # Create AKS cluster
                from azureml.core.compute import AksCompute
                
                prov_config = AksCompute.provisioning_configuration(
                    vm_size=self.config.vm_size,
                    agent_count=1
                )
                
                aks_target = ComputeTarget.create(
                    self.workspace,
                    "aks-cluster",
                    prov_config
                )
                
                aks_target.wait_for_completion(show_output=True)
            
            deployment_config = AksWebservice.deploy_configuration(
                cpu_cores=self.config.cpu_cores,
                memory_gb=self.config.memory_gb,
                autoscale_enabled=True,
                autoscale_min_replicas=1,
                autoscale_max_replicas=3,
                autoscale_refresh_seconds=10,
                autoscale_target_utilization=70
            )
        
        # Deploy the model
        service = Model.deploy(
            workspace=self.workspace,
            name=self.config.deployment_name,
            models=[model],
            inference_config=inference_config,
            deployment_config=deployment_config
        )
        
        service.wait_for_deployment(show_output=True)
        
        self.logger.info(f"Model deployed: {service.name}")
        self.logger.info(f"Service URL: {service.scoring_uri}")
        
        return service
    
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
    """Main function to demonstrate Azure MLOps fine-tuning."""
    
    # Create output directory
    os.makedirs("./azure_mlops_output", exist_ok=True)
    
    # Setup configuration
    config = AzureMLOpsConfig(
        # Azure ML settings
        subscription_id="your-subscription-id",
        resource_group="your-resource-group",
        workspace_name="your-workspace-name",
        tenant_id="your-tenant-id",
        service_principal_id="your-service-principal-id",
        service_principal_password="your-service-principal-password",
        
        # Model settings
        model_name="microsoft/DialoGPT-small",
        use_peft=True,
        peft_method="lora",
        r=8,
        learning_rate=2e-4,
        batch_size=4,
        num_epochs=2,  # Reduced for demo
        max_length=128,
        output_dir="./azure_mlops_output",
        
        # Experiment settings
        experiment_name="dialogpt-finetuning-demo",
        run_name="dialogpt-lora-finetuning",
        
        # Model registration settings
        model_name="dialogpt-finetuned",
        model_description="Fine-tuned DialoGPT model for conversational AI",
        
        # Deployment settings
        deployment_name="dialogpt-service",
        deployment_type="aci",
        cpu_cores=1,
        memory_gb=2
    )
    
    # Load sample data
    print("Loading sample data...")
    train_texts = load_sample_data()
    
    # Initialize and train
    print("Initializing Azure MLOps fine-tuner...")
    trainer = AzureMLOpsFineTuner(config)
    
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
    
    print("\nTraining complete! Model saved to ./azure_mlops_output")


if __name__ == "__main__":
    main()