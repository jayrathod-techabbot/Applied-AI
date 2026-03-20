# Infrastructure Setup - Concepts

## Table of Contents
1. [Cloud Provider Overview](#cloud-provider-overview)
2. [Azure OpenAI Setup](#azure-openai-setup)
3. [AWS Setup](#aws-setup)
4. [GCP Setup](#gcp-setup)
5. [Self-Hosted Infrastructure](#self-hosted-infrastructure)
6. [Kubernetes Setup](#kubernetes-setup)
7. [Infrastructure as Code](#infrastructure-as-code)

---

## Cloud Provider Overview

### Comparison of LLM Cloud Services

| Provider | Service | Key Features | Pricing |
|----------|---------|--------------|---------|
| **Azure** | OpenAI Service | Enterprise SLA, private endpoints, content safety | Per-token |
| **AWS** | Bedrock | Model variety, agents, knowledge bases | Per-token |
| **GCP** | Vertex AI | Model Garden, grounding, tuning | Per-token |
| **AWS** | SageMaker | End-to-end ML, JumpStart | Compute + per-token |

---

## Azure OpenAI Setup

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                Azure OpenAI Architecture                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Your Application                                               │
│   ┌─────────────┐                                               │
│   │ FastAPI/    │                                               │
│   │ Flask/Django│                                               │
│   └──────┬──────┘                                               │
│          │                                                        │
│          │ Private Endpoint (vNet)                               │
│          ▼                                                        │
│   ┌─────────────────────────────────────────┐                  │
│   │         Azure Virtual Network            │                  │
│   │  ┌─────────────────────────────────┐    │                  │
│   │  │    Private Endpoint             │    │                  │
│   │  │    (Azure OpenAI)               │    │                  │
│   │  └─────────────────────────────────┘    │                  │
│   └────────────────┬────────────────────────┘                  │
│                    │                                              │
│           ┌────────┴────────┐                                     │
│           ▼                 ▼                                     │
│   ┌─────────────┐   ┌─────────────┐                              │
│   │ GPT-4       │   │ GPT-3.5    │                              │
│   │ Deployment  │   │ Deployment  │                              │
│   └─────────────┘   └─────────────┘                              │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Azure AI Content Safety (Optional)                     │   │
│   │  - Content filtering                                    │   │
│   │  - Moderation                                            │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Setup

#### 1. Create Azure OpenAI Resource

```bash
# Azure CLI commands to create OpenAI resource
az group create --name rg-llmops --location eastus

az cognitiveservices account create \
    --name aoai-llmops \
    --resource-group rg-llmops \
    --kind OpenAI \
    --sku S0 \
    --location eastus

# Get the endpoint
az cognitiveservices account show \
    --name aoai-llmops \
    --resource-group rg-llmops \
    --query properties.endpoint
```

#### 2. Deploy Models

```bash
# Deploy GPT-4
az cognitiveservices account deployment create \
    --name aoai-llmops \
    --resource-group rg-llmops \
    --deployment-name gpt-4 \
    --model-name gpt-4 \
    --model-version "0125" \
    --sku-capacity 10 \
    --sku-name "Standard"

# Deploy GPT-3.5 Turbo
az cognitiveservices account deployment create \
    --name aoai-llmops \
    --resource-group rg-llmops \
    --deployment-name gpt-35-turbo \
    --model-name gpt-35-turbo \
    --model-version "0125" \
    --sku-capacity 120 \
    --sku-name "Standard"
```

#### 3. Configure Network Security

```json
// azuredeploy.parameters.json
{
    "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
    "contentVersion": "1.0.0.0",
    "parameters": {
        "networkAcls": {
            "value": {
                "defaultAction": "Deny",
                "ipRules": [],
                "virtualNetworkRules": [
                    {
                        "id": "/subscriptions/{sub-id}/resourceGroups/rg-llmops/providers/Microsoft.Network/virtualNetworks/vnet-llmops/subnets/default",
                        "action": "Allow"
                    }
                ]
            }
        }
    }
}
```

### Python Client Configuration

```python
# azure_openai_client.py
from openai import AzureOpenAI
import os

class AzureOpenAIClient:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-01",
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
        )
    
    def chat_completion(
        self,
        messages: list,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response
    
    def chat_completion_with_streaming(self, messages: list, model: str = "gpt-4"):
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )

# Usage
client = AzureOpenAIClient()
response = client.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

---

## AWS Setup

### AWS Bedrock Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   AWS Bedrock Architecture                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │                    VPC (Your Account)                      │ │
│   │                                                           │ │
│   │  ┌─────────────┐     ┌─────────────┐                      │ │
│   │  │ EC2/Lambda │     │   ECS/EKS   │                      │ │
│   │  │  (App)     │     │   (App)     │                      │ │
│   │  └──────┬──────┘     └──────┬──────┘                      │ │
│   │         │                   │                              │ │
│   │         └─────────┬─────────┘                              │ │
│   │                   │                                         │ │
│   └───────────────────┼─────────────────────────────────────────┘ │
│                       │ VPC Endpoint                                │
│                       ▼                                            │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │                  AWS Bedrock                               │ │
│   │                                                           │ │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │ │
│   │  │ Claude    │  │  GPT-4   │  │  Titan   │                 │ │
│   │  │ (Anthropic)│ │(AI21)   │  │(Amazon)  │                 │ │
│   │  └──────────┘  └──────────┘  └──────────┘                 │ │
│   │                                                           │ │
│   │  ┌──────────────────────────────────────────────────┐   │ │
│   │  │              Knowledge Bases (RAG)                 │   │ │
│   │  │  - Vector Store (OpenSearch, Pinecone)            │   │ │
│   │  │  - Document Chunking                              │   │ │
│   │  │  - Context Retrieval                              │   │ │
│   │  └──────────────────────────────────────────────────┘   │ │
│   │                                                           │ │
│   │  ┌──────────────────────────────────────────────────┐   │ │
│   │  │              Agents (Action Execution)            │   │ │
│   │  │  - Function Definition                           │   │ │
│   │  │  - Tool Execution                                 │   │ │
│   │  └──────────────────────────────────────────────────┘   │ │
│   └──────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### AWS Bedrock Setup

#### 1. Enable Bedrock Models

```bash
# Using AWS CLI
aws bedrock get-foundation-model-model \
    --model-provider anthropic \
    --model-id anthropic.claude-3-sonnet-20240229-v1:0

# List available models
aws bedrock list-foundation-models \
    --region us-east-1
```

#### 2. Create VPC Endpoint for Bedrock

```bash
# Create VPC endpoint for Bedrock
aws ec2 create-vpc-endpoint \
    --vpc-id vpc-xxxxx \
    --vpc-endpoint-type Interface \
    --service-name com.amazonaws.us-east-1.bedrock-runtime \
    --subnet-ids subnet-xxxxx \
    --security-group-ids sg-xxxxx
```

#### 3. Python Client Configuration

```python
# aws_bedrock_client.py
import boto3
import json
import os

class BedrockClient:
    def __init__(self, region: str = "us-east-1"):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region
        )
    
    def invoke_claude(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ):
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature
        }
        
        response = self.client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )
        
        return json.loads(response["body"].read())
    
    def invoke_with_guardrails(self, prompt: str):
        # Using Bedrock Guardrails
        response = self.client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            guardrailIdentifier="guardrail-xxxxx",
            guardrailVersion="v1",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024
            })
        )
        return response

# Usage
client = BedrockClient()
response = client.invoke_claude("Explain quantum computing in simple terms")
print(response["content"][0]["text"])
```

### AWS SageMaker Setup for Self-Hosted Models

```python
# sageMaker_deployment.py
import boto3
import sagemaker
from sagemaker.huggingface import HuggingFaceModel

def deploy_to_sagemaker(
    model_id: str = "meta-llama/Llama-2-7b-hf",
    instance_type: str = "ml.g5.2xlarge",
    instance_count: int = 1
):
    sess = sagemaker.Session()
    
    # Create HuggingFace model
    huggingface_model = HuggingFaceModel(
        model_data=f"s3://{sess.default_bucket()}/llm-models/{model_id}/model.tar.gz",
        role=sess.get_execution_role(),
        transformers_version="4.28.0",
        pytorch_version="2.0.0",
        py_version="py310",
        env={
            "HF_MODEL_ID": model_id,
            "HF_TASK": "text-generation",
            "MAX_INPUT_LENGTH": "4096",
            "MAX_TOTAL_TOKENS": "4096"
        }
    )
    
    # Deploy
    predictor = huggingface_model.deploy(
        initial_instance_count=instance_count,
        instance_type=instance_type,
        endpoint_name="llama2-7b-endpoint"
    )
    
    return predictor
```

---

## GCP Setup

### Vertex AI Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Google Vertex AI Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │                  Your Application                         │ │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│   │  │ Cloud Run  │  │  GKE       │  │  Compute   │        │ │
│   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │ │
│   └─────────┼─────────────────┼─────────────────┼──────────────┘ │
│             │                 │                 │               │
│             └─────────────────┼─────────────────┘               │
│                               │                                  │
│                               ▼                                  │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │               Vertex AI API                               │ │
│   │                                                           │ │
│   │  ┌─────────────────────────────────────────────────────┐ │ │
│   │  │            Model Garden                              │ │ │
│   │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │ │ │
│   │  │  │ PaLM 2   │  │  Gemini  │  │  Claude  │            │ │ │
│   │  │  └──────────┘  └──────────┘  └──────────┘            │ │ │
│   │  └─────────────────────────────────────────────────────┘ │ │
│   │                                                           │ │
│   │  ┌─────────────────────────────────────────────────────┐ │ │
│   │  │            Matching Engine (Vector Search)          │ │ │
│   │  └─────────────────────────────────────────────────────┘ │ │
│   │                                                           │ │
│   │  ┌─────────────────────────────────────────────────────┐ │ │
│   │  │            Grounding (Search/RAG)                    │ │ │
│   │  └─────────────────────────────────────────────────────┘ │ │
│   └──────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### GCP Vertex AI Setup

```python
# vertex_ai_client.py
from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel

def initialize_vertex_ai(project_id: str, location: str = "us-central1"):
    vertexai.init(project=project_id, location=location)

def generate_text(
    prompt: str,
    model_name: str = "gemini-1.5-pro-preview-0409",
    temperature: float = 0.7,
    max_output_tokens: int = 2048
):
    model = GenerativeModel(model_name)
    
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "top_p": 0.95,
            "top_k": 40
        }
    )
    
    return response.text

