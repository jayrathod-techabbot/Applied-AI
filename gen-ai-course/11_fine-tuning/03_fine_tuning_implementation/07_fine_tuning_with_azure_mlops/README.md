# Azure MLOps Fine-Tuning Implementation

This directory contains a comprehensive implementation of fine-tuning using Azure Machine Learning services, including experiment tracking, model registration, deployment, and monitoring.

## Overview

Azure Machine Learning provides a complete cloud-based platform for machine learning operations, including compute management, experiment tracking, model versioning, and deployment. This implementation demonstrates how to leverage Azure ML for efficient fine-tuning workflows.

## Key Features

- **Azure ML Workspace**: Complete workspace management and resource organization
- **Compute Clusters**: Scalable GPU compute for training workloads
- **Experiment Tracking**: Comprehensive experiment tracking with MLflow integration
- **Model Registration**: Centralized model versioning and metadata management
- **Hyperparameter Tuning**: Automated hyperparameter optimization with HyperDrive
- **Model Deployment**: Easy deployment to ACI or AKS for production inference
- **Monitoring**: Built-in model monitoring and performance tracking

## Architecture

```
Azure MLOps Pipeline:
1. Setup Azure ML Workspace and Compute
2. Configure Environment and Dependencies
3. Create Experiment and Run Configuration
4. Train Model with Experiment Tracking
5. Register Model in Model Registry
6. Deploy Model to ACI/AKS
7. Monitor and Manage Model Lifecycle
```

## Files

- `azure_mlops_fine_tuning.py` - Main implementation with complete Azure ML pipeline
- `requirements.txt` - Dependencies for Azure MLOps
- `README.md` - This documentation file

## Quick Start

### Prerequisites

1. **Azure Subscription**: You need an active Azure subscription
2. **Azure ML Workspace**: Create a workspace in Azure ML Studio
3. **Service Principal**: Set up service principal for authentication
4. **Compute Resources**: Configure compute clusters for training

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from azure_mlops_fine_tuning import AzureMLOpsFineTuner, AzureMLOpsConfig

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
    num_epochs=3,
    
    # Experiment settings
    experiment_name="fine-tuning-experiment",
    run_name="lora-finetuning-run",
    
    # Model registration settings
    model_name="fine-tuned-model",
    model_description="Fine-tuned model using Azure MLOps"
)

# Initialize trainer
trainer = AzureMLOpsFineTuner(config)

# Prepare data
train_texts = ["Your training data here..."]
trainer.prepare_data(train_texts)

# Train model
train_result = trainer.train(train_texts)

# Register model
trainer.register_model()

# Deploy model
service = trainer.deploy_model("fine-tuned-model", 1)
```

### Advanced Configuration

```python
config = AzureMLOpsConfig(
    # Azure ML Configuration
    subscription_id="your-subscription-id",
    resource_group="your-resource-group",
    workspace_name="your-workspace-name",
    tenant_id="your-tenant-id",
    service_principal_id="your-service-principal-id",
    service_principal_password="your-service-principal-password",
    
    # Model configuration
    model_name="microsoft/DialoGPT-medium",
    tokenizer_name=None,
    
    # PEFT configuration
    use_peft=True,
    peft_method="lora",  # "lora", "qlora", "ia3"
    r=8,
    lora_alpha=16,
    lora_dropout=0.1,
    target_modules=None,
    
    # Quantization configuration (for QLoRA)
    quantization_type="nf4",
    load_in_4bit=False,
    load_in_8bit=False,
    
    # Training configuration
    learning_rate=2e-4,
    batch_size=4,
    num_epochs=3,
    warmup_steps=100,
    weight_decay=0.01,
    
    # Data configuration
    max_length=512,
    train_split=0.8,
    dataset_name=None,
    
    # Azure ML Compute
    compute_cluster_name="gpu-cluster",
    vm_size="Standard_NC6",  # GPU-enabled VM
    min_nodes=0,
    max_nodes=2,
    idle_seconds_before_scaledown=1200,
    
    # Azure ML Environment
    conda_env_name="pytorch-env",
    pip_packages=[
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "datasets>=2.0.0",
        "peft>=0.4.0",
        "accelerate>=0.20.0",
        "wandb>=0.13.0",
        "mlflow>=2.0.0"
    ],
    
    # Experiment configuration
    experiment_name="fine-tuning-experiment",
    run_name=None,
    
    # Model registration
    model_name="fine-tuned-model",
    model_description="Fine-tuned model using Azure MLOps",
    model_tags={
        "model_type": "DialoGPT",
        "peft_method": "lora",
        "fine_tuning_date": "2024-01-01"
    },
    
    # Deployment configuration
    deployment_name="fine-tuned-model-service",
    deployment_type="aci",  # "aci" or "aks"
    cpu_cores=1,
    memory_gb=2,
    
    # Advanced training settings
    gradient_accumulation_steps=1,
    max_grad_norm=1.0,
    use_gradient_checkpointing=True,
    use_mixed_precision=True,
    
    # Logging and saving
    save_steps=500,
    eval_steps=250,
    logging_steps=100,
    output_dir="./azure_mlops_output",
    
    # Device configuration
    device="cuda" if torch.cuda.is_available() else "cpu"
)
```

## Azure ML Setup

### 1. Create Azure ML Workspace

```python
from azureml.core import Workspace

