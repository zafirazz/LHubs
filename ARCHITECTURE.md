# AML Casefile Generation System - Architecture Overview

## 1. High-Level System Overview

### Purpose
The system automatically generates comprehensive AML (Anti-Money Laundering) casefiles from uploaded client data. It processes CSV files, notes, and transaction records through a multi-agent pipeline to produce:
- Full case summary
- Risk score calculation
- Detected inconsistencies
- Red flags with evidence links
- Final SAR (Suspicious Activity Report) recommendation

### System Architecture Principles
- **Event-Driven**: Agents communicate via message queues and events
- **Modular**: Each agent is independently deployable and testable
- **Observable**: Comprehensive logging and monitoring at every stage
- **Resilient**: Error handling, retries, and dead-letter queues
- **Scalable**: Horizontal scaling through stateless agent design

### Data Flow

```
Upload → Parser Agent → Data Validation → Multi-Agent Processing → Aggregation → Casefile Generation
```

1. **Input Stage**: Judge uploads client folder (CSV + notes + transactions)
2. **Parsing Stage**: Data Parser Agent extracts and normalizes all data
3. **Validation Stage**: Data Validator Agent checks completeness and quality
4. **Analysis Stage**: Parallel agent execution:
   - Risk Assessment Agent
   - Inconsistency Detection Agent
   - Red Flag Detection Agent
5. **Synthesis Stage**: Casefile Builder Agent aggregates all findings
6. **Output Stage**: SAR Recommendation Agent produces final report

### Key Components

#### Orchestration Layer
- **Workflow Engine**: Manages agent execution order and dependencies
- **Message Broker**: Handles inter-agent communication (Redis/RabbitMQ)
- **Task Queue**: Manages long-running tasks and retries
- **State Manager**: Tracks workflow state and agent outputs

#### Agent Layer
- Specialized agents with specific capabilities
- Each agent has isolated execution environment
- Agents communicate via structured messages

#### Tool Layer
- File system operations
- Database access
- External API integrations
- Vector search capabilities

#### Service Layer
- Data persistence
- Caching
- Authentication/Authorization
- API endpoints

## 2. Agent Architecture

### Agent Communication Model
- **Message Passing**: Agents communicate via structured JSON messages
- **Shared Memory**: Redis for temporary state, PostgreSQL for persistent data
- **Event Bus**: Pub/Sub for asynchronous notifications
- **Workflow State**: Centralized state store for coordination

### Agent Definitions

#### 1. Data Parser Agent
**Role**: Extract and normalize data from various file formats

**Inputs**:
- Client folder path
- File metadata (types, sizes)

**Outputs**:
- Normalized CSV data (structured)
- Extracted notes (text)
- Parsed transactions (structured)
- Data quality metrics

**Tools**:
- CSV parser
- PDF/text extractor
- Transaction normalizer
- Data validator

**Decision Logic**:
- Detects file types automatically
- Chooses appropriate parser
- Validates schema compliance
- Reports parsing errors

**Communication**:
- Publishes: `data.parsed` event
- Subscribes: `upload.received` event
- Writes to: Shared data store

---

#### 2. Data Validator Agent
**Role**: Validate data completeness, consistency, and quality

**Inputs**:
- Parsed data from Parser Agent
- Validation rules and schemas

**Outputs**:
- Validation report
- Data quality score
- Missing data indicators
- Schema compliance status

**Tools**:
- Schema validator
- Data quality scorer
- Completeness checker
- Anomaly detector

**Decision Logic**:
- Applies validation rules
- Calculates quality metrics
- Flags critical missing data
- Determines if data is sufficient for analysis

**Communication**:
- Publishes: `validation.complete` event
- Subscribes: `data.parsed` event
- Writes to: Validation results store

---

#### 3. Risk Assessment Agent
**Role**: Calculate comprehensive risk score based on multiple factors

**Inputs**:
- Validated client data
- Transaction patterns
- Historical risk models
- Regulatory rules

**Outputs**:
- Overall risk score (0-100)
- Risk breakdown by category
- Risk factors identified
- Confidence level

**Tools**:
- Risk scoring models
- Pattern matcher
- Statistical analyzer
- Rule engine

**Decision Logic**:
- Weights different risk factors
- Applies ML models if available
- Considers transaction velocity
- Factors in client profile

**Communication**:
- Publishes: `risk.assessed` event
- Subscribes: `validation.complete` event
- Writes to: Risk assessment store

---

#### 4. Inconsistency Detection Agent
**Role**: Identify discrepancies and contradictions in the data

**Inputs**:
- All parsed data sources
- Cross-reference data

**Outputs**:
- List of inconsistencies
- Severity levels
- Evidence links
- Impact assessment

**Tools**:
- Cross-reference checker
- Logic validator
- Temporal analyzer
- Pattern matcher

