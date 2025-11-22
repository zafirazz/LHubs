"""
Workflow Engine - Orchestrates agent execution based on workflow definitions.
"""

import logging
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Executes workflows defined in YAML files.
    
    Manages:
    - Agent execution order
    - Dependencies
    - Parallel execution
    - Error handling
    - State management
    """

    def __init__(self, workflow_file: str = "workflows/default.yaml"):
        self.workflow_file = workflow_file
        self.workflow_def: Dict[str, Any] = {}
        self.agents: Dict[str, Any] = {}
        self.state: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []

    def load_workflow(self) -> None:
        """Load workflow definition from YAML file."""
        workflow_path = Path(__file__).parent.parent / self.workflow_file
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

        with open(workflow_path, "r") as f:
            self.workflow_def = yaml.safe_load(f)

        logger.info(f"Loaded workflow: {self.workflow_def.get('workflow', {}).get('name', 'unknown')}")

    def register_agent(self, agent_id: str, agent: Any) -> None:
        """Register an agent for execution."""
        self.agents[agent_id] = agent
        logger.info(f"Registered agent: {agent_id}")

    def execute(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            initial_input: Initial input data (e.g., client_folder_path)
            
        Returns:
            Final workflow output
        """
        if not self.workflow_def:
            self.load_workflow()

        workflow_id = str(uuid.uuid4())
        self.state = {
            "workflow_id": workflow_id,
            "start_time": datetime.utcnow(),
            "status": "running",
            "inputs": initial_input,
            "outputs": {},
            "step_outputs": {},
        }

        logger.info(f"Starting workflow execution: {workflow_id}")

        try:
            steps = self.workflow_def.get("steps", [])
            executed_steps = set()

            # Execute steps in dependency order
            while len(executed_steps) < len(steps):
                # Find steps ready to execute
                ready_steps = self._find_ready_steps(steps, executed_steps)

                if not ready_steps:
                    # Check for circular dependencies or missing dependencies
                    remaining = [s["id"] for s in steps if s["id"] not in executed_steps]
                    raise RuntimeError(f"Cannot proceed: steps {remaining} have unmet dependencies")

                # Execute ready steps (potentially in parallel)
                for step in ready_steps:
                    if step.get("parallel", False):
                        # Execute in parallel (simplified - in production use async/threading)
                        self._execute_step(step, initial_input)
                    else:
                        self._execute_step(step, initial_input)

                    executed_steps.add(step["id"])

            # Workflow completed
            self.state["status"] = "completed"
            self.state["end_time"] = datetime.utcnow()

            logger.info(f"Workflow completed: {workflow_id}")

            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "outputs": self.state["outputs"],
                "execution_time": (
                    self.state["end_time"] - self.state["start_time"]
                ).total_seconds(),
            }

        except Exception as e:
            self.state["status"] = "failed"
            self.state["error"] = str(e)
            self.state["end_time"] = datetime.utcnow()
            logger.error(f"Workflow failed: {e}")
            raise

    def _find_ready_steps(
        self, steps: List[Dict[str, Any]], executed_steps: set
    ) -> List[Dict[str, Any]]:
        """Find steps that are ready to execute (dependencies met)."""
        ready = []

        for step in steps:
            if step["id"] in executed_steps:
                continue

            # Check dependencies
            depends_on = step.get("depends_on", [])
            if all(dep in executed_steps for dep in depends_on):
                ready.append(step)

        return ready

    def _execute_step(self, step: Dict[str, Any], initial_input: Dict[str, Any]) -> None:
        """Execute a single workflow step."""
        step_id = step["id"]
        agent_id = step["agent"]

        logger.info(f"Executing step: {step_id} with agent: {agent_id}")

        if agent_id not in self.agents:
            raise ValueError(f"Agent not registered: {agent_id}")

        agent = self.agents[agent_id]

        # Prepare inputs
        step_inputs = {}
        for input_key in step.get("inputs", []):
            # Try to get from step outputs first, then from initial input
            if input_key in self.state["step_outputs"]:
                step_inputs[input_key] = self.state["step_outputs"][input_key]
            elif input_key in initial_input:
                step_inputs[input_key] = initial_input[input_key]
            else:
                raise ValueError(f"Missing input for step {step_id}: {input_key}")

        # Execute agent
        task_id = f"{self.state['workflow_id']}_{step_id}"
        result = agent.execute(step_inputs, task_id)

        # Store outputs
        for output_key in step.get("outputs", []):
            if output_key in result:
                self.state["step_outputs"][output_key] = result[output_key]
                self.state["outputs"][output_key] = result[output_key]

        # Record execution
        self.execution_history.append({
            "step_id": step_id,
            "agent_id": agent_id,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_state(self) -> Dict[str, Any]:
        """Get current workflow state."""
        return self.state.copy()

