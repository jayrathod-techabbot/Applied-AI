# AWS MLOps Fine-Tuning Implementation

This directory contains a comprehensive implementation of fine-tuning using AWS SageMaker services, including experiment tracking, model training, deployment, and monitoring.

## Overview

AWS SageMaker provides a complete managed service for machine learning, including data labeling, model training, hyperparameter tuning, model deployment, and monitoring. This implementation demonstrates how to leverage SageMaker for efficient fine-tuning workflows.

## Key Features

- **SageMaker Training**: Managed training with automatic scaling and optimization
- **Hyperparameter Tuning**: Automated hyperparameter optimization with Bayesian optimization
- **Model Registry**: Centralized model versioning and approval workflows
- **Endpoint Deployment**: Easy deployment to scalable inference endpoints
- **Experiment Tracking**: Comprehensive experiment tracking with SageMaker Experiments
- **Data Management**: S3 integration for data storage and versioning
- **Monitoring**: Built-in model monitoring and performance tracking

## Architecture

```
AWS MLOps Pipeline:
1. Setup AWS Services (S3, SageMaker, IAM)
2. Upload Data to S3
3. Create Training Script and Estimator
4. Train Model with SageMaker
5. Hyperparameter Tuning (Optional)
6. Register Model in SageMaker Model Registry
7. Deploy Model to SageMaker Endpoint
8. Monitor and Manage Model Lifecycle
```

## Files

- `aws_mlops_fine_tuning.py` - Main implementation with complete AWS MLOps pipeline
- `requirements.txt` - Dependencies for AWS MLOps
- `README.md` - This documentation file

## Quick Start

### Prerequisites

1. **AWS Account**: You need an active AWS account
2. **IAM Permissions**: SageMaker, S3, and related service permissions
3. **AWS CLI**: Configured with your credentials
4. **SageMaker Role**: IAM role with SageMaker permissions

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from aws_mlops_fine_tuning import AWSMLOpsFineTuner, AWSMLOpsConfig

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
    num_epochs=3,
    
    # SageMaker settings
    instance_type="ml.g4dn.xlarge",
    instance_count=1,
    volume_size=30,
    max_run_time=3600,
    
    # Model registration settings
    model_package_group_name="fine-tuned-models",
    model_description="Fine-tuned model using AWS SageMaker",
    
    # Deployment settings
    endpoint_name="fine-tuned-model-endpoint",
    endpoint_instance_type="ml.m5.large",
    endpoint_initial_instance_count=1
)

# Initialize trainer
trainer = AWSMLOpsFineTuner(config)

# Prepare data
train_texts = ["Your training data here..."]
trainer.prepare_data(train_texts)

# Train model
estimator = trainer.train(train_texts)

# Register model
model_package_arn = trainer.register_model(estimator)

# Deploy model
predictor = trainer.deploy_model(estimator)
```

### Advanced Configuration

```python
config = AWSMLOpsConfig(
    # AWS Configuration
    aws_region="us-east-1",
    aws_profile=None,
    sagemaker_role="SageMakerRole",
    
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
    
    # SageMaker Configuration
    instance_type="ml.g4dn.xlarge",  # GPU instance
    instance_count=1,
    volume_size=30,  # GB
    max_run_time=3600,  # seconds
    
    # S3 Configuration
    s3_bucket=None,  # Will be auto-generated
    s3_prefix="fine-tuning",
    
    # Experiment configuration
    experiment_name="fine-tuning-experiment",
    trial_name="fine-tuning-trial",
    trial_component_display_name="fine-tuning-component",
    
    # Model registration
    model_package_group_name="fine-tuned-models",
    model_description="Fine-tuned model using AWS SageMaker",
    approval_status="PendingManualApproval",
    
    # Deployment configuration
    endpoint_name="fine-tuned-model-endpoint",
    endpoint_instance_type="ml.m5.large",
    endpoint_initial_instance_count=1,
    
    # Advanced training settings
    gradient_accumulation_steps=1,
    max_grad_norm=1.0,
    use_gradient_checkpointing=True,
    use_mixed_precision=True,
    
    # Logging and saving
    save_steps=500,
    eval_steps=250,
    logging_steps=100,
    output_dir="./aws_mlops_output",
    
    # Device configuration
    device="cuda" if torch.cuda.is_available() else "cpu"
)
```

## AWS Setup

### 1. Configure AWS CLI

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, region, and output format
```

### 2. Create SageMaker Role

```python
import sagemaker
from sagemaker import get_execution_role

# Get or create SageMaker execution role
role = get_execution_role()
print(f"SageMaker Role: {role}")
```

### 3. Setup S3 Bucket

```python
import boto3

s3 = boto3.client('s3')
bucket_name = "your-sagemaker-bucket"

# Create bucket if it doesn't exist
try:
    s3.head_bucket(Bucket=bucket_name)
    print(f"Using existing bucket: {bucket_name}")
except:
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': 'us-east-1'}
    )
    print(f"Created new bucket: {bucket_name}")
```

## SageMaker Training

