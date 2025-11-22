# Streamlit UI Guide

## Quick Start

### 1. Install Dependencies

```bash
cd LHubs
pip install -r requirements.txt
```

### 2. Start the API Server

In one terminal:

```bash
cd LHubs
python -m src.main
```

Or using uvicorn:

```bash
cd LHubs
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### 3. Start the Streamlit UI

In another terminal:

```bash
cd LHubs
streamlit run streamlit_app.py
```

The UI will open in your browser at `http://localhost:8501`

## Using the UI

### Upload Files

1. Click "Browse files" in the upload section
2. Select one or more CSV files (or other supported formats)
3. Files will be displayed in a preview table
4. Click "🚀 Process Files" to analyze the data

### Test Files

Sample test files are available in the `data/` directory:

- `data/test_transactions.csv` - Sample transaction data
- `data/test_accounts.csv` - Sample account data  
- `data/test_client_notes.txt` - Sample client notes

You can use these files to test the system.

### View Results

After processing, you'll see:

- **Risk Score** - Overall risk assessment (0-100)
- **Executive Summary** - High-level findings
- **Red Flags** - Detected AML red flags
- **Inconsistencies** - Data quality issues
- **SAR Recommendation** - Filing recommendation with reasoning

### Download Results

Click "📥 Download JSON Report" to save the complete casefile as JSON.

## Configuration

### Change API Endpoint

In the Streamlit UI sidebar, you can modify the API host if your API is running on a different address or port.

### File Format

The system expects CSV files with transaction data. Supported columns include:

- Transaction ID
- Date
- Amount
- Currency
- Account ID
- Transfer Type
- Counterparty Account ID
- External Counterparty Country

## Troubleshooting

### "Could not connect to API"

- Make sure the API server is running
- Check that the API host in the sidebar matches your API server address
- Verify the API is accessible at the configured port (default: 8000)

### "Error processing files"

- Check the API server logs for detailed error messages
- Ensure uploaded files are in the correct format
- Verify file paths and permissions

### Files not uploading

- Check file size (max 100MB by default)
- Ensure file format is supported (.csv, .txt, .json)
- Try uploading one file at a time

## Features

- ✅ Multi-file upload support
- ✅ File preview before processing
- ✅ Real-time processing status
- ✅ Comprehensive results display
- ✅ JSON report download
- ✅ Responsive design

