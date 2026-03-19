# GCP MLOps Fine-Tuning Implementation

This directory contains a comprehensive implementation of fine-tuning using Google Cloud AI Platform services, including Vertex AI, experiment tracking, model training, deployment, and monitoring.

## Overview

Google Cloud AI Platform provides a complete managed service for machine learning, including Vertex AI for model training and deployment, experiment tracking, hyperparameter tuning, and model monitoring. This implementation demonstrates how to leverage GCP services for efficient fine-tuning workflows.

## Key Features

- **Vertex AI Training**: Managed training with automatic scaling and optimization
- **Hyperparameter Tuning**: Automated hyperparameter optimization with Bayesian optimization
- **Model Registry**: Centralized model versioning and approval workflows
- **Endpoint Deployment**: Easy deployment to scalable inference endpoints
- **Experiment Tracking**: Comprehensive experiment tracking with Vertex AI Experiments
- **Data Management**: Google Cloud Storage integration for data storage and versioning
- **Monitoring**: Built-in model monitoring and performance tracking

## Architecture

```
GCP MLOps Pipeline:
1. Setup GCP Services (GCS, Vertex AI, IAM)
2. Upload Data to Google Cloud Storage
3. Create Training Script and Custom Training Job
4. Train Model with Vertex AI
5. Hyperparameter Tuning (Optional)
6. Register Model in Vertex AI Model Registry
7. Deploy Model to Vertex AI Endpoint
8. Monitor and Manage Model Lifecycle
```

## Files

- `gcp_mlops_fine_tuning.py` - Main implementation with complete GCP MLOps pipeline
- `requirements.txt` - Dependencies for GCP MLOps
- `README.md` - This documentation file

## Quick Start

### Prerequisites

1. **Google Cloud Account**: You need an active Google Cloud account
2. **GCP Project**: A project with billing enabled
3. **IAM Permissions**: Vertex AI, Storage, and related service permissions
4. **Google Cloud SDK**: Installed and configured with your credentials
5. **Service Account**: IAM service account with necessary permissions

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from gcp_mlops_fine_tuning import GCPMLOpsFineTuner, GCPMLOpsConfig

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
    num_epochs=3,
    
    # Vertex AI training settings
    training_machine_type="n1-standard-4",
    accelerator_type="NVIDIA_TESLA_V100",
    accelerator_count=1,
    replica_count=1,
    boot_disk_size_gb=100,
    
    # GCS settings
    gcs_bucket="your-gcs-bucket",
    gcs_prefix="fine-tuning",
    
    # Model registration settings
    model_display_name="fine-tuned-model",
    model_description="Fine-tuned model using GCP Vertex AI",
    
    # Deployment settings
    endpoint_display_name="fine-tuned-model-endpoint",
    deployment_machine_type="n1-standard-2",
    min_replica_count=1,
    max_replica_count=3
)

# Initialize trainer
trainer = GCPMLOpsFineTuner(config)

# Prepare data
train_texts = ["Your training data here..."]
trainer.prepare_data(train_texts)

# Train model
model = trainer.train(train_texts)

# Register model
registered_model = trainer.register_model(model)