### PyTorch Estimator

```python
from sagemaker.pytorch import PyTorch

# Create SageMaker estimator
estimator = PyTorch(
    entry_point='train.py',
    role=role,
    framework_version='2.0.0',
    py_version='py310',
    instance_count=1,
    instance_type='ml.g4dn.xlarge',
    volume_size=30,
    max_run=3600,
    hyperparameters={
        'model-name': 'microsoft/DialoGPT-small',
        'learning-rate': 2e-4,
        'batch-size': 4,
        'num-epochs': 3,
        'r': 8,
        'lora-alpha': 16,
        'use-peft': True,
        'peft-method': 'lora'
    }
)

# Start training
estimator.fit({'train': train_data_uri, 'eval': eval_data_uri})
```

### HuggingFace Estimator

```python
from sagemaker.huggingface import HuggingFace

# Create HuggingFace estimator
huggingface_estimator = HuggingFace(
    entry_point='train.py',
    source_dir='./scripts',
    instance_type='ml.g4dn.xlarge',
    instance_count=1,
    role=role,
    transformers_version='4.26',
    pytorch_version='1.13',
    py_version='py39',
    hyperparameters={
        'model-name': 'microsoft/DialoGPT-small',
        'learning-rate': 2e-4,
        'batch-size': 4,
        'num-epochs': 3,
        'r': 8,
        'lora-alpha': 16,
        'use-peft': True,
        'peft-method': 'lora'
    }
)

# Start training
huggingface_estimator.fit({'train': train_data_uri, 'eval': eval_data_uri})
```

## Hyperparameter Tuning

### Setup Hyperparameter Tuner

```python
from sagemaker.tuner import (
    HyperparameterTuner,
    IntegerParameter,
    CategoricalParameter,
    ContinuousParameter
)

# Define hyperparameter ranges
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

# Create hyperparameter tuner
tuner = HyperparameterTuner(
    estimator=estimator,
    objective_metric_name=objective_metric_name,
    hyperparameter_ranges=hyperparameter_ranges,
    objective_type=objective_type,
    max_jobs=20,
    max_parallel_jobs=4,
    base_tuning_job_name='fine-tuning-hpo'
)

# Start hyperparameter tuning
tuner.fit({'train': train_data_uri, 'eval': eval_data_uri})

# Get best training job
best_training_job = tuner.best_training_job()
print(f"Best training job: {best_training_job}")
```

## Model Registration

### Create Model Package Group

```python
import boto3

sagemaker_client = boto3.client('sagemaker')

# Create model package group
model_package_group_name = "fine-tuned-models"
try:
    sagemaker_client.describe_model_package_group(
        ModelPackageGroupName=model_package_group_name
    )
    print(f"Model package group exists: {model_package_group_name}")
except:
    sagemaker_client.create_model_package_group(
        ModelPackageGroupName=model_package_group_name,
        ModelPackageGroupDescription="Fine-tuned models for conversational AI"
    )
    print(f"Created model package group: {model_package_group_name}")
```

### Register Model

```python
# Create model metrics
from sagemaker.model_metrics import MetricsSource, ModelMetrics

model_metrics = ModelMetrics(
    model_statistics=MetricsSource(
        s3_uri=f"{estimator.model_data}/metrics.json",
        content_type="application/json"
    )
)

# Register model
model_package_arn = sagemaker_client.create_model_package(
    ModelPackageGroupName=model_package_group_name,
    ModelPackageDescription="Fine-tuned DialoGPT model",
    ModelApprovalStatus="PendingManualApproval",
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

print(f"Model registered: {model_package_arn}")
```

## Model Deployment

### Deploy to SageMaker Endpoint

```python
from sagemaker.model import Model
from sagemaker.predictor import Predictor
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer

# Create SageMaker model
model = Model(
    model_data=estimator.model_data,
    image_uri=estimator.image_uri,
    role=role,
    entry_point='inference.py',
    name='fine-tuned-model'
)

# Deploy model
predictor = model.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.large',
    endpoint_name='fine-tuned-model-endpoint'
)

print(f"Model deployed to endpoint: {predictor.endpoint_name}")
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

response = predictor.predict(input_data)
generated_text = response["generated_text"]
print(f"Generated text: {generated_text}")
```

## Experiment Tracking

### SageMaker Experiments

```python
import sagemaker
from sagemaker.experiments import Experiment, Trial, TrialComponent

# Create experiment
experiment = Experiment.create(
    experiment_name="fine-tuning-experiment",
    description="Fine-tuning DialoGPT with LoRA"
)

# Create trial
trial = Trial.create(
    trial_name="lora-finetuning-trial",
    experiment_name=experiment.experiment_name
)

# Create trial component
trial_component = TrialComponent.create(
    trial_component_name="fine-tuning-component",
    display_name="Fine-tuning with LoRA",
    parameters={
        "learning_rate": 2e-4,
        "batch_size": 4,
        "num_epochs": 3,
        "r": 8,
        "lora_alpha": 16
    },
    metrics=[
        {"MetricName": "train_loss", "Value": 0.5},
        {"MetricName": "eval_loss", "Value": 0.6},
        {"MetricName": "perplexity", "Value": 1.8}
    ]
)

# Associate trial component with trial
trial.add_trial_component(trial_component)

print(f"Experiment: {experiment.experiment_name}")
print(f"Trial: {trial.trial_name}")
print(f"Trial Component: {trial_component.trial_component_name}")
```

