# Directory OCR - Automated File Processing Pipeline

An automated file processing system that monitors a folder for incoming files, extracts text using OCR and PDF parsing, and structures data using a local LLM (`llama-server`).

## Features

- **Automatic File Monitoring**: Watches the `incoming` folder for new files
- **Multi-Format Support**: Processes PDFs, JPGs, and PNGs
- **Two-Step Processing**:
  1. **Text Extraction**: OCR for images, text extraction for PDFs
  2. **Data Structuring**: LLM-based extraction of structured data to JSON
- **Intelligent File Management**: Automatically sorts files into `processed` or `errors` folders
- **Configurable Prompts**: Customize prompts for OCR and data extraction via `config.yaml`
- **Robust Error Handling**: Gracefully handles failures without crashing

## Folder Structure

```
directory-ocr/
├── data/           # Data directory
│   ├── incoming/   # Drop files here to process
│   ├── processed/  # Successfully processed source files
│   ├── errors/     # Failed source files
│   └── output/     # Generated .txt and .json files
├── src/            # Application source code
├── config.yaml     # Configuration file
└── start-llm.sh    # Script to start llama-server instances
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
  processed: "data/processed"
  errors: "data/errors"
  output: "data/output"
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
  You are a data extraction assistant. Extract the following information...
  {text}
```

Customize this prompt to extract the specific fields you need!

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

1. **Drop files** into the `data/incoming/` folder
2. The application will automatically:
   - Detect the new file
   - Extract text (Step 1) → saves to `data/output/filename.txt`
   - Extract structured data (Step 2) → saves to `data/output/filename.json`
   - Move source file to `data/processed/` (success) or `data/errors/` (failure)

### Monitor Logs

The application outputs detailed logs to the console:

```
2026-02-09 10:30:15 - src.watcher - INFO - New file detected: invoice.pdf
2026-02-09 10:30:16 - src.file_processor - INFO - Processing file: invoice.pdf
2026-02-09 10:30:18 - src.text_extractor - INFO - Extracting text from PDF: invoice.pdf
2026-02-09 10:30:19 - src.file_processor - INFO - Step 1 complete: invoice.txt
2026-02-09 10:30:25 - src.file_processor - INFO - Step 2 complete: invoice.json
2026-02-09 10:30:25 - src.file_processor - INFO - Successfully processed: invoice.pdf
```

## Workflow

### Step 1: Text Extraction

#### For PDFs
- Uses `PyPDF2` to extract text layer only
- Ignores embedded images/figures
- Saves to `output/filename.txt`

#### For Images (JPG/PNG)
- Sends image to vision LLM on port 8080
- Uses configurable OCR prompt
- Saves transcribed text to `output/filename.txt`

### Step 2: Data Structuring

- Reads the generated `.txt` file
- Sends text to text LLM on port 8081 with custom prompt
- Extracts structured data (e.g., invoice number, date, amount)
- Saves as `output/filename.json`

### File Management

- **Success**: Source file → `processed/`
- **Failure**: Source file → `errors/`
- **Output**: `.txt` and `.json` → `output/`

## Architecture

### Modular Design

```
src/
├── __init__.py           # Package initialization
├── config.py             # Configuration loader
├── llm_client.py         # LLM API client
├── text_extractor.py     # PDF & image text extraction
├── file_processor.py     # Two-step processing orchestrator
├── watcher.py            # File system watcher
└── main.py               # Entry point
```

### Key Components

- **Config**: YAML-based configuration management
- **LLMClient**: OpenAI-compatible API client for llama-server
- **TextExtractor**: Handles PDF parsing and image OCR
- **FileProcessor**: Orchestrates the two-step pipeline
- **DirectoryWatcher**: Monitors incoming folder using `watchdog`

## Error Handling

The application is designed to be resilient:

- ✅ Continues running even if a single file fails
- ✅ Logs all errors with context
- ✅ Moves failed files to `errors/` folder
- ✅ Graceful shutdown on Ctrl+C
- ✅ Validates LLM responses and handles malformed JSON

## Customization

### Adding New File Types

Edit `config.yaml`:

```yaml
processing:
  image_extensions: [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
  pdf_extensions: [".pdf"]
```

### Customizing Extraction Fields

Modify the `extraction_prompt` in `config.yaml` to extract different fields:

```yaml
extraction_prompt: |
  Extract the following from the text:
  - customer_id
  - order_date
  - total_price
  - items (as an array)
  
  Return as JSON.
  
  Text: {text}
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

### PDF Text Extraction Fails

- Ensure PDF has a text layer (not a scanned image)
- For scanned PDFs, convert to images and use OCR

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