# Deploy model
endpoint, deployed_model = trainer.deploy_model(registered_model)
```

### Advanced Configuration

```python
config = GCPMLOpsConfig(
    # GCP Configuration
    project_id="your-project-id",
    region="us-central1",
    service_account_path="path/to/service-account.json",
    
    # Vertex AI Configuration
    vertex_ai_location="us-central1",
    vertex_ai_staging_bucket="gs://your-staging-bucket",
    
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
    
    # Vertex AI Training Configuration
    training_machine_type="n1-standard-4",  # CPU instance
    accelerator_type="NVIDIA_TESLA_V100",   # GPU accelerator
    accelerator_count=1,
    replica_count=1,
    boot_disk_size_gb=100,
    
    # GCS Configuration
    gcs_bucket="your-gcs-bucket",
    gcs_prefix="fine-tuning",
    
    # Experiment configuration
    experiment_name="fine-tuning-experiment",
    run_name="fine-tuning-run",
    
    # Model registration
    model_display_name="fine-tuned-model",
    model_description="Fine-tuned model using GCP Vertex AI",
    
    # Deployment configuration
    endpoint_display_name="fine-tuned-model-endpoint",
    deployed_model_display_name="fine-tuned-model-deployed",
    deployment_machine_type="n1-standard-2",
    min_replica_count=1,
    max_replica_count=3,
    
    # Advanced training settings
    gradient_accumulation_steps=1,
    max_grad_norm=1.0,
    use_gradient_checkpointing=True,
    use_mixed_precision=True,
    
    # Logging and saving
    save_steps=500,
    eval_steps=250,
    logging_steps=100,
    output_dir="./gcp_mlops_output",
    
    # Device configuration
    device="cuda" if torch.cuda.is_available() else "cpu"
)
```

## GCP Setup

### 1. Install Google Cloud SDK

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize SDK
gcloud init
```

### 2. Configure Authentication

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set project
gcloud config set project your-project-id

# Create service account
gcloud iam service-accounts create fine-tuning-sa \
    --display-name="Fine Tuning Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:fine-tuning-sa@your-project-id.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:fine-tuning-sa@your-project-id.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create key.json \
    --iam-account=fine-tuning-sa@your-project-id.iam.gserviceaccount.com
```

### 3. Setup Google Cloud Storage

```python
from google.cloud import storage

# Create GCS client
client = storage.Client(project="your-project-id")

# Create bucket
bucket = client.create_bucket("your-gcs-bucket")
print(f"Bucket {bucket.name} created")
```

### 4. Enable Required APIs

```bash
# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Vertex AI Training

### Custom Training Job

```python
from google.cloud import aiplatform

# Create custom training job
job = aiplatform.CustomTrainingJob(
    display_name="fine-tuning-job",
    script_path="train.py",
    container_uri="gcr.io/cloud-aiplatform/training/pytorch-gpu.1-13:latest",
    requirements=[
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "peft>=0.4.0"
    ],
    model_serving_container_image_uri="gcr.io/cloud-aiplatform/prediction/pytorch-gpu.1-13:latest"
)

# Start training
model = job.run(
    args=[
        "--model-name", "microsoft/DialoGPT-small",
        "--learning-rate", "2e-4",
        "--batch-size", "4",
        "--num-epochs", "3",
        "--use-peft", "True",
        "--peft-method", "lora",
        "--train", "gs://your-bucket/train-data.json"
    ],
    replica_count=1,
    machine_type="n1-standard-4",
    accelerator_type="NVIDIA_TESLA_V100",
    accelerator_count=1,
    staging_bucket="gs://your-staging-bucket"
)
```

### Hyperparameter Tuning

```python
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
    display_name="fine-tuning-hpo",
    custom_job_spec={
        'workerPoolSpecs': [{
            'machineSpec': {
                'machineType': 'n1-standard-4',
                'acceleratorType': 'NVIDIA_TESLA_V100',
                'acceleratorCount': 1
            },
            'replicaCount': 1,
            'containerSpec': {
                'imageUri': 'gcr.io/cloud-aiplatform/training/pytorch-gpu.1-13:latest',
                'command': ['python'],
                'args': ['train.py', '--train', 'gs://your-bucket/train-data.json']
            }
        }]
    },
    max_trial_count=20,
    parallel_trial_count=4,
    hyperparameter_spec=hp_spec,
    metrics_spec=metric_spec
)

# Start hyperparameter tuning
job.run()
```

## Model Registration

### Register Model

```python
# Register model
registered_model = model.register(
    display_name="fine-tuned-model",
    description="Fine-tuned DialoGPT model",
    labels={"fine-tuning-method": "lora"}
)

print(f"Model registered: {registered_model.resource_name}")
```