# Usage
initialize_vertex_ai("your-project-id")
result = generate_text("What is machine learning?")
print(result)
```

---

## Self-Hosted Infrastructure

### GPU Requirements

| Model Size | FP16 VRAM | INT8 VRAM | INT4 VRAM | Recommended GPU |
|------------|-----------|-----------|-----------|-----------------|
| 7B | 14 GB | 7 GB | 3.5 GB | A10G, T4, L4 |
| 13B | 26 GB | 13 GB | 6.5 GB | A100 40GB |
| 34B | 68 GB | 34 GB | 17 GB | A100 80GB x2 |
| 70B | 140 GB | 70 GB | 35 GB | A100 80GB x4 |

### Self-Hosted Setup with vLLM

```dockerfile
# Dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app

# Install vLLM
RUN pip install vllm>=0.3.0

# Copy model files (or download at runtime)
# COPY models /models

# Expose API port
EXPOSE 8000

# Run vLLM server
CMD ["--host", "0.0.0.0", "--port", "8000", "--model", "meta-llama/Llama-2-7b-hf"]
```

```bash
# docker-compose.yml
version: '3.8'

services:
  vllm:
    build: .
    ports:
      - "8000:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - VLLM_WORKER_MULTIPROC_MODULE=vllm.worker.multiprocessing.gpu
      - VLLM_TENSOR_PARALLEL_SIZE=1
    volumes:
      - ./models:/models
    restart: unless-stopped
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-inference
  labels:
    app: vllm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: vllm
  template:
    metadata:
      labels:
        app: vllm
    spec:
      containers:
      - name: vllm
        image: vllm/vllm:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            nvidia.com/gpu: 1
            memory: "16Gi"
            cpu: "4"
          limits:
            nvidia.com/gpu: 1
            memory: "32Gi"
            cpu: "8"
        env:
        - name: VLLM_MODEL
          value: "meta-llama/Llama-2-7b-hf"
        - name: VLLM_TENSOR_PARALLEL_SIZE
          value: "1"
        - name: VLLM_MAX_NUM_BATCHED_TOKENS
          value: "4096"
        volumeMounts:
        - name: model-cache
          mountPath: /root/.cache/huggingface
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc
      nodeSelector:
        gpu: "true"
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-service
spec:
  selector:
    app: vllm
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

