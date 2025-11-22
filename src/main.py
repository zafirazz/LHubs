"""
Main entry point for AML Casefile Generation System.
"""

import asyncio
import logging
import sys
import os
import re
from pathlib import Path
from typing import Dict, Any

import yaml
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator.workflow_engine import WorkflowEngine
from src.agents.parser.data_parser_agent import DataParserAgent
from src.agents.validator.data_validator_agent import DataValidatorAgent
from src.agents.risk_assessment.risk_assessment_agent import RiskAssessmentAgent
from src.agents.inconsistency_detection.inconsistency_detection_agent import InconsistencyDetectionAgent
from src.agents.redflag_detection.redflag_detection_agent import RedFlagDetectionAgent
from src.agents.casefile_builder.casefile_builder_agent import CasefileBuilderAgent
from src.agents.sar_recommendation.sar_recommendation_agent import SARRecommendationAgent
from src.services.llm_service import LLMService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AML Casefile Generation System",
    description="Automated AML casefile generation from client data",
    version="1.0.0",
)

# Global state
workflow_engine: WorkflowEngine = None
llm_service: LLMService = None


def expand_env_vars(value: Any) -> Any:
    """Expand environment variable syntax in config values."""
    if isinstance(value, str):
        # Match ${VAR:default} syntax
        match = re.match(r'\$\{([^:]+):([^}]+)\}', value)
        if match:
            var_name, default_value = match.groups()
            return os.getenv(var_name, default_value)
        # Match ${VAR} syntax (no default)
        match = re.match(r'\$\{([^}]+)\}', value)
        if match:
            var_name = match.group(1)
            return os.getenv(var_name, "")
    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    return value


def load_config() -> Dict[str, Any]:
    """Load application configuration."""
    config_path = Path(__file__).parent.parent / "configs" / "app.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    # Expand environment variables
    return expand_env_vars(config)


def initialize_system():
    """Initialize the system with all agents and services."""
    global workflow_engine, llm_service

    logger.info("Initializing AML Casefile Generation System")

    # Load configuration
    config = load_config()

    # Initialize LLM service (Hugging Face)
    llm_config = config.get("llm", {})
    if llm_config.get("use_local", True):
        llm_service = LLMService(
            model_name=llm_config.get("model_name", "Qwen/Qwen2.5-7B-Instruct"),
            model_path=llm_config.get("model_path"),
            device=llm_config.get("device", "auto"),
            temperature=llm_config.get("temperature", 0.1),
            max_tokens=llm_config.get("max_tokens", 4000),
            trust_remote_code=llm_config.get("trust_remote_code", True),
        )
        # Initialize model (this may take time on first run)
        logger.info("Initializing LLM model (this may take a moment)...")
        try:
            llm_service.initialize()
            logger.info("LLM model initialized successfully")
        except Exception as e:
            logger.warning(f"LLM initialization failed: {e}. System will continue without LLM features.")

    # Initialize workflow engine
    workflow_engine = WorkflowEngine(workflow_file="workflows/default.yaml")
    workflow_engine.load_workflow()

    # Initialize and register agents
    agents_config = config.get("agents", {})

    parser_agent = DataParserAgent(llm_service=llm_service)
    workflow_engine.register_agent("data_parser", parser_agent)

    validator_agent = DataValidatorAgent(llm_service=llm_service)
    workflow_engine.register_agent("data_validator", validator_agent)

    risk_agent = RiskAssessmentAgent(llm_service=llm_service)
    workflow_engine.register_agent("risk_assessment", risk_agent)

    inconsistency_agent = InconsistencyDetectionAgent(llm_service=llm_service)
    workflow_engine.register_agent("inconsistency_detection", inconsistency_agent)

    redflag_agent = RedFlagDetectionAgent(llm_service=llm_service)
    workflow_engine.register_agent("redflag_detection", redflag_agent)

    casefile_agent = CasefileBuilderAgent(llm_service=llm_service)
    workflow_engine.register_agent("casefile_builder", casefile_agent)

    sar_agent = SARRecommendationAgent(llm_service=llm_service)
    workflow_engine.register_agent("sar_recommendation", sar_agent)

    logger.info("System initialization complete")


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    initialize_system()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AML Casefile Generation System",
        "version": "1.0.0",
    }


@app.post("/api/v1/process-casefile")
async def process_casefile(client_folder_path: str):
    """
    Process a client folder and generate AML casefile.
    
    Args:
        client_folder_path: Path to the client folder containing CSV files and data
        
    Returns:
        Complete casefile with all findings and SAR recommendation
    """
    try:
        logger.info(f"Processing casefile for: {client_folder_path}")

        # Execute workflow
        initial_input = {
            "client_folder_path": client_folder_path,
        }

        result = workflow_engine.execute(initial_input)

        # Build response
        response = {
            "case_id": result["workflow_id"],
            "status": "completed",
            "execution_time_seconds": result["execution_time"],
            "casefile": {
                "summary": result["outputs"].get("casefile", {}).get("summary", {}),
                "executive_summary": result["outputs"].get("casefile", {}).get("executive_summary", ""),
                "risk_score": result["outputs"].get("risk_assessment", {}).get("risk_score", 0),
                "red_flags": result["outputs"].get("red_flags", {}),
                "inconsistencies": result["outputs"].get("inconsistencies", {}),
                "sar_recommendation": result["outputs"].get("sar_recommendation", {}),
            },
        }

        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"Error processing casefile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workflow/state")
async def get_workflow_state():
    """Get current workflow state."""
    if workflow_engine:
        return workflow_engine.get_state()
    return {"status": "not_initialized"}


if __name__ == "__main__":
    import uvicorn

    config = load_config()
    api_config = config.get("api", {})

    # Ensure port is an integer
    port = api_config.get("port", 8000)
    if isinstance(port, str):
        try:
            port = int(port)
        except ValueError:
            logger.warning(f"Invalid port value '{port}', using default 8000")
            port = 8000

    uvicorn.run(
        "src.main:app",
        host=api_config.get("host", "0.0.0.0"),
        port=port,
        reload=config.get("app", {}).get("debug", False),
    )

