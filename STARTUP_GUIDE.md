# Startup Guide - AML Casefile Generation System

## Prerequisites

- Python 3.11 or higher
- pip
- (Optional) CUDA-capable GPU for faster LLM inference
- (Optional) Docker and Docker Compose

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd LHubs

# Run setup script
./scripts/setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and configure:
# - LLM_MODEL_NAME: Your Hugging Face model name (e.g., your ChatGPT OSS 20B model)
# - LLM_MODEL_PATH: (Optional) Local path if model is already downloaded
# - LLM_DEVICE: auto, cpu, cuda, or mps (for Apple Silicon)
```

### 3. Download/Configure Hugging Face Model

If you haven't already downloaded your ChatGPT OSS 20B model:

```python
# Option 1: Let the system download automatically on first run
# The model will be downloaded from Hugging Face on first initialization

# Option 2: Download manually using Python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "your-model-name-here"  # Replace with your model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
```

Update `configs/app.yaml` or `.env` with your model name:
```yaml
llm:
  model_name: "your-chatgpt-oss-20b-model-name"
  use_local: true
```

### 4. Prepare Data

Create a test client folder structure:
```
data/raw/test_client/
├── transactions.csv
├── client_data.csv
└── notes.txt
```

Example `transactions.csv`:
```csv
transaction_id,date,amount,currency,type,from_account,to_account,description
tx1,2024-01-15,5000,USD,transfer,ACC001,ACC002,Payment
tx2,2024-01-16,9500,USD,transfer,ACC001,ACC003,Payment
tx3,2024-01-17,9800,USD,transfer,ACC002,ACC001,Refund
```

### 5. Run the System

```bash
# Activate virtual environment
source venv/bin/activate

# Run the API server
python -m src.main

# Or using uvicorn directly
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### 6. Test the System

```bash
# Health check
curl http://localhost:8000/health

# Process a casefile
curl -X POST "http://localhost:8000/api/v1/process-casefile?client_folder_path=data/raw/test_client"
```

## Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t aml-system .
docker run -p 8000:8000 -v $(pwd)/data:/app/data aml-system
```

## Project Structure Overview

```
LHubs/
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── parser/         # Data parsing agents
│   │   ├── validator/      # Data validation agents
│   │   ├── risk_assessment/
│   │   ├── inconsistency_detection/
│   │   ├── redflag_detection/
│   │   ├── casefile_builder/
│   │   └── sar_recommendation/
│   ├── orchestrator/       # Workflow engine
│   ├── tools/              # Agent tools
│   ├── services/           # Core services (LLM, DB, etc.)
│   └── workflows/          # Workflow definitions
├── configs/                # Configuration files
├── data/                   # Data directories
├── tests/                  # Test suites
└── scripts/                # Utility scripts
```

## Key Configuration Files

- `configs/app.yaml`: Main application configuration
- `.env`: Environment variables (not in git)
- `src/workflows/default.yaml`: Workflow definition

## Troubleshooting

### Model Loading Issues

If the model fails to load:
1. Check available disk space (models can be 10-40GB)
2. Verify model name is correct in config
3. Check Hugging Face access (may need authentication)
4. Try using CPU if GPU memory is insufficient

### CSV Parsing Issues

- Ensure CSV files are UTF-8 encoded
- Check for proper headers
- Verify delimiter (comma, semicolon, etc.)

### Memory Issues

- Reduce `max_tokens` in LLM config
- Use smaller batch sizes
- Consider using CPU if GPU memory is limited

## Next Steps

1. Review `ARCHITECTURE.md` for system design details
2. Customize agents in `src/agents/`
3. Modify workflows in `src/workflows/`
4. Add custom tools in `src/tools/`
5. Extend with database persistence if needed

## Support

For issues or questions, check:
- Architecture documentation: `ARCHITECTURE.md`
- Code comments in agent implementations
- Workflow definitions in `src/workflows/`