---

## Infrastructure as Code

### Terraform for Azure OpenAI

```hcl
# main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

resource "azurerm_resource_group" "llmops" {
  name     = "rg-llmops"
  location = var.location
}

resource "azurerm_cognitive_account" "openai" {
  name                = "aoai-llmops-${var.environment}"
  location            = azurerm_resource_group.llmops.location
  resource_group_name = azurerm_resource_group.llmops.name
  kind                = "OpenAI"
  sku_name            = "S0"
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

resource "azurerm_cognitive_deployment" "gpt4" {
  name                 = "gpt-4"
  cognitive_account_id = azurerm_cognitive_account.openai.id
  model {
    format  = "OpenAI"
    name    = "gpt-4"
    version = "0125"
  }
  scale {
    type = "Standard"
    capacity = var.gpt4_capacity
  }
}

resource "azurerm_cognitive_deployment" "gpt35" {
  name                 = "gpt-35-turbo"
  cognitive_account_id = azurerm_cognitive_account.openai.id
  model {
    format  = "OpenAI"
    name    = "gpt-35-turbo"
    version = "0125"
  }
  scale {
    type = "Standard"
    capacity = var.gpt35_capacity
  }
}

# Variables
variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
}

variable "location" {
  description = "Azure Region"
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "gpt4_capacity" {
  description = "GPT-4 deployment capacity"
  type        = number
  default     = 10
}

variable "gpt35_capacity" {
  description = "GPT-3.5 Turbo deployment capacity"
  type        = number
  default     = 120
}

variable "tags" {
  description = "Tags for resources"
  type        = map(string)
  default     = {}
}
```

