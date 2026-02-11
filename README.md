# Directory OCR - Automated File Processing Pipeline

An automated file processing system that monitors a folder for incoming files, extracts text using OCR and PDF parsing, and structures data using a local LLM (`llama-server`).

## Features

- **Automatic Processing Loop**: Continuously processes files in batches
- **Multi-Format Support**: Processes PDFs, JPGs, and PNGs
- **Two-Step Processing**:
  1. **Text Extraction**: OCR for images, text extraction for PDFs → saved to `extracted/`
  2. **Data Matching**: Matches extracted text with CSV reference data → moves matches to `matches/`
- **Intelligent File Management**: Automatically sorts files into appropriate folders
- **Configurable Prompts**: Customize prompts for OCR and matching via `config.yaml`
- **Robust Error Handling**: Gracefully handles failures without crashing

## Folder Structure

```
directory-ocr/
├── data/              # Data directory
│   ├── incoming/      # Drop files here to process
│   ├── extracted/     # Extracted text files (.txt)
│   ├── matches/       # Successfully matched files
│   ├── processed/     # Successfully processed source files
│   ├── errors/        # Failed source files
│   ├── output/        # Legacy output folder
│   └── matchwith.csv  # CSV reference data for matching
├── src/               # Application source code
├── config.yaml        # Configuration file
└── start-llm.sh       # Script to start llama-server instances
```

## Requirements

- **OS**: Linux (all variants)
- **Python**: 3.10 or higher
- **UV**: Python package manager
- **llama-server**: For LLM inference (Vision + Text models)

## Installation

### 1. Install UV (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup

```bash
cd /home/heas/dev/haskoe/directory-ocr
uv sync
```

This will install all dependencies defined in `pyproject.toml`.

### 3. Start LLM Servers

The application requires two `llama-server` instances:
- **Port 8080**: Vision model for OCR (images)
- **Port 8081**: Text model for data extraction

```bash
chmod +x start-llm.sh
./start-llm.sh
```

**Note**: Make sure to update the model paths in `start-llm.sh` to match your system.

## Configuration

Edit `config.yaml` to customize:

### Folder Paths
```yaml
folders:
  incoming: "data/incoming"
  extracted: "data/extracted"
  processed: "data/processed"
  matches: "data/matches"
  errors: "data/errors"
  output: "data/output"
```

### Processing Settings
```yaml
processing:
  match_file: "data/matchwith.csv"
  sleep_time: 2
```

### LLM Endpoints
```yaml
llm:
  vision_endpoint: "http://localhost:8080"
  text_endpoint: "http://localhost:8081"
  timeout: 120
```

### Extraction Prompt (Customizable!)
```yaml
extraction_prompt: |
  You are a data matching assistant. Find the best matching row from CSV...
  {text}
  {match_data}
```

Customize this prompt to change how matching works!

## Usage

### Start the Application

```bash
uv run directory-ocr
```

Or with debug logging:

```bash
uv run directory-ocr --debug
```

Or directly:

```bash
uv run python -m src.main
```

### Processing Files

1. **Prepare reference data**: Create/update `data/matchwith.csv` with columns: `date,description,amount,total`
2. **Drop files** into the `data/incoming/` folder
3. The application will automatically (in a loop every 2 seconds):
   - **Step 1**: Process all files in `incoming/`
     - Extract text → saves to `data/extracted/filename.txt`
     - Move source file to `data/processed/` (success) or `data/errors/` (failure)
   - **Step 2**: If `matchwith.csv` exists and Step 1 processed files
     - Match each file in `extracted/` with CSV rows
     - If match found (confidence ≥ 0.6): Move text file + matched row to `data/matches/`
     - If no match: Keep text file in `extracted/`
   - **Sleep** 2 seconds and repeat

### Monitor Logs

The application outputs detailed logs to the console:

```
2026-02-09 10:30:15 - src.main - INFO - Step 1: Processing 3 file(s) from incoming
2026-02-09 10:30:16 - src.file_processor - INFO - Processing: invoice.pdf
2026-02-09 10:30:18 - src.text_extractor - INFO - Extracting text from PDF: invoice.pdf
2026-02-09 10:30:19 - src.file_processor - INFO - Saved extracted text: invoice.txt
2026-02-09 10:30:19 - src.file_processor - INFO - Step 1 complete: 3/3 files processed successfully
2026-02-09 10:30:19 - src.main - INFO - Step 2: Matching 3 file(s) with matchwith.csv
2026-02-09 10:30:25 - src.file_processor - INFO - Match result for invoice.txt: confidence=0.92, row=3
2026-02-09 10:30:25 - src.file_processor - INFO - Moved invoice.txt to matches
```

## Workflow

### Processing Loop

The application runs in a continuous loop:

