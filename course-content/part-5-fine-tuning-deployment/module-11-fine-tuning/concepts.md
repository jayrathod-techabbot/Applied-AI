# Module 11: Fine-Tuning LLMs — Core Concepts

## Table of Contents
- [11.1 When and Why to Fine-Tune vs. Prompt Engineering](#111-when-and-why-to-fine-tune-vs-prompt-engineering)
- [11.2 Fine-Tuning Techniques: LoRA, QLoRA, PEFT](#112-fine-tuning-techniques-lora-qlora-peft)
- [11.3 Fine-Tuning Implementation Walkthrough](#113-fine-tuning-implementation-walkthrough)

---

## 11.1 When and Why to Fine-Tune vs. Prompt Engineering

Fine-tuning is the process of continuing to train a pre-trained model on a domain-specific or task-specific dataset so that it adapts its weights to your use case. Before committing to fine-tuning, it is critical to evaluate whether prompt engineering or RAG can solve the problem first.

### Comparison: Fine-Tuning vs Prompt Engineering vs RAG

| Criterion | Prompt Engineering | RAG | Fine-Tuning |
|-----------|-------------------|-----|-------------|
| **Setup effort** | Low | Medium | High |
| **Data required** | None (examples in prompt) | Documents / knowledge base | Labeled training dataset (hundreds–thousands) |
| **Cost** | API cost only | API + vector DB cost | Training compute + inference cost |
| **Latency impact** | Slight (longer prompts) | Higher (retrieval step) | Lower (shorter prompts, specialized model) |
| **Knowledge update** | Instant (change prompt) | Instant (update index) | Requires retraining |
| **Output consistency** | Variable | Variable | High |
| **Domain adaptation** | Shallow | Retrieval-based | Deep (weight-level) |
| **Best for** | Quick prototyping, general tasks | Dynamic knowledge, FAQs | Tone, format, domain expertise |

### Decision Framework: When to Fine-Tune

| Signal | Action |
|--------|--------|
| Prompt engineering gives inconsistent results | Try few-shot / chain-of-thought first |
| Model needs external knowledge at runtime | Use RAG |
| Model must adopt a specific tone or output format consistently | Fine-tune |
| Domain has specialized vocabulary the base model lacks | Fine-tune |
| You need to reduce prompt token usage and cost | Fine-tune |
| Data changes frequently (daily/weekly) | RAG (fine-tuning is too slow) |
| You have < 50 labeled examples | Prompt engineering or few-shot |
| You have 500+ high-quality labeled examples | Fine-tune |

### Data Preparation

High-quality data is the single most important factor in fine-tuning success.

#### Data Format

Most fine-tuning frameworks expect JSONL format:

```jsonl
{"messages": [{"role": "system", "content": "You are a medical assistant."}, {"role": "user", "content": "What are symptoms of diabetes?"}, {"role": "assistant", "content": "Common symptoms include increased thirst, frequent urination, unexplained weight loss, fatigue, and blurred vision."}]}
{"messages": [{"role": "system", "content": "You are a medical assistant."}, {"role": "user", "content": "How is hypertension diagnosed?"}, {"role": "assistant", "content": "Hypertension is diagnosed when blood pressure readings consistently measure 130/80 mmHg or higher on two or more occasions."}]}
```

#### Data Quality Checklist

| Factor | Guideline |
|--------|-----------|
| **Accuracy** | All labels/outputs must be correct — garbage in, garbage out |
| **Consistency** | Same input patterns should produce consistent outputs |
| **Diversity** | Cover edge cases, varied phrasing, different difficulty levels |
| **Balance** | Avoid over-representing one class or output style |
| **Size** | 100–10,000 examples typically; quality > quantity |
| **Format** | Match the inference-time prompt format exactly |

### Instruction Tuning and SFT (Supervised Fine-Tuning)

**Instruction Tuning** trains the model to follow instructions by presenting input-output pairs where the output is a high-quality response to an instruction.

**SFT (Supervised Fine-Tuning)** is the first stage of RLHF (Reinforcement Learning from Human Feedback). A human-written or curated dataset of prompt-response pairs is used to teach the model desired behavior before reward model training.

```python
# SFT dataset example (Hugging Face format)
dataset = [
    {
        "instruction": "Summarize the following article in 2 sentences.",
        "input": "Large language models have transformed NLP by...",
        "output": "Large language models revolutionized NLP through pre-training on massive corpora. Fine-tuning techniques like LoRA enable efficient domain adaptation."
    },
    {
        "instruction": "Convert this sentence to passive voice.",
        "input": "The researcher published the paper.",
        "output": "The paper was published by the researcher."
    }
]
```

### Training Hyperparameters

| Hyperparameter | Typical Range | Effect |
|---------------|---------------|--------|
| **Learning Rate** | 1e-5 to 5e-4 | Too high → divergence; too low → slow convergence |
| **Epochs** | 1–5 | More epochs → risk of overfitting on small datasets |
| **Batch Size** | 1–16 (limited by GPU memory) | Larger → more stable gradients; smaller → more updates |
| **Warmup Steps** | 10–10% of total steps | Prevents early training instability |
| **Max Seq Length** | 512–4096 | Must cover your longest input+output |
| **Weight Decay** | 0.01–0.1 | Regularization to prevent overfitting |
| **LoRA Rank (r)** | 8–64 | Higher → more capacity, more memory |
| **LoRA Alpha** | 16–128 (typically 2× rank) | Scaling factor for LoRA updates |

### Evaluation Metrics

| Metric | Use Case |
|--------|----------|
| **Loss** | General training progress |
| **Perplexity** | Language modeling quality (lower = better) |
| **Accuracy** | Classification tasks |
| **F1 Score** | Imbalanced classification |
| **BLEU / ROUGE** | Text generation quality vs reference |
| **Human evaluation** | Tone, factual accuracy, helpfulness |
| **Task-specific metrics** | Exact match, pass@k for code |

### Cost Considerations

| Approach | Cost Level | Notes |
|----------|-----------|-------|
| Prompt engineering | $ | Per-token API cost only |
| RAG | $$ | API cost + vector DB hosting |
| LoRA fine-tuning | $$–$$$ | Moderate GPU hours; small adapter files |
| Full fine-tuning | $$$$ | High GPU memory and compute required |
| Azure OpenAI fine-tuning | $$ | Pay per training token + inference token |

**Cost optimization tips:**
- Start with prompt engineering and RAG before fine-tuning
- Use LoRA/QLoRA instead of full fine-tuning to reduce GPU requirements by 60–75%
- Fine-tune smaller models (7B) before larger ones (70B)
- Use cloud spot instances for training
- Cache inference results for repeated queries

---

## 11.2 Fine-Tuning Techniques: LoRA, QLoRA, PEFT

### Full Fine-Tuning

Full fine-tuning updates **all parameters** of the pre-trained model. For a 7B parameter model, this means updating 7 billion weights, requiring massive GPU memory (typically 4× model size in GB for Adam optimizer states).

```
Model: 7B params × 4 bytes (FP32) = 28 GB just for weights
Optimizer states (Adam): 2 × 28 GB = 56 GB
Gradients: 28 GB
Activations: variable
Total: ~120+ GB GPU memory
```

This is impractical for most teams. Enter parameter-efficient methods.

### PEFT (Parameter-Efficient Fine-Tuning)

PEFT is an umbrella category of techniques that freeze most model parameters and only train a small subset. Benefits:

- **Memory efficient**: Train on consumer GPUs (24 GB)
- **Storage efficient**: Save only small adapter weights (MBs vs GBs)
- **No catastrophic forgetting**: Base weights are frozen
- **Composable**: Swap adapters for different tasks

PEFT methods include: LoRA, AdaLoRA, Prefix Tuning, Prompt Tuning, IA3, and more.

### LoRA (Low-Rank Adaptation)

LoRA freezes all original model weights and injects trainable low-rank decomposition matrices into each layer's attention projections.

#### Theory

For a pre-trained weight matrix $W_0 \in \mathbb{R}^{d \times k}$, LoRA adds a low-rank update:

$$W = W_0 + \Delta W = W_0 + BA$$

Where:
- $B \in \mathbb{R}^{d \times r}$ (down-projection)
- $A \in \mathbb{R}^{r \times k}$ (up-projection)
- $r \ll \min(d, k)$ — the rank (e.g., 16 or 32)
- $\Delta W$ is scaled by $\frac{\alpha}{r}$ where $\alpha$ is a hyperparameter

```
Original:  W (d × k)        → d × k parameters
LoRA:      B (d × r) + A (r × k) → d × r + r × k parameters

Example for d=4096, k=4096, r=16:
  Full:    4096 × 4096 = 16,777,216 params
  LoRA:    4096 × 16 + 16 × 4096 = 131,072 params
  Reduction: 128× fewer parameters
```

#### Code: LoRA with Hugging Face PEFT

```python
from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoModelForCausalLM

# Load base model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    load_in_4bit=True,          # 4-bit quantization for memory savings
    device_map="auto"
)

# Configure LoRA
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,                        # Rank of the low-rank matrices
    lora_alpha=32,               # Scaling factor (typically 2× rank)
    lora_dropout=0.05,           # Dropout on LoRA layers
    target_modules=[             # Which layers to apply LoRA to
        "q_proj", "v_proj",      # Query and Value projections
        "k_proj", "o_proj",      # Key and Output projections
        "gate_proj", "up_proj", "down_proj"  # MLP layers
    ],
    bias="none"
)

# Wrap model with LoRA adapters
model = get_peft_model(model, lora_config)

# Check trainable parameters
model.print_trainable_parameters()
# Output: trainable params: 4,194,304 || all params: 6,742,609,920 || trainable%: 0.0622
```

### QLoRA (Quantized LoRA)

QLoRA combines 4-bit NormalFloat (NF4) quantization with LoRA, enabling fine-tuning of 65B+ models on a single 48 GB GPU.

#### Key Innovations

1. **4-bit NormalFloat (NF4)**: Information-theoretically optimal quantization for normally distributed weights
2. **Double Quantization**: Quantize the quantization constants themselves to save ~0.4 bits/param
3. **Paged Optimizers**: Use NVIDIA unified memory to handle memory spikes during training

```
Memory comparison for Llama-2-7B:
  FP16 full fine-tuning:  ~120 GB
  LoRA (FP16 base):       ~30 GB
  QLoRA (4-bit base):     ~10 GB  ← single consumer GPU
```

#### Code: QLoRA Configuration

```python
from transformers import BitsAndBytesConfig
import torch

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",           # NormalFloat4 quantization
    bnb_4bit_compute_dtype=torch.bfloat16,  # Compute in bfloat16
    bnb_4bit_use_double_quant=True        # Double quantization
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-13b-hf",
    quantization_config=bnb_config,
    device_map="auto"
)

# Apply LoRA on top of quantized model (same as above)
lora_config = LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    task_type=TaskType.CAUSAL_LM
)
model = get_peft_model(model, lora_config)
```

### Technique Comparison

| Feature | Full Fine-Tuning | LoRA | QLoRA | Prefix Tuning |
|---------|-----------------|------|-------|---------------|
| **Trainable params** | 100% | 0.01–1% | 0.01–1% | <0.1% |
| **GPU memory (7B)** | ~120 GB | ~30 GB | ~10 GB | ~28 GB |
| **Training speed** | Baseline | ~1.2× faster | ~0.8× (dequant overhead) | ~1.1× faster |
| **Output quality** | Best | Near-best | Near-best | Good |
| **Merges with base** | N/A | Yes (weight merge) | Yes (after dequant) | No |
| **Multi-task** | Separate models | Swap adapters | Swap adapters | Swap prefixes |

---

## 11.3 Fine-Tuning Implementation Walkthrough

### Walkthrough 1: Hugging Face Transformers + PEFT (Open Source)

This walkthrough fine-tunes Llama-2-7B on a custom instruction dataset using QLoRA.

#### Step 1: Install Dependencies

```bash
pip install transformers peft datasets accelerate bitsandbytes trl
```

#### Step 2: Load and Prepare Dataset

```python
from datasets import load_dataset

# Load dataset (or use your own JSONL file)
dataset = load_dataset("tatsu-lab/alpaca", split="train")

# Format into chat template
def format_prompt(example):
    if example["input"]:
        return f"""### Instruction:
{example["instruction"]}

### Input:
{example["input"]}

### Response:
{example["output"]}"""
    else:
        return f"""### Instruction:
{example["instruction"]}

### Response:
{example["output"]}"""

dataset = dataset.map(lambda x: {"text": format_prompt(x)})

# Train/validation split
dataset = dataset.train_test_split(test_size=0.05, seed=42)
```

#### Step 3: Load Model with QLoRA

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

model_id = "meta-llama/Llama-2-7b-hf"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto"
)
```

#### Step 4: Apply LoRA

```python
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"]
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
```

#### Step 5: Configure Training

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./llama2-7b-finetuned",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,  # Effective batch size = 16
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch",
    evaluation_strategy="epoch",
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    optim="paged_adamw_8bit",
    gradient_checkpointing=True,
    report_to="none"
)
```

#### Step 6: Train

```python
from trl import SFTTrainer

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    peft_config=lora_config,
    args=training_args,
    max_seq_length=512,
    tokenizer=tokenizer
)

trainer.train()

# Save adapter weights (only ~16 MB, not the full 13 GB model)
trainer.save_model("./llama2-7b-finetuned/adapter")
```

#### Step 7: Inference

```python
from peft import PeftModel

# Load base + adapter
base_model = AutoModelForCausalLM.from_pretrained(
    model_id, torch_dtype=torch.bfloat16, device_map="auto"
)
model = PeftModel.from_pretrained(base_model, "./llama2-7b-finetuned/adapter")

# Merge adapter into base for faster inference
model = model.merge_and_unload()

# Generate
prompt = "### Instruction:\nExplain LoRA in simple terms.\n\n### Response:\n"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

### Walkthrough 2: Azure OpenAI Fine-Tuning API

Azure OpenAI supports fine-tuning GPT-4o and GPT-4o-mini via a managed API.

#### Step 1: Prepare Training Data (JSONL)

```jsonl
{"messages": [{"role": "system", "content": "You are a helpful travel assistant."}, {"role": "user", "content": "Best time to visit Japan?"}, {"role": "assistant", "content": "The best times to visit Japan are spring (March–May) for cherry blossoms and autumn (September–November) for fall foliage. Both seasons offer mild weather and stunning natural scenery."}]}
{"messages": [{"role": "system", "content": "You are a helpful travel assistant."}, {"role": "user", "content": "Do I need a visa for Japan?"}, {"role": "assistant", "content": "Citizens of 68 countries can enter Japan visa-free for short stays (14–90 days). Check the Japanese Ministry of Foreign Affairs website for your country's specific requirements."}]}
```

#### Step 2: Upload Training File

```python
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key="YOUR_API_KEY",
    api_version="2024-10-01-preview",
    azure_endpoint="https://YOUR_RESOURCE.openai.azure.com/"
)

# Upload training file
with open("training_data.jsonl", "rb") as f:
    response = client.files.create(file=f, purpose="fine-tune")
training_file_id = response.id
print(f"Training file ID: {training_file_id}")
```

#### Step 3: Create Fine-Tuning Job

```python
response = client.fine_tuning.jobs.create(
    training_file=training_file_id,
    model="gpt-4o-mini-2024-07-18",  # Base model
    hyperparameters={
        "n_epochs": 3,
        "batch_size": 4,
        "learning_rate_multiplier": 0.1
    }
)
job_id = response.id
print(f"Fine-tuning job ID: {job_id}")

# Monitor job status
job = client.fine_tuning.jobs.retrieve(job_id)
print(f"Status: {job.status}")
```

#### Step 4: Deploy and Use Fine-Tuned Model

```python
# Once status is "succeeded", use the fine-tuned model
response = client.chat.completions.create(
    model="gpt-4o-mini-ft-2024-xx-xx",  # Fine-tuned model name
    messages=[
        {"role": "system", "content": "You are a helpful travel assistant."},
        {"role": "user", "content": "What should I pack for Tokyo in April?"}
    ]
)
print(response.choices[0].message.content)
```

#### Azure OpenAI Fine-Tuning Pricing (Approximate)

| Model | Training Cost (per 1M tokens) | Inference Cost |
|-------|-------------------------------|----------------|
| GPT-4o-mini | $3.00 | Standard rate |
| GPT-4o | $25.00 | Standard rate |

### Key Takeaways

1. **Always try prompt engineering and RAG first** — fine-tuning is a last resort, not a first step
2. **Data quality is king** — 500 excellent examples outperform 50,000 mediocre ones
3. **LoRA/QLoRA make fine-tuning accessible** — a single consumer GPU can fine-tune 7B–13B models
4. **QLoRA reduces memory by ~75%** compared to standard LoRA via 4-bit quantization
5. **Save only adapter weights** — LoRA adapters are ~16 MB vs ~13 GB for full models
6. **Azure OpenAI fine-tuning** is the simplest path if you want managed infrastructure
7. **Evaluate carefully** — use human eval + automated metrics to catch regressions
8. **Start small** — fine-tune a 7B model before attempting 70B
