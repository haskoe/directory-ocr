# Quick Start Guide

## 1. Install Dependencies

```bash
# Install UV if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

## 2. Configure

Edit `config.yaml` if you need to customize:
- Folder paths
- LLM endpoints
- Extraction prompts

## 3. Start LLM Servers

```bash
# Make sure to update model paths in start-llm.sh first!
chmod +x start-llm.sh
./start-llm.sh
```

This starts:
- Vision model on port 8080 (for OCR)
- Text model on port 8081 (for data extraction)

## 4. Run the Application

```bash
# Normal mode
uv run directory-ocr

# Or with debug logging
uv run directory-ocr --debug

# Or directly
uv run python -m src.main
```

## 5. Test It

Drop a file into the `data/incoming/` folder:
- PDF: `invoice.pdf`
- Image: `receipt.jpg`

Watch the console output for processing status.

Check the results:
- `data/output/invoice.txt` - extracted text
- `data/output/invoice.json` - structured data
- `data/processed/invoice.pdf` - original file (on success)

## Common Commands

```bash
# View logs in real-time
uv run directory-ocr

# Stop the application
Ctrl+C

# Check if LLM servers are running
curl http://localhost:8080/health
curl http://localhost:8081/health

# View folder structure
tree -L 1
```

## Troubleshooting

**Application won't start:**
- Check that `config.yaml` exists
- Verify UV is installed: `uv --version`

**Files not being processed:**
- Ensure LLM servers are running
- Check file extensions match config
- Enable debug mode

**LLM errors:**
- Check server health endpoints
- Review model paths in `start-llm.sh`
- Check available VRAM/memory