**Decision Logic**:
- Compares data across sources
- Checks temporal consistency
- Validates logical relationships
- Prioritizes by severity

**Communication**:
- Publishes: `inconsistencies.detected` event
- Subscribes: `validation.complete` event
- Writes to: Inconsistency findings store

---

#### 5. Red Flag Detection Agent
**Role**: Identify suspicious patterns and AML red flags

**Inputs**:
- Transaction data
- Client profile
- Red flag rules database
- Historical patterns

**Outputs**:
- Red flags list
- Evidence links
- Pattern matches
- Regulatory rule violations

**Tools**:
- Pattern matcher
- Rule engine
- Anomaly detector
- Vector similarity search

**Decision Logic**:
- Matches against known red flag patterns
- Applies regulatory rules
- Detects unusual behaviors
- Links evidence to findings

**Communication**:
- Publishes: `redflags.detected` event
- Subscribes: `validation.complete` event
- Writes to: Red flag findings store

---

#### 6. Casefile Builder Agent
**Role**: Aggregate all findings into comprehensive casefile

**Inputs**:
- All agent outputs
- Original data
- Templates

**Outputs**:
- Complete casefile document
- Structured summary
- Evidence compilation
- Executive summary

**Tools**:
- Document generator
- Template engine
- Evidence linker
- Report formatter

**Decision Logic**:
- Aggregates all findings
- Prioritizes information
- Structures narrative
- Formats for presentation

**Communication**:
- Publishes: `casefile.built` event
- Subscribes: `risk.assessed`, `inconsistencies.detected`, `redflags.detected`
- Writes to: Casefile store

---

#### 7. SAR Recommendation Agent
**Role**: Generate final SAR filing recommendation

**Inputs**:
- Complete casefile
- Regulatory thresholds
- Filing criteria

**Outputs**:
- SAR recommendation (Yes/No/Maybe)
- Confidence level
- Rationale
- Filing priority

**Tools**:
- Decision engine
- Regulatory rule checker
- Confidence calculator
- Recommendation formatter

**Decision Logic**:
- Evaluates all evidence
- Applies regulatory criteria
- Calculates recommendation confidence
- Provides clear rationale

**Communication**:
- Publishes: `sar.recommendation.ready` event
- Subscribes: `casefile.built` event
- Writes to: Final recommendation store

---

#### 8. Orchestrator Agent
**Role**: Coordinate workflow execution and manage agent lifecycle

**Inputs**:
- Workflow definitions
- System state
- Agent health status

**Outputs**:
- Workflow execution plan
- Agent assignments
- Error recovery actions

**Tools**:
- Workflow engine
- Agent manager
- State tracker
- Error handler

**Decision Logic**:
- Determines execution order
- Manages parallel execution
- Handles failures and retries
- Monitors agent health

**Communication**:
- Publishes: Workflow events
- Subscribes: All agent events
- Manages: Agent lifecycle

## 3. Technology Stack Recommendations

### Core Framework
- **Python 3.11+**: Primary language
- **FastAPI**: REST API and async support
- **LangGraph**: Agent orchestration and state management
- **LangChain**: LLM integration and tooling

### Data & Storage
- **PostgreSQL**: Primary database for structured data
- **Redis**: Caching and message broker
- **Chroma/FAISS**: Vector database for embeddings
- **SQLite**: Local development database

### Message Queue & Events
- **Redis Streams**: Lightweight message queue
- **Celery**: Task queue for long-running operations
- **WebSockets**: Real-time updates

### AI/ML
- **Hugging Face Transformers**: Local LLM models (ChatGPT OSS 20B, etc.)
- **PyTorch**: Deep learning framework
- **scikit-learn**: Traditional ML models
- **pandas**: Data manipulation
- **numpy**: Numerical operations

### Observability
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **ELK Stack**: Log aggregation (optional)
- **Sentry**: Error tracking

### Development
- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking
- **ruff**: Linting

## 4. Memory Architecture

### Short-term Memory (Redis)
- Agent execution state
- Workflow progress
- Temporary data caches
- Message queues

### Long-term Memory (PostgreSQL)
- Client data
- Agent outputs
- Casefiles
- Audit logs

### Vector Memory (Chroma/FAISS)
- Document embeddings
- Similarity search
- Pattern matching
- Historical case references

## 5. Error Handling & Recovery

### Agent Failures
- Automatic retry with exponential backoff
- Dead-letter queue for failed tasks
- Health checks and auto-restart
- Circuit breakers for external dependencies

### Workflow Recovery
- Checkpoint system for workflow state
- Ability to resume from last checkpoint
- Manual intervention points
- Rollback capabilities

## 6. Security Considerations

- Input validation and sanitization
- Secure file handling
- Encrypted data storage
- Audit logging
- Role-based access control
- API authentication (JWT)

