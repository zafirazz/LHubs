# AML Agent Architecture - Simple Context-Based Design

## Overview

**Simple, Clean Architecture:**
1. 🎓 **Training Phase**: Agent learns from `/workspace/data/` (one-time context loading)
2. 📤 **Runtime Phase**: Upload complete CSV/Excel → Analyze → Generate report
3. ❌ **No complex database lookups during runtime**

---

## Phase 1: Context/Training Layer

### Purpose
Give the agent **background knowledge** about:
- Normal transaction patterns
- FINMA regulations
- Reporting thresholds (e.g., 10,000 CHF)
- Known AML typologies
- Baseline statistical patterns

### Data Sources (`/workspace/data/`)
```
/workspace/data/
├── transactions.csv       # Historical transaction data
├── accounts.csv           # Account information
├── br_to_account.csv      # Account relationships
└── ...                    # Other regulatory/context files
```

### Components

#### 1. **ContextService** (`src/services/context_service.py`)
- Loads data from `/workspace/data/`
- Creates embeddings using `sentence-transformers/all-MiniLM-L6-v2`
- Stores in vector database (ChromaDB)
- Provides semantic search for compliance queries

**Purpose:** Answer questions like "What are normal transaction patterns for Swiss accounts?"

#### 2. **AMLContextRulesEngine** (`src/services/aml_context_rules.py`)
- Hardcoded FINMA regulations
- Pattern definitions (fan-out, fan-in, circular flow, etc.)
- Risk level mappings
- Compliance implications
- Recommended actions

**Purpose:** Explain detected patterns with regulatory context

#### 3. **GraphAnalysisService** (`src/services/graph_analysis_service.py`)
- Pre-computes patterns from training data
- Builds baseline understanding of transaction graphs
- Fan threshold: 3 transactions
- Amount threshold: 10,000 CHF

**Purpose:** Understand what normal vs. suspicious graph patterns look like

---

## Phase 2: Runtime Analysis (Upload → Analyze → Report)

### User Workflow
```
1. User uploads CSV/Excel with:
   - Accounts (account_id, IBAN)
   - Transactions (from, to, amount, date, etc.)

2. Agent processes:
   ├── Load data from uploaded file (NOT from database)
   ├── Build transaction graph
   ├── Detect patterns (fan-out, fan-in, cycles, etc.)
   ├── Apply context from training data
   ├── Assess risk level
   └── Generate PDF report

3. User downloads PDF with findings
```

### Components

#### 1. **ExcelLoader** (`src/services/excel_loader.py`)
```python
# BEFORE (Wrong - Complex):
upload accounts → lookup transactions from database → analyze

# AFTER (Correct - Simple):
upload accounts + transactions → analyze
```

**Key Methods:**
- `load_from_bytes()`: Loads Excel/CSV from Streamlit upload
- `_normalize_accounts()`: Standardizes account data
- `_normalize_transactions()`: Standardizes transaction data

**No database lookups!**

#### 2. **AMLAnalysisAgent** (`src/agents/aml_analysis/aml_analysis_agent.py`)
Main agent that orchestrates analysis:

```python
def process(self, input_data):
    # 1. Load uploaded data
    data = self.excel_loader.load_from_bytes(excel_bytes)
    accounts = data["accounts"]
    transactions = data["transactions"]
    
    # 2. Detect patterns using graph analysis
    patterns = self.pattern_detector.detect_all_patterns(transactions)
    
    # 3. Apply AML context rules (from training)
    explanations = self.aml_rules.explain_pattern(pattern)
    
    # 4. Assess risk
    risk = self.aml_rules.assess_risk(patterns)
    
    # 5. Generate PDF report
    pdf = self.pdf_generator.generate_report(...)
    
    return {
        "patterns_detected": patterns,
        "risk_assessment": risk,
        "pdf_bytes": pdf
    }
```

#### 3. **GraphPatternDetector** (`src/tools/analyzers/graph_pattern_detector.py`)
Detects AML patterns:
- **Fan-Out**: One account → many accounts (structuring/smurfing)
- **Fan-In**: Many accounts → one account (layering)
- **Gather-Scatter**: Fan-in followed by fan-out (integration)
- **Simple Cycle**: Circular money flow (obfuscation)
- **U-Turn**: Money returns to source (wash trading)