1. **Step 1: Text Extraction** - Process all files in `incoming/`
2. **Step 2: Data Matching** - Match extracted text with `matchwith.csv` (only if Step 1 processed files)
3. **Sleep** 2 seconds
4. **Repeat**

### Step 1: Text Extraction

#### For PDFs
- Uses `PyPDF2` to extract text layer only
- Ignores embedded images/figures
- Saves to `extracted/filename.txt`

#### For Images (JPG/PNG)
- Sends image to vision LLM on port 8080
- Uses configurable OCR prompt
- Saves transcribed text to `extracted/filename.txt`

### Step 2: Data Matching

- Reads CSV file `matchwith.csv` with columns: `date,description,amount,total`
- For each `.txt` file in `extracted/`:
  - Sends text + all CSV rows to text LLM on port 8081
  - LLM finds best matching row based on date, description, amount
  - Returns match result with confidence score (0.0 to 1.0)
- If confidence ≥ 0.6:
  - Moves text file to `matches/filename.txt`
  - Saves match result to `matches/filename_match.json`
  - Saves matched CSV row to `matches/filename_matched_row.txt`
- If confidence < 0.6:
  - Keeps text file in `extracted/` for manual review

### File Management

- **Success (Step 1)**: Source file → `processed/`
- **Failure (Step 1)**: Source file → `errors/`
- **Extracted text**: `.txt` → `extracted/`
- **Matched files**: `.txt` → `matches/` (with `_match.json` and `_matched_row.txt`)
- **Unmatched files**: `.txt` remains in `extracted/`

## Architecture

### Modular Design

```
src/
├── __init__.py           # Package initialization
├── config.py             # Configuration loader
├── llm_client.py         # LLM API client
├── text_extractor.py     # PDF & image text extraction
├── file_processor.py     # Two-step processing orchestrator
└── main.py               # Entry point with processing loop
```

### Key Components

- **Config**: YAML-based configuration management
- **LLMClient**: OpenAI-compatible API client for llama-server
- **TextExtractor**: Handles PDF parsing and image OCR
- **FileProcessor**: Orchestrates the two-step pipeline with batch processing
- **Main Loop**: Continuously processes files with configurable sleep intervals

## Error Handling

The application is designed to be resilient:

- ✅ Continues running even if a single file fails
- ✅ Logs all errors with context
- ✅ Moves failed files to `errors/` folder
- ✅ Graceful shutdown on Ctrl+C
- ✅ Validates LLM responses and handles malformed JSON

## Customization

### Configuring Match CSV

Create `data/matchwith.csv` with the following format:

```csv
date,description,amount,total
2025-01-15,Kontorartikler til kontoret,1250.00,1562.50
2025-01-18,Software licens årlig fornyelse,4800.00,6000.00
```

### Adding New File Types

Edit `config.yaml`:

```yaml
processing:
  image_extensions: [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
  pdf_extensions: [".pdf"]
```

### Customizing Match Logic

Modify the `extraction_prompt` in `config.yaml` to change matching criteria:

```yaml
extraction_prompt: |
  You are a data matching assistant...
  Compare based on:
  - Date similarity (weight: 40%)
  - Description similarity (weight: 40%) 
  - Amount similarity (weight: 20%)
  ...
```

### Adjusting Confidence Threshold

Edit `src/file_processor.py` line ~230:

```python
if confidence >= 0.6:  # Change threshold here
```

### Changing Sleep Time

Edit `config.yaml`:

```yaml
processing:
  sleep_time: 5  # seconds between loops
```

### Adjusting LLM Parameters

Modify `src/llm_client.py` to change temperature, max_tokens, etc.

## Troubleshooting

### LLM Servers Not Responding

Check if servers are running:
```bash
curl http://localhost:8080/health
curl http://localhost:8081/health
```

Restart servers:
```bash
./start-llm.sh
```

### Files Not Being Processed

1. Check file extensions match `config.yaml`
2. Enable debug logging: `uv run directory-ocr --debug`
3. Check file permissions in `data/incoming/` folder
4. Verify `data/matchwith.csv` exists for Step 2

### PDF Text Extraction Fails

- Ensure PDF has a text layer (not a scanned image)
- For scanned PDFs, convert to images and use OCR

### Matching Not Working

- Ensure `data/matchwith.csv` exists and has correct format
- Check CSV has header row: `date,description,amount,total`
- Review match results in `matches/filename_match.json`
- Adjust confidence threshold if too strict/loose
- Check LLM text endpoint is responding

### JSON Extraction Returns Null

- Check LLM endpoint is responding
- Review extraction prompt for clarity
- Increase timeout in `config.yaml`

## Development

### Run Tests (when implemented)

```bash
uv run pytest
```

### Code Structure

- Follow modular design principles
- Add logging at INFO level for key operations
- Use DEBUG level for detailed tracing
- Handle exceptions gracefully with try/except

## License

This project is proprietary.

## Support

For issues or questions, contact the development team.
