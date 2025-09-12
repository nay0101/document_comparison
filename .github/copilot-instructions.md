# Document Comparison System - AI Agent Instructions

This is a multilingual document comparison and compliance system built with Python and Streamlit. The system focuses on PDF document analysis, comparison, and regulatory compliance checking.

## Architecture Overview

### Core Applications

- **Document Comparison** (`app.py`): Compares two multilingual documents to identify discrepancies, mistranslations, and content deviations
- **Guideline Compliance** (`guideline_app.py`): Evaluates documents against regulatory guidelines (e.g., Bank Negara Malaysia standards)

### Key Components

- **Document Parser** (`documentParseJson/md_extractor.py`): Converts PDFs to structured JSON using OpenAI vision models, supports both PDF bytes and image extraction modes
- **Comparison Chain** (`helpers/document_comparison.py`): LangChain-based pipeline that chunks documents and performs semantic comparison
- **Guideline Chain** (`helpers/guideline_comparison.py`): Clause-by-clause compliance evaluation with structured output

## Critical Patterns

### PDF Processing Pipeline

The system uses a multi-stage approach:

1. **Chunking**: PDFs split into manageable chunks (`chunks_document()`)
2. **Parallel Processing**: Uses `ThreadPoolExecutor` for concurrent API calls
3. **Mode Selection**: Either direct PDF processing or image-based extraction
4. **Structured Output**: JSON schema-enforced responses with section grouping

Example usage:

```python
from documentParseJson.md_extractor import extract_layout
extract_layout(pdf_bytes, outdir, mode="image", max_workers=4)
```

### Worker Optimization

- **Small docs (1-10 pages)**: `max_workers=4-6`
- **Medium docs (10-50 pages)**: `max_workers=6-8`
- **Large docs (50+ pages)**: `max_workers=8-12`
- **Production environments**: Use conservative values (4-6) to avoid OpenAI rate limits
- Primary bottleneck is OpenAI API response time (~2-10s per chunk), not CPU

### LangChain Integration

All comparison logic uses LangChain `Runnable` chains:

- Recursive token limit handling for long documents
- Structured prompt templates with XML chunking format
- Callback integration with Langfuse for observability

### Environment-Based Behavior

Set `ENVIRONMENT=development` to enable:

- Debug file outputs (`./chunks/iteration_*.txt`)
- Detailed logging and intermediate results
- Test JSON outputs

## LLM Model Management

### Model Configuration

Models defined in `helpers/types.py` with mappings in `helpers/llm_mappings.py`:

- OpenAI: `gpt-4.1`, `gpt-5`, `o1-mini` (uses responses API with reasoning)
- Anthropic: `claude-3-5-sonnet-latest`, `claude-3-5-haiku-latest`
- Google: `gemini-2.5-flash-preview-05-20`

### Temperature Handling

OpenAI reasoning models don't support temperature - handled in `helpers/llm_integrations.py`

## Document Processing Specifics

### Text Normalization

The system handles multilingual content with specific normalization:

- Bracket removal for TOC matching (`normalize_toc_item()`)
- Trailing number cleanup (e.g., "Products18" → "Products")
- Flexible text matching with overlap ratios

### Section Grouping

Two strategies in `md_extractor.py`:

1. **TOC-based**: Uses table of contents for intelligent sectioning
2. **Fallback**: Header-level based grouping when no TOC detected

## Testing Approach

### Test Structure

- Individual test files for specific features (`test_md_extractor.py`, `test_toc_extraction.py`)
- Jupyter notebooks for exploratory testing (`document_parser_with_json.ipynb`)
- AST parsing for syntax validation without imports

### Common Test Pattern

```python
def test_functions_exist():
    import ast
    with open("documentParseJson/md_extractor.py", "r") as f:
        tree = ast.parse(f.read())
    # Validate function signatures and structure
```

## Development Workflow

### Environment Setup

```bash
python -m venv venv
venv/Scripts/activate  # Windows
pip install -r requirements.txt
cp .env.example .env   # Configure API keys
```

### Running Applications

```bash
# Document comparison (port 8501)
streamlit run app.py --server.port 8501

# Guideline compliance (port 8502)
streamlit run guideline_app.py --server.port 8502
```

### Debugging Guidelines

- Check `./chunks/` directory for intermediate outputs in development mode
- Monitor token usage via `usage.txt` files in output directories
- Use progress callbacks for long-running operations
- Validate JSON schema compliance in structured outputs

## Integration Points

### File System Structure

- `chunks/`: Temporary XML chunks for document processing
- `compared_doc/`: Processed guideline documents
- `guideline_app/`: Extracted sections from compliance documents
- `reports/`: Generated PDF reports

### External Dependencies

- **OpenAI**: Document parsing and comparison (primary)
- **Langfuse**: LLM observability and tracing
- **Streamlit**: Web interface with session state management
- **PyMuPDF/pypdf**: PDF manipulation and chunking

The system prioritizes accuracy over speed, using conservative comparison thresholds and comprehensive validation to ensure reliable multilingual document analysis.