### Model Versioning

```python
# Create model version
versioned_model = registered_model.version_create(
    version_id="v1.0",
    display_name="Fine-tuned model v1.0",
    description="First version of fine-tuned model"
)

print(f"Model version created: {versioned_model.version_id}")
```

## Model Deployment

### Deploy to Endpoint

```python
# Create endpoint
endpoint = aiplatform.Endpoint.create(
    display_name="fine-tuned-model-endpoint"
)

# Deploy model
deployed_model = endpoint.deploy(
    model=registered_model,
    deployed_model_display_name="fine-tuned-model-deployed",
    machine_type="n1-standard-2",
    min_replica_count=1,
    max_replica_count=3
)

print(f"Model deployed to endpoint: {endpoint.resource_name}")
```

### Inference Script

```python
# inference.py
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
    
    return {'model': model, 'tokenizer': tokenizer}

def input_fn(request_body, request_content_type):
    """Parse input request."""
    if request_content_type == "application/json":
        input_data = json.loads(request_body)
        return input_data
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")

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
    
    return {"generated_text": generated_text}

def output_fn(prediction, response_content_type):
    """Format output response."""
    if response_content_type == "application/json":
        return json.dumps(prediction), response_content_type
    else:
        raise ValueError(f"Unsupported content type: {response_content_type}")
```

### Make Predictions

```python
# Make predictions
input_data = {
    "prompt": "Hello, how are you today?",
    "max_length": 100
}

response = endpoint.predict([input_data])
generated_text = response.predictions[0]["generated_text"]
print(f"Generated text: {generated_text}")
```

## Experiment Tracking

### Vertex AI Experiments

```python
import vertexai
from vertexai.preview import aiplatform as vertex_ai

# Initialize Vertex AI
vertexai.init(
    project="your-project-id",
    location="us-central1",
    staging_bucket="gs://your-staging-bucket"
)

# Create experiment
experiment = vertex_ai.Experiment.create(
    experiment_name="fine-tuning-experiment",
    description="Fine-tuning DialoGPT with LoRA"
)

# Create experiment run
with vertex_ai.start_run(run="lora-finetuning-run") as run:
    # Log parameters
    vertex_ai.log_params({
        "learning_rate": 2e-4,
        "batch_size": 4,
        "num_epochs": 3,
        "r": 8,
        "lora_alpha": 16
    })
    
    # Log metrics
    vertex_ai.log_metrics({
        "train_loss": 0.5,
        "eval_loss": 0.6,
        "perplexity": 1.8
    })
    
    # Log model
    vertex_ai.log_model(model, "fine-tuned-model")
```

## Model Monitoring

### Enable Model Monitoring

```python
# Setup data capture
data_capture_config = aiplatform.model_monitoring.ModelMonitoringConfig(
    enable_monitoring=True,
    sampling_rate=1.0,
    monitoring_interval=3600  # 1 hour
)

# Create monitoring job
monitoring_job = endpoint.create_model_monitoring_job(
    display_name="fine-tuned-model-monitoring",
    model_monitoring_objective_config=data_capture_config,
    alert_config=aiplatform.model_monitoring.EmailAlertConfig(
        email_addresses=["your-email@example.com"]
    )
)

print(f"Monitoring job created: {monitoring_job.name}")
```

## Best Practices

### Resource Management

1. **Machine Types**: Choose appropriate machine types for your workload
2. **Accelerators**: Use GPUs for training, CPUs for inference when possible
3. **Disk Size**: Set adequate disk size for model and data storage
4. **Auto Scaling**: Use auto scaling for endpoints based on traffic

### Cost Optimization

1. **Preemptible VMs**: Use preemptible VMs for training when possible
2. **Instance Sizing**: Right-size instances for your workload
3. **Data Storage**: Use appropriate GCS storage classes
4. **Endpoint Management**: Stop endpoints when not in use