#### 4. **PDFReportGenerator** (`src/services/pdf_report_generator.py`)
Creates comprehensive PDF with:
- Executive summary
- Pattern detections with regulatory context
- 4 visualizations:
  - Transaction network graph
  - Pattern-highlighted subgraph
  - Fund flow diagram
  - Risk heatmap

---

## Data Flow Diagram

```
┌─────────────────────────────────────────┐
│       TRAINING PHASE (One-Time)         │
├─────────────────────────────────────────┤
│                                         │
│  /workspace/data/                       │
│  ├── transactions.csv                   │
│  ├── accounts.csv                       │
│  └── ...                                │
│           ↓                             │
│  ContextService (Vector DB)             │
│  AMLContextRulesEngine (FINMA Rules)    │
│  GraphAnalysisService (Baselines)       │
│                                         │
│  Result: Agent has "knowledge"          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         RUNTIME PHASE (Per Upload)      │
├─────────────────────────────────────────┤
│                                         │
│  User Uploads: accounts_and_txns.csv    │
│           ↓                             │
│  ExcelLoader.load_from_bytes()          │
│           ↓                             │
│  GraphPatternDetector                   │
│    - Build graph from uploaded data     │
│    - Detect patterns                    │
│           ↓                             │
│  AMLContextRulesEngine                  │
│    - Apply regulatory context           │
│    - Explain patterns                   │
│           ↓                             │
│  PDFReportGenerator                     │
│    - Create visualizations              │
│    - Generate PDF                       │
│           ↓                             │
│  User Downloads: aml_report.pdf         │
│                                         │
└─────────────────────────────────────────┘
```

---

## Key Design Principles

### ✅ DO
1. **Simple data flow**: Upload complete file → analyze → report
2. **Context from training data**: Use `/workspace/data/` for background knowledge
3. **Graph-based detection**: Real algorithms, not just LLM guessing
4. **Regulatory grounding**: Every pattern explained with FINMA context
5. **Guardrails**: No invented rules, no false accusations

### ❌ DON'T
1. **No runtime database lookups**: Everything in uploaded file
2. **No complex joins**: Keep it simple
3. **No policy hallucination**: Only use established rules
4. **No criminal accusations**: Patterns ≠ proof of crime

---

## File Format Requirements

### Option 1: Excel with Two Sheets
```
Sheet 1: Accounts
- account_id (required)
- account_iban (optional)
- account_holder (optional)

Sheet 2: Transactions
- transaction_id (required)
- from_account (required)
- to_account (required)
- amount (required)
- currency (optional, default: CHF)
- date (optional)
- type (optional)
```

### Option 2: Single CSV
Combine all columns in one CSV file.

### Example Files
- `/workspace/example_complete_upload.csv` - Sample data with red flags
- `/workspace/example_excel_format.md` - Format documentation

---

## Testing

### Quick Test
```bash
cd /workspace/LHubs_Zafira
streamlit run streamlit_aml_app.py
```

Then upload: `/workspace/example_complete_upload.csv`

### Expected Output
- ✅ Loads 9 accounts
- ✅ Loads 13 transactions
- ✅ Detects multiple patterns (fan-out, fan-in, structuring)
- ✅ High risk assessment
- ✅ PDF report with 4 visualizations

---

## Architecture Benefits

1. **🚀 Fast**: No database queries during analysis
2. **🎯 Simple**: Easy to understand and debug
3. **🔒 Secure**: No data persistence, no database
4. **📊 Transparent**: Clear what data agent sees
5. **🧪 Testable**: Easy to create test cases
6. **🎓 Explainable**: Context-based reasoning

---

## Future Enhancements (if needed)

- [ ] Add more AML typologies (trade-based laundering, etc.)
- [ ] Support more file formats (JSON, Parquet)
- [ ] Batch processing for multiple files
- [ ] Real-time streaming analysis
- [ ] Integration with external AML databases

But keep it simple for now! 🎯
