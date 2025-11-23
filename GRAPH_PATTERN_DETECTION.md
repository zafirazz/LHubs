# Graph-Based AML Pattern Detection System

## Overview

This system implements graph-based detection of money laundering patterns using transaction data. The detection runs **BEFORE** LLM reasoning, providing algorithmic pattern detection that the compliance agent uses as evidence.

## Architecture

```
Transaction Data → Graph Builder → Pattern Detector → Graph Analysis Service → Compliance Agent
```

1. **Graph Builder**: Converts transactions into a graph structure (nodes=accounts, edges=transactions)
2. **Pattern Detector**: Algorithmically detects laundering patterns using graph theory
3. **Graph Analysis Service**: Manages pattern detection, caching, and query relevance
4. **Compliance Agent**: Integrates graph analysis results into compliance assessment

## Detected Patterns

### 1. Fan-Out Pattern
**Description**: One account sends money to many different accounts.

**Detection Logic**:
- Account with out-degree ≥ threshold (default: 5)
- Multiple unique recipients

**AML Significance**: Indicates potential money distribution or structuring to avoid detection.

**Example**: Account A sends to 10 different accounts within a short time period.

### 2. Fan-In Pattern
**Description**: Many accounts send money to one account.

**Detection Logic**:
- Account with in-degree ≥ threshold (default: 5)
- Multiple unique senders

**AML Significance**: Indicates potential money collection or funneling.

**Example**: 10 different accounts all send money to Account B.

### 3. Gather-Scatter Pattern
**Description**: Money is gathered from multiple sources, then scattered to multiple destinations.

**Detection Logic**:
- Account with high in-degree AND high out-degree
- Receives from many, sends to many

**AML Significance**: Classic laundering pattern - money is mixed and redistributed.

**Example**: Account C receives from 5 accounts, then sends to 8 different accounts.

### 4. Scatter-Gather Pattern
**Description**: Money is scattered first, then gathered (opposite flow).

**Detection Logic**:
- One account sends to many
- Multiple recipients then send to a common destination

**AML Significance**: Complex laundering structure to obscure money trail.

**Example**: Account D sends to 6 accounts, 4 of which then send to Account E.

### 5. Simple Cycle Pattern
**Description**: Circular transaction paths (money returns to origin).

**Detection Logic**:
- DFS to find cycles of length 3-10
- Path: A → B → C → ... → A

**AML Significance**: Circular transactions to create false transaction history.

**Example**: A → B → C → A (3-node cycle).

### 6. Bipartite Pattern
**Description**: Two distinct groups with transactions only between groups.

**Detection Logic**:
- Partition graph into two sets
- High cross-group transaction count

**AML Significance**: Structured money movement between two groups.

**Example**: Group 1 (5 accounts) only sends to Group 2 (3 accounts).

### 7. Layered/Stack Pattern
**Description**: Multi-layer transaction structure.

**Detection Logic**:
- Identify source layer (high out-degree, low in-degree)
- Intermediate layer (balanced)
- Sink layer (high in-degree, low out-degree)

**AML Significance**: Complex multi-stage laundering operation.

**Example**: 3 source accounts → 4 intermediaries → 2 sink accounts.

### 8. Random/Complex Graph Pattern
**Description**: High connectivity, complex interconnected structure.

**Detection Logic**:
- High average degree (≥ 3)
- Many cycles and interconnections
- No clear pattern structure

**AML Significance**: Deliberately complex structure to obscure money flow.

**Example**: 20 accounts with dense interconnections, average degree 5.

## Pattern Specifications

Each pattern is specified with:

```python
PatternMatch(
    pattern_type: str,           # Pattern identifier
    severity: str,                # "high", "medium", "low"
    description: str,             # Human-readable description
    accounts_involved: List[str], # Account IDs
    transactions_involved: List[str], # Transaction IDs
    total_amount: float,         # Total amount in pattern
    time_window_days: int,       # Time span
    confidence: float,            # 0.0 to 1.0
    metadata: Dict[str, Any]     # Pattern-specific data
)
```

## Integration with Compliance Agent

### Pre-LLM Analysis
Graph analysis runs **BEFORE** the LLM processes the query:

1. Query received
2. **Graph pattern detection** (algorithmic)
3. Context retrieval (RAG)
4. LLM reasoning (with graph results + context)

### Prompt Integration
Graph analysis results are included in the prompt:

```
## GRAPH-BASED PATTERN DETECTION (PRE-ANALYSIS)

[Pattern 1]
Type: FAN-OUT
Severity: HIGH
Confidence: 85%
Description: Account X sends to 12 different accounts
...

## CONTEXT DATA PROVIDED
[Retrieved context]

## COMPLIANCE QUESTION
[User query]
```

### Agent Instructions
The agent is instructed to:
- Reference specific detected patterns
- Correlate patterns with regulatory requirements
- Use pattern severity in risk assessment
- Explain how patterns relate to AML compliance

## Usage

### Pre-compute Patterns
```bash
# Generate graph patterns and cache them
python -m services.graph_analysis_service
```

### Generate Summaries with Patterns
```bash
# Include graph patterns in pre-computed summaries
python -m services.summary_generator
```

### Use in Compliance Agent
The compliance agent automatically:
1. Loads cached patterns
2. Filters patterns relevant to query
3. Includes in prompt
4. Uses in compliance assessment

## Configuration

### Thresholds
- `fan_threshold`: Minimum connections for fan patterns (default: 5)
- `cycle_min_length`: Minimum cycle length (default: 3)
- `cycle_max_length`: Maximum cycle length (default: 10)
- `amount_threshold`: Minimum amount for pattern significance (default: 10,000)

### Performance
- Patterns are pre-computed and cached
- Query-time filtering for relevance
- Limits on transaction/account lists for storage

## Files

- `src/tools/analyzers/graph_pattern_detector.py`: Core pattern detection algorithms
- `src/services/graph_analysis_service.py`: Service layer for pattern management
- `src/agents/compliance/compliance_agent.py`: Integration with compliance agent
- `src/services/summary_generator.py`: Pre-computed summary generation

## Future Enhancements

- Temporal pattern detection (patterns over time)
- Weighted graph analysis (amount-based)
- Machine learning pattern classification
- Real-time pattern detection
- Pattern evolution tracking

