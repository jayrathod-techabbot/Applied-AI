# Setup Guide for GenAI Technical Content Course

## Prerequisites

- Python 3.10 or higher
- Git
- API keys for AI providers (OpenAI, Anthropic, Google, etc.)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gen-ai-course
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   GOOGLE_API_KEY=your_google_key
   ```

## Verify Installation

Run the verification script:
```bash
python utils/verify_setup.py
```

## IDE Setup (VS Code Recommended)

1. Install Python extension
2. Install Jupyter extension
3. Select the virtual environment as Python interpreter
4. Configure Jupyter to use the virtual environment

## Troubleshooting

### Common Issues

- **API Key errors**: Ensure keys are set in `.env` file
- **Import errors**: Verify all packages installed with `pip list`
- **Jupyter issues**: Install ipykernel: `python -m ipykernel install --user`

## Next Steps

Once setup is complete, start with Module 1: [01_generative_ai/README.md](01_generative_ai/README.md)