## Model Monitoring

### Enable Model Monitoring

```python
from sagemaker.model_monitor import DataCaptureConfig, ModelMonitor, DefaultModelMonitor

# Setup data capture
data_capture_config = DataCaptureConfig(
    enable_capture=True,
    sampling_percentage=100,
    destination_s3_uri=f"s3://{bucket_name}/data-capture"
)

# Create model monitor
model_monitor = DefaultModelMonitor(
    role=role,
    instance_count=1,
    instance_type='ml.m5.large',
    volume_size_in_gb=20,
    max_runtime_in_seconds=1800
)

# Schedule monitoring
monitoring_schedule = model_monitor.create_monitoring_schedule(
    monitor_schedule_name='fine-tuned-model-monitor',
    endpoint_input=predictor.endpoint,
    statistics=model_monitor.baseline_statistics(),
    constraints=model_monitor.suggested_constraints(),
    schedule_cron_expression='cron(0 2 ? * * *)',  # Daily at 2 AM
    enable_cloudwatch_metrics=True
)

print(f"Monitoring schedule created: {monitoring_schedule.monitoring_schedule_name}")
```

## Best Practices

### Resource Management

1. **Instance Types**: Choose appropriate instance types for your workload
2. **Volume Size**: Set adequate volume size for model and data storage
3. **Max Run Time**: Set reasonable max run time to avoid timeouts
4. **Auto Scaling**: Use auto scaling for endpoints based on traffic

### Cost Optimization

1. **Spot Instances**: Use spot instances for training when possible
2. **Instance Sizing**: Right-size instances for your workload
3. **Data Storage**: Use appropriate S3 storage classes
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
   - Verify S3 bucket access
   - Ensure SageMaker service role is correct

2. **Training Failures**
   - Check instance type availability
   - Verify training script syntax
   - Monitor resource usage

3. **Deployment Issues**
   - Check model format and dependencies
   - Verify endpoint configuration
   - Monitor endpoint health

### Debugging Tips

```python
# Check training job status
training_job_name = estimator.latest_training_job.name
print(f"Training job: {training_job_name}")

# Check endpoint status
endpoint_name = predictor.endpoint_name
print(f"Endpoint: {endpoint_name}")

# Check model data location
model_data = estimator.model_data
print(f"Model data: {model_data}")

# Check logs
import boto3
cloudwatch = boto3.client('logs')
# Use CloudWatch logs for debugging
```

## Examples

### Chatbot Fine-tuning
```python
config = AWSMLOpsConfig(
    model_name="microsoft/DialoGPT-medium",
    use_peft=True,
    peft_method="lora",
    instance_type="ml.g4dn.xlarge",
    endpoint_instance_type="ml.m5.large",
    model_package_group_name="chatbot-models",
    endpoint_name="chatbot-endpoint"
)

trainer = AWSMLOpsFineTuner(config)
estimator = trainer.train(conversation_data)
model_package_arn = trainer.register_model(estimator)
predictor = trainer.deploy_model(estimator)
```

### Code Generation
```python
config = AWSMLOpsConfig(
    model_name="bigcode/starcoder",
    use_peft=True,
    peft_method="qlora",
    load_in_4bit=True,
    instance_type="ml.g5.xlarge",
    endpoint_instance_type="ml.g5.xlarge",
    model_package_group_name="code-models",
    endpoint_name="code-generation-endpoint"
)

trainer = AWSMLOpsFineTuner(config)
estimator = trainer.train(code_data)
model_package_arn = trainer.register_model(estimator)
predictor = trainer.deploy_model(estimator)
```

### Instruction Following
```python
config = AWSMLOpsConfig(
    model_name="meta-llama/Llama-2-7b-chat-hf",
    use_peft=True,
    peft_method="ia3",
    instance_type="ml.g5.2xlarge",
    endpoint_instance_type="ml.g5.2xlarge",
    model_package_group_name="instruction-models",
    endpoint_name="instruction-following-endpoint"
)

trainer = AWSMLOpsFineTuner(config)
estimator = trainer.train(instruction_data)
model_package_arn = trainer.register_model(estimator)
predictor = trainer.deploy_model(estimator)
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

- [AWS SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [SageMaker Python SDK](https://sagemaker.readthedocs.io/)
- [SageMaker Experiments](https://docs.aws.amazon.com/sagemaker/latest/dg/experiments.html)
- [SageMaker Model Registry](https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html)
- [SageMaker Hyperparameter Tuning](https://docs.aws.amazon.com/sagemaker/latest/dg/automatic-model-tuning.html)
- [AWS CLI Documentation](https://docs.aws.amazon.com/cli/latest/)