# Create workspace
ws = Workspace.create(
    name="your-workspace-name",
    subscription_id="your-subscription-id",
    resource_group="your-resource-group",
    location="eastus"  # Choose your preferred location
)

# Save workspace config
ws.write_config()
```

### 2. Setup Authentication

```python
from azureml.core.authentication import ServicePrincipalAuthentication

# Service principal authentication
auth = ServicePrincipalAuthentication(
    tenant_id="your-tenant-id",
    service_principal_id="your-service-principal-id",
    service_principal_password="your-service-principal-password"
)

# Get workspace
ws = Workspace.from_config(auth=auth)
```

### 3. Create Compute Cluster

```python
from azureml.core.compute import AmlCompute, ComputeTarget

# Check if compute target exists
try:
    compute_target = ComputeTarget(workspace=ws, name="gpu-cluster")
    print("Found existing compute target")
except:
    # Create new compute target
    compute_config = AmlCompute.provisioning_configuration(
        vm_size="Standard_NC6",
        min_nodes=0,
        max_nodes=2,
        idle_seconds_before_scaledown=1200
    )
    
    compute_target = ComputeTarget.create(
        ws,
        "gpu-cluster",
        compute_config
    )
    
    compute_target.wait_for_completion(show_output=True)
```

## Experiment Tracking

### MLflow Integration

```python
import mlflow
import mlflow.pytorch

# Set MLflow tracking URI
mlflow.set_tracking_uri(ws.get_mlflow_tracking_uri())
mlflow.set_experiment("fine-tuning-experiment")

# Start run
with mlflow.start_run(run_name="lora-finetuning"):
    # Log parameters
    mlflow.log_params(config.__dict__)
    
    # Train model
    train_result = trainer.train(train_texts)
    
    # Log metrics
    mlflow.log_metrics({
        "train_loss": train_result.training_loss,
        "global_step": train_result.global_step
    })
    
    # Log model
    mlflow.pytorch.log_model(trainer.model, "model")
```

### Custom Metrics

```python
def compute_custom_metrics(eval_pred):
    predictions, labels = eval_pred
    
    # Your custom metrics computation
    accuracy = compute_accuracy(predictions, labels)
    f1_score = compute_f1_score(predictions, labels)
    perplexity = compute_perplexity(predictions, labels)
    
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

## Hyperparameter Tuning

### HyperDrive Configuration