### Security

1. **IAM Roles**: Use least privilege principle for IAM roles
2. **VPC**: Deploy endpoints in VPC for network security
3. **Encryption**: Enable encryption for data at rest and in transit
4. **Access Control**: Use IAM policies for access control

### Model Management

1. **Versioning**: Always version your models
2. **Approval Workflows**: Use approval workflows for production models
3. **Monitoring**: Monitor model performance and data drift
4. **Rollback**: Implement rollback mechanisms for failed deployments

## Troubleshooting

### Common Issues

1. **Permission Errors**
   - Check IAM role permissions
   - Verify GCS bucket access
   - Ensure service account has necessary permissions

2. **Training Failures**
   - Check machine type availability
   - Verify training script syntax
   - Monitor resource usage

3. **Deployment Issues**
   - Check model format and dependencies
   - Verify endpoint configuration
   - Monitor endpoint health

### Debugging Tips

```python
# Check training job status
training_job_name = model.resource_name
print(f"Training job: {training_job_name}")

# Check endpoint status
endpoint_name = endpoint.resource_name
print(f"Endpoint: {endpoint_name}")

# Check model artifacts
model_artifacts = model.uri
print(f"Model artifacts: {model_artifacts}")

# Check logs
import subprocess
subprocess.run(["gcloud", "ai-platform", "jobs", "stream-logs", training_job_name])
```

## Examples

### Chatbot Fine-tuning
```python
config = GCPMLOpsConfig(
    project_id="your-project-id",
    model_name="microsoft/DialoGPT-medium",
    use_peft=True,
    peft_method="lora",
    training_machine_type="n1-standard-4",
    accelerator_type="NVIDIA_TESLA_V100",
    deployment_machine_type="n1-standard-2",
    model_display_name="chatbot-model",
    endpoint_display_name="chatbot-endpoint"
)

trainer = GCPMLOpsFineTuner(config)
model = trainer.train(conversation_data)
registered_model = trainer.register_model(model)
endpoint, deployed_model = trainer.deploy_model(registered_model)
```

### Code Generation
```python
config = GCPMLOpsConfig(
    project_id="your-project-id",
    model_name="bigcode/starcoder",
    use_peft=True,
    peft_method="qlora",
    load_in_4bit=True,
    training_machine_type="n1-standard-8",
    accelerator_type="NVIDIA_A100",
    deployment_machine_type="n1-standard-8",
    model_display_name="code-model",
    endpoint_display_name="code-generation-endpoint"
)

trainer = GCPMLOpsFineTuner(config)
model = trainer.train(code_data)
registered_model = trainer.register_model(model)
endpoint, deployed_model = trainer.deploy_model(registered_model)
```

### Instruction Following
```python
config = GCPMLOpsConfig(
    project_id="your-project-id",
    model_name="meta-llama/Llama-2-7b-chat-hf",
    use_peft=True,
    peft_method="ia3",
    training_machine_type="n1-standard-16",
    accelerator_type="NVIDIA_A100",
    deployment_machine_type="n1-standard-16",
    model_display_name="instruction-model",
    endpoint_display_name="instruction-following-endpoint"
)

trainer = GCPMLOpsFineTuner(config)
model = trainer.train(instruction_data)
registered_model = trainer.register_model(model)
endpoint, deployed_model = trainer.deploy_model(registered_model)
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

- [Google Cloud AI Platform Documentation](https://cloud.google.com/ai-platform)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai)
- [Vertex AI Python SDK](https://googleapis.dev/python/aiplatform/latest/)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage)
- [Google Cloud SDK Documentation](https://cloud.google.com/sdk/docs)
- [Vertex AI Experiments](https://cloud.google.com/vertex-ai/docs/experiments)
- [Vertex AI Model Registry](https://cloud.google.com/vertex-ai/docs/model-registry)
