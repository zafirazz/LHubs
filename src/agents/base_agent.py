"""
Base agent class providing common functionality for all agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import uuid

from langchain.tools import BaseTool

# Optional imports for type hints (may not be available in all LangChain versions)
if TYPE_CHECKING:
    try:
        from langchain.agents import AgentExecutor
    except ImportError:
        AgentExecutor = Any
    try:
        from langchain.memory import ConversationBufferMemory
    except ImportError:
        ConversationBufferMemory = Any
else:
    # Try to import, but don't fail if not available
    try:
        from langchain.agents import AgentExecutor
    except ImportError:
        AgentExecutor = Any
    try:
        from langchain.memory import ConversationBufferMemory
    except ImportError:
        ConversationBufferMemory = Any


class AgentStatus(Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class AgentMessage:
    """Structured message for inter-agent communication."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: str = ""
    message_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary."""
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            sender=data.get("sender", ""),
            receiver=data.get("receiver", ""),
            message_type=data.get("message_type", ""),
            payload=data.get("payload", {}),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            correlation_id=data.get("correlation_id", ""),
            metadata=data.get("metadata", {}),
        )


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    
    Provides common functionality:
    - Message handling
    - Tool management
    - State management
    - Error handling
    - Logging
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        tools: Optional[List[BaseTool]] = None,
        memory: Optional[ConversationBufferMemory] = None,
        max_iterations: int = 10,
        verbose: bool = True,
        llm_service: Optional[Any] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.tools = tools or []
        # Initialize memory (optional, may not be used)
        if memory is not None:
            self.memory = memory
        else:
            # Try to create ConversationBufferMemory, but don't fail if not available
            try:
                # Check if ConversationBufferMemory is actually a class (not Any)
                if ConversationBufferMemory is not Any and hasattr(ConversationBufferMemory, '__call__'):
                    self.memory = ConversationBufferMemory()
                else:
                    self.memory = None
            except (ImportError, NameError, TypeError):
                self.memory = None  # Memory not available
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.llm_service = llm_service
        
        self.status = AgentStatus.IDLE
        self.current_task_id: Optional[str] = None
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Agent executor (initialized in subclasses)
        self.executor: Optional[AgentExecutor] = None

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method to be implemented by subclasses.
        
        Args:
            input_data: Input data for processing
            
        Returns:
            Processing results
        """
        pass

    @abstractmethod
    def get_required_inputs(self) -> List[str]:
        """Return list of required input field names."""
        pass

    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for output data."""
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data against required inputs."""
        required = self.get_required_inputs()
        missing = [field for field in required if field not in input_data]
        if missing:
            self.last_error = f"Missing required inputs: {missing}"
            return False
        return True

    def execute(self, input_data: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """
        Execute agent with error handling and state management.
        
        Args:
            input_data: Input data
            task_id: Task identifier
            
        Returns:
            Processing results
        """
        self.current_task_id = task_id
        self.status = AgentStatus.RUNNING
        self.start_time = datetime.utcnow()
        self.error_count = 0
        self.last_error = None

        try:
            # Validate input
            if not self.validate_input(input_data):
                raise ValueError(self.last_error)

            # Process
            result = self.process(input_data)
            
            # Mark as completed
            self.status = AgentStatus.COMPLETED
            self.end_time = datetime.utcnow()
            
            return result

        except Exception as e:
            self.status = AgentStatus.FAILED
            self.error_count += 1
            self.last_error = str(e)
            self.end_time = datetime.utcnow()
            
            if self.verbose:
                print(f"Agent {self.name} failed: {e}")
            
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "current_task_id": self.current_task_id,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "duration_seconds": duration,
        }

    def reset(self):
        """Reset agent state."""
        self.status = AgentStatus.IDLE
        self.current_task_id = None
        self.error_count = 0
        self.last_error = None
        self.start_time = None
        self.end_time = None

    def send_message(self, receiver: str, message_type: str, payload: Dict[str, Any]) -> AgentMessage:
        """Create and send a message to another agent."""
        message = AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            payload=payload,
            correlation_id=self.current_task_id or "",
        )
        return message

    def receive_message(self, message: AgentMessage) -> None:
        """Handle incoming message."""
        if self.verbose:
            print(f"Agent {self.name} received message: {message.message_type} from {message.sender}")