```python
from azureml.train.hyperdrive import (
    BayesianParameterSampling,
    choice, 
    uniform,
    HyperDriveConfig,
    PrimaryMetricGoal
)

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
        "--model_name", config.model_name,
        "--use_peft", str(config.use_peft),
        "--peft_method", config.peft_method,
        "--train_texts", " ".join(train_texts),
        "--output_dir", config.output_dir
    ],
    compute_target=compute_target,
    environment=environment
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
hyperdrive_run = experiment.submit(hyperdrive_config)
hyperdrive_run.wait_for_completion(show_output=True)

# Get best run
best_run = hyperdrive_run.get_best_run_by_primary_metric()
best_run_metrics = best_run.get_metrics()
```

## Model Registration

### Register Model

```python
from azureml.core.model import Model

# Register model
model = Model.register(
    workspace=ws,
    model_path="./azure_mlops_output",
    model_name="fine-tuned-model",
    description="Fine-tuned model using Azure MLOps",
    tags={
        "model_type": "DialoGPT",
        "peft_method": "lora",
        "fine_tuning_date": "2024-01-01"
    }
)

print(f"Model registered: {model.name}, version: {model.version}")
```

### List Registered Models

```python
# List all models
models = Model.list(workspace=ws)
for model in models:
    print(f"Model: {model.name}, Version: {model.version}")

# Get specific model
model = Model(ws, name="fine-tuned-model", version=1)
```

## Model Deployment

### Deploy to ACI

```python
from azureml.core.webservice import AciWebservice
from azureml.core.model import InferenceConfig

# Define inference configuration
inference_config = InferenceConfig(
    entry_script="score.py",
    environment=environment
)

# Define deployment configuration
aci_config = AciWebservice.deploy_configuration(
    cpu_cores=1,
    memory_gb=2,
    description="Fine-tuned model service"
)

# Deploy model
service = Model.deploy(
    workspace=ws,
    name="fine-tuned-model-service",
    models=[model],
    inference_config=inference_config,
    deployment_config=aci_config
)

service.wait_for_deployment(show_output=True)
print(f"Service URL: {service.scoring_uri}")
```

### Deploy to AKS

```python
from azureml.core.webservice import AksWebservice

# Setup AKS compute
try:
    aks_target = ComputeTarget(workspace=ws, name="aks-cluster")
except:
    # Create AKS cluster
    from azureml.core.compute import AksCompute
    
    prov_config = AksCompute.provisioning_configuration(
        vm_size="Standard_DS3_v2",
        agent_count=1
    )
    
    aks_target = ComputeTarget.create(
        ws,
        "aks-cluster",
        prov_config
    )
    
    aks_target.wait_for_completion(show_output=True)

# Define deployment configuration
aks_config = AksWebservice.deploy_configuration(
    cpu_cores=1,
    memory_gb=2,
    autoscale_enabled=True,
    autoscale_min_replicas=1,
    autoscale_max_replicas=3,
    autoscale_target_utilization=70
)

# Deploy model
service = Model.deploy(
    workspace=ws,
    name="fine-tuned-model-service",
    models=[model],
    inference_config=inference_config,
    deployment_config=aks_config,
    deployment_target=aks_target
)

service.wait_for_deployment(show_output=True)
print(f"Service URL: {service.scoring_uri}")
```

### Scoring Script

```python
# score.py
import json
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def init():
    global model, tokenizer
    
    # Load model and tokenizer
    model_path = os.path.join(os.getenv("AZUREML_MODEL_DIR"), "model")
    model = AutoModelForCausalLM.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    # Set model to evaluation mode
    model.eval()

def run(raw_data):
    try:
        # Parse input
        data = json.loads(raw_data)
        prompt = data["prompt"]
        max_length = data.get("max_length", 100)
        
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=max_length,
                do_sample=True,
                top_p=0.95,
                temperature=0.7
            )
        
        # Decode output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return {"generated_text": generated_text}
    
    except Exception as e:
        return {"error": str(e)}
```

## Model Monitoring

### Enable Monitoring

```python
# Enable model data collection
service.update(enable_data_collection=True)

# Get telemetry data
telemetry_data = service.get_telemetry_data()
print(telemetry_data)
```

### Custom Monitoring

