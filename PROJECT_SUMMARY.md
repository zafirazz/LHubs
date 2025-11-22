# AML Casefile Generation System - Project Summary

## Overview

A complete, production-ready agentic system architecture for automated AML (Anti-Money Laundering) casefile generation. The system processes client data (CSV files, notes, transactions) through a multi-agent pipeline to produce comprehensive casefiles with risk assessments, red flags, inconsistencies, and SAR recommendations.

## Key Features

✅ **Multi-Agent Architecture**: 8 specialized agents working in coordinated workflows  
✅ **Hugging Face Integration**: Uses local ChatGPT OSS 20B model (or any HF model)  
✅ **CSV-First Design**: Optimized for CSV data processing  
✅ **Event-Driven**: Message-passing architecture for agent communication  
✅ **Workflow Engine**: YAML-defined workflows with dependency management  
✅ **Production Ready**: Docker support, logging, error handling, health checks  
✅ **Modular & Extensible**: Clean separation of concerns, easy to extend  

## System Components

### Agents (8 Total)

1. **Data Parser Agent** - Parses CSV files, notes, and transactions
2. **Data Validator Agent** - Validates data completeness and quality
3. **Risk Assessment Agent** - Calculates comprehensive risk scores
4. **Inconsistency Detection Agent** - Identifies data discrepancies
5. **Red Flag Detection Agent** - Detects AML red flags and suspicious patterns
6. **Casefile Builder Agent** - Aggregates all findings into casefile
7. **SAR Recommendation Agent** - Generates final filing recommendation
8. **Orchestrator Agent** - Coordinates workflow execution

### Core Services

- **LLM Service**: Hugging Face model integration (ChatGPT OSS 20B)
- **Workflow Engine**: YAML-based workflow execution
- **Message Broker**: Inter-agent communication (Redis-ready)
- **State Manager**: Workflow state tracking

### Tools

- **Parsers**: CSV, text, transaction normalizers
- **Validators**: Cross-reference, logic validators
- **Analyzers**: Risk scoring, pattern matching, rule engine
- **Formatters**: Document generation, template engine

## Architecture Highlights

### Data Flow

```
Upload → Parser → Validator → [Risk Assessment | Inconsistency Detection | Red Flag Detection] → Casefile Builder → SAR Recommendation
```

### Agent Communication

- **Message Passing**: Structured JSON messages via AgentMessage class
- **Shared State**: Workflow state managed centrally
- **Event-Driven**: Agents publish/subscribe to events
- **Dependency Management**: Workflow engine handles execution order

### Technology Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI for REST API
- **LLM**: Hugging Face Transformers (local models)
- **Orchestration**: Custom workflow engine with YAML definitions
- **Data Processing**: pandas, numpy
- **Containerization**: Docker & Docker Compose

## Project Structure

```
LHubs/
├── src/
│   ├── agents/              # 8 agent implementations
│   ├── orchestrator/        # Workflow engine
│   ├── tools/               # Agent tools (parsers, validators, analyzers)
│   ├── services/            # Core services (LLM, storage, etc.)
│   ├── workflows/           # YAML workflow definitions
│   └── main.py              # FastAPI application entry point
├── configs/
│   └── app.yaml             # Application configuration
├── data/                    # Data directories (raw, processed, outputs)
├── tests/                   # Test suites
├── scripts/                  # Utility scripts
├── infrastructure/          # Docker, K8s configs
├── ARCHITECTURE.md          # Detailed architecture documentation
├── STARTUP_GUIDE.md         # Getting started guide
└── requirements.txt         # Python dependencies
```

## Quick Start

```bash
# 1. Setup
./scripts/setup.sh
cp .env.example .env
# Edit .env with your Hugging Face model name

# 2. Run
source venv/bin/activate
python -m src.main

# 3. Test
curl -X POST "http://localhost:8000/api/v1/process-casefile?client_folder_path=data/raw/test_client"
```

## Configuration

### Hugging Face Model Setup

In `configs/app.yaml` or `.env`:
```yaml
llm:
  provider: "huggingface"
  model_name: "your-chatgpt-oss-20b-model"  # Your model name
  use_local: true
  device: "auto"  # auto, cpu, cuda, mps
```

### CSV Data Format

The system expects CSV files with transaction data:
- `transaction_id`, `date`, `amount`, `currency`
- `type`, `from_account`, `to_account`, `description`

## Output Structure

The system produces:

1. **Full Summary**: Executive summary of findings
2. **Risk Score**: 0-100 risk assessment
3. **Detected Inconsistencies**: Data quality issues
4. **Red Flags**: AML red flags with evidence links
5. **SAR Recommendation**: Final filing recommendation (yes/no/maybe)

## Extensibility

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement `process()`, `get_required_inputs()`, `get_output_schema()`
3. Register in `src/main.py`
4. Add to workflow in `src/workflows/default.yaml`

### Adding New Tools

1. Create tool class inheriting from `BaseTool` (LangChain)
2. Implement `_run()` and `_arun()` methods
3. Add to agent's tool list

### Customizing Workflows

Edit `src/workflows/default.yaml` to:
- Change execution order
- Add/remove steps
- Configure parallel execution
- Set timeouts and retries

## Production Considerations

- **Scalability**: Agents are stateless, can be horizontally scaled
- **Monitoring**: Health checks, logging, metrics endpoints
- **Error Handling**: Retries, dead-letter queues, checkpointing
- **Security**: Input validation, secure file handling, audit logging
- **Performance**: Parallel agent execution, async operations

## Documentation

- **ARCHITECTURE.md**: Complete system design and architecture
- **STARTUP_GUIDE.md**: Step-by-step setup and usage
- **README.md**: Quick reference
- Code comments: Detailed inline documentation

## Next Steps

1. Review `ARCHITECTURE.md` for detailed design
2. Follow `STARTUP_GUIDE.md` to get started
3. Customize agents and workflows for your needs
4. Add database persistence if needed
5. Deploy using Docker or your preferred method

## Support

The system is designed to be:
- **Self-documenting**: Extensive code comments
- **Modular**: Easy to understand and modify
- **Testable**: Clear interfaces and separation of concerns
- **Maintainable**: Clean code principles throughout