### Terraform for AWS Bedrock

```hcl
# main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# VPC for private access to Bedrock
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "llmops-vpc"
  }
}

# Subnet for Bedrock VPC Endpoint
resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.region}a"
  map_public_ip_on_launch = false
  
  tags = {
    Name = "llmops-private-subnet"
  }
}

# Security Group
resource "aws_security_group" "llmops" {
  name        = "llmops-sg"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }
  
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# VPC Endpoint for Bedrock Runtime
resource "aws_vpc_endpoint" "bedrock" {
  vpc_id             = aws_vpc.main.id
  service_name       = "com.amazonaws.${var.region}.bedrock-runtime"
  vpc_endpoint_type  = "Interface"
  
  subnet_ids          = [aws_subnet.private.id]
  security_group_ids  = [aws_security_group.llmops.id]
  
  tags = {
    Name = "bedrock-vpce"
  }
}

# IAM Role for Bedrock access
resource "aws_iam_role" "bedrock_access" {
  name = "llmops-bedrock-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "bedrock_access" {
  role       = aws_iam_role.bedrock_access.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
}
```

---

## Best Practices

### Security Checklist

- [ ] Use Private Endpoints (VPC)
- [ ] Enable TLS 1.2+
- [ ] Implement RBAC for access control
- [ ] Rotate API keys regularly
- [ ] Enable audit logging
- [ ] Use customer-managed keys (CMK) for encryption
- [ ] Configure network ACLs
- [ ] Enable Azure/AWS Defender for Cloud

### Cost Optimization

- [ ] Start with lower capacity, scale as needed
- [ ] Use auto-scaling to match demand
- [ ] Implement caching for repeated queries
- [ ] Choose the right model for each use case
- [ ] Set up budget alerts
- [ ] Use reserved capacity for predictable workloads

### Performance Optimization

- [ ] Enable connection pooling
- [ ] Use async API calls where possible
- [ ] Implement request batching
- [ ] Configure appropriate timeouts
- [ ] Use streaming for long responses
- [ ] Enable response caching