```python
# Log custom metrics
from azureml.core import Run

run = Run.get_context()
run.log("custom_metric", value)
run.log_row("custom_table", metric1=value1, metric2=value2)
```

## Best Practices

### Resource Management

1. **Compute Clusters**: Use appropriate VM sizes for your workload
2. **Auto-scaling**: Configure auto-scaling for cost optimization
3. **Idle Timeout**: Set appropriate idle timeout to save costs
4. **Resource Tags**: Use tags for resource organization and billing

### Experiment Organization

1. **Clear Naming**: Use descriptive names for experiments and runs
2. **Tags**: Use tags for categorization and filtering
3. **Notes**: Add detailed notes to experiments
4. **Comparisons**: Use Azure ML Studio for experiment comparison

### Model Management

1. **Versioning**: Always version your models
2. **Metadata**: Add comprehensive metadata and tags
3. **Documentation**: Document model purpose and usage
4. **Approval**: Use model approval workflows for production

### Security

1. **Authentication**: Use service principals for automation
2. **Network Security**: Configure network security groups
3. **Data Encryption**: Ensure data encryption at rest and in transit
4. **Access Control**: Use role-based access control (RBAC)

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Check service principal permissions
   - Verify workspace access
   - Ensure proper authentication configuration

2. **Compute Issues**
   - Check VM availability in your region
   - Verify quota limits
   - Monitor compute cluster status

3. **Deployment Issues**
   - Check model dependencies
   - Verify scoring script
   - Monitor service health

### Debugging Tips

```python
# Check workspace status
print(f"Workspace: {ws.name}")
print(f"Subscription: {ws.subscription_id}")
print(f"Resource Group: {ws.resource_group}")

# Check compute status
print(f"Compute Target: {compute_target.name}")
print(f"Compute Status: {compute_target.provisioning_state}")

# Check experiment status
print(f"Experiment: {experiment.name}")
print(f"Run Count: {len(experiment.get_runs())}")

# Check model status
print(f"Model: {model.name}")
print(f"Model Version: {model.version}")
print(f"Model Path: {model.download_target_path}")
```

## Examples

### Chatbot Fine-tuning
```python
config = AzureMLOpsConfig(
    model_name="microsoft/DialoGPT-medium",
    use_peft=True,
    peft_method="lora",
    experiment_name="chatbot-finetuning",
    model_name="chatbot-model",
    deployment_name="chatbot-service",
    deployment_type="aci"
)

trainer = AzureMLOpsFineTuner(config)
trainer.train(conversation_data)
trainer.register_model()
service = trainer.deploy_model("chatbot-model", 1)
```

### Code Generation
```python
config = AzureMLOpsConfig(
    model_name="bigcode/starcoder",
    use_peft=True,
    peft_method="qlora",
    load_in_4bit=True,
    experiment_name="code-generation-finetuning",
    model_name="code-model",
    deployment_name="code-service",
    deployment_type="aks"
)

trainer = AzureMLOpsFineTuner(config)
trainer.train(code_data)
trainer.register_model()
service = trainer.deploy_model("code-model", 1)
```

### Instruction Following
```python
config = AzureMLOpsConfig(
    model_name="meta-llama/Llama-2-7b-chat-hf",
    use_peft=True,
    peft_method="ia3",
    experiment_name="instruction-following-finetuning",
    model_name="instruction-model",
    deployment_name="instruction-service",
    deployment_type="aks"
)

trainer = AzureMLOpsFineTuner(config)
trainer.train(instruction_data)
trainer.register_model()
service = trainer.deploy_model("instruction-model", 1)
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

- [Azure Machine Learning Documentation](https://learn.microsoft.com/en-us/azure/machine-learning/)
- [Azure ML Python SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ml/?view=azure-ml-py)
- [MLflow Integration](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-mlflow-cli-runs)
- [Model Deployment](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-deploy-and-where)
- [Hyperparameter Tuning](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-tune-hyperparameters)
- [Azure ML Studio](https://ml.azure.com/)