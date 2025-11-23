# What to Run - Step by Step

## Step 1: Install Dependencies

```bash
cd /workspace/LHubs_Zafira
pip install -r requirements.txt
```

This installs:
- `networkx` - Graph analysis
- `matplotlib` - Visualizations
- `reportlab` - PDF generation
- `openpyxl` - Excel reading
- `streamlit` - Web interface
- All other dependencies

## Step 2: Choose How to Run

### Option A: Streamlit Web App (Easiest for Demo) ⭐

```bash
cd /workspace/LHubs_Zafira
streamlit run streamlit_aml_app.py
```

Then:
1. Browser opens automatically (or go to http://localhost:8501)
2. Upload Excel file via web interface
3. Click "Analyze for AML Patterns"
4. View results and download PDF

### Option B: Command Line Script

```bash
cd /workspace/LHubs_Zafira
python run_aml_analysis.py <path_to_excel_file.xlsx>
```

Example:
```bash
python run_aml_analysis.py /workspace/data/sample.xlsx
```

### Option C: Python API

```python
import sys
sys.path.insert(0, 'src')

from agents.aml_analysis import AMLAnalysisAgent

agent = AMLAnalysisAgent()
result = agent.process({
    "excel_file_path": "path/to/file.xlsx"
})

print(result["summary"])
```

## Step 3: Prepare Your Excel File

Your Excel file needs:

**Sheet 1: Accounts** (sheet name should contain "account")
- `Account ID` or `IBAN` column
- `Account Holder` or `Name` (optional)

**Sheet 2: Transactions** (sheet name should contain "transaction")
- `From Account` or `Sender` column
- `To Account` or `Receiver` column  
- `Amount` column
- `Date` (optional)
- `Transaction Type` (optional)

## What Happens When You Run

1. ✅ Excel file is loaded (accounts + transactions)
2. ✅ Transaction graph is constructed
3. ✅ AML patterns are detected (algorithmic, before LLM)
4. ✅ AML context rules explain each pattern
5. ✅ Risk assessment is calculated
6. ✅ PDF report is generated with visualizations
7. ✅ Results are displayed/downloaded

## Expected Output

### Console Output:
```
Analysis Results:
- Patterns Detected: 15
- Risk Level: HIGH
- Recommendation: Enhanced due diligence required...

Pattern Breakdown:
  - Fan Out: 8
  - Fan In: 4
  - Gather Scatter: 2
  - Simple Cycle: 1

✓ PDF Report Generated: /tmp/aml_analysis_report.pdf
```

### PDF Report Contains:
- Executive Summary
- Data Overview
- Pattern Detections (with AML context)
- 4 Visualizations:
  - Transaction Network Graph
  - Pattern-Highlighted Subgraph
  - Fund Flow Diagram
  - Risk Heatmap

## Quick Test

If you don't have an Excel file yet, you can test the system by:

1. Creating a simple Excel file with test data
2. Or use the existing transaction data format

## Troubleshooting

### "ModuleNotFoundError"
→ Run: `pip install -r requirements.txt`

### "No transactions found"
→ Check Excel file has correct column names
→ Verify sheet names contain "account" and "transaction"

### "Import errors"
→ Make sure you're in `/workspace/LHubs_Zafira` directory
→ Check that `src` directory exists

## Files You Can Run

1. **`streamlit_aml_app.py`** - Web interface (recommended)
2. **`run_aml_analysis.py`** - Command-line script
3. **`run_graph_analysis.py`** - Just graph pattern detection (for testing)

## Summary

**For Demo/Testing:**
```bash
pip install -r requirements.txt
streamlit run streamlit_aml_app.py
```

**For Production/API:**
```python
from agents.aml_analysis import AMLAnalysisAgent
agent = AMLAnalysisAgent()
result = agent.process({"excel_file_path": "file.xlsx"})
```

That's it! The system is ready to analyze Excel files and generate AML compliance reports.

