# AML Casefile Generation System

An intelligent, multi-agent system for automated AML casefile generation from client data uploads.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the system
python -m src.main
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

## Project Structure

```
LHubs/
├── src/
│   ├── agents/          # Agent implementations
│   ├── orchestrator/    # Workflow orchestration
│   ├── tools/           # Agent tools and utilities
│   ├── services/        # Core services (DB, cache, etc.)
│   └── workflows/       # Workflow definitions
├── configs/             # Configuration files
├── prompts/             # LLM prompts and templates
├── tests/               # Test suites
├── scripts/             # Utility scripts
└── infrastructure/      # Docker, K8s configs
```

## Development

```bash
# Run tests
pytest

# Format code
black src/
ruff check src/

# Type check
mypy src/
```

## License

Proprietary

