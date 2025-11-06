# Guideline Comparison Process Documentation

## Overview

The Guideline Comparison System is a sophisticated AI-powered tool that evaluates document compliance against regulatory guidelines (primarily Bank Negara Malaysia standards). The system performs clause-by-clause analysis to determine compliance status, providing detailed assessments and actionable suggestions.

## Architecture Components

### Core System Files

- **`guideline_app.py`**: Main Streamlit application interface
- **`helpers/guideline_comparison.py`**: Core comparison logic using LangChain
- **`helpers/models.py`**: Pydantic models for structured outputs
- **`documentParseJson/md_extractor.py`**: PDF parsing and layout extraction
- **`helpers/document_processor.py`**: Document content processing and filtering

## Process Flow

### 1. Document Ingestion and Preprocessing

#### 1.1 Guideline Document Processing

```
PDF Upload → Layout Extraction → Section Identification → Content Structuring
```

**Key Steps:**

- User uploads regulatory guideline PDF via Streamlit interface
- System uses `extract_layout()` function with OpenAI vision models
- PDF is processed in chunks for parallel processing (4-12 workers depending on size)
- Content is extracted to structured JSON format with sections and images
- Table of Contents (TOC) detection for intelligent sectioning
- Each section includes:
  - Header/title
  - Markdown content
  - Associated images (charts, diagrams, tables)

**Output:** `./guideline_app/sections.json`

```json
{
  "header": "16 Product Disclosure Sheet (PDS)",
  "content_md": "S 16.1 A FSP shall provide a PDS...",
  "images": ["./guideline_app/page_1_section_0.png"]
}
```

#### 1.2 Document-to-Compare Processing

```
PDF Upload → Layout Extraction → Content Chunking → Image Association
```

**Key Steps:**

- User uploads document to be evaluated for compliance
- Same `extract_layout()` process applied
- Document split into logical sections
- Each section processed independently for granular comparison

**Output:** `./compared_doc/sections.json`

### 2. Section Selection and Configuration

#### 2.1 Guideline Section Selection

- User selects specific guideline sections from available options
- System displays full content of selected sections
- Optional attachment selection for additional context

#### 2.2 Attachment Management

- Users can associate supplementary sections as attachments
- Attachments provide additional context for clause interpretation
- Visual pill-based interface for attachment selection

### 3. Comparison Engine

#### 3.1 Chain Initialization

```python
class GuidelineComparisonChain:
    def __init__(self, chat_model_name: Model = "gpt-5", temperature: float = 0.0):
        self.chat_model = get_llm(model=chat_model_name, temperature=temperature)
        self.document_processor = DocumentProcessor()
```

**Supported Models:**

- OpenAI: `gpt-5`, `gpt-4o-2024-11-20`, `o1-mini`
- Google: `gemini-2.5-flash-preview-05-20`
- Claude: `claude-3-5-sonnet-latest`, `claude-3-5-haiku-latest`

#### 3.2 Prompt Engineering

The system uses sophisticated prompt engineering with XML-structured input:

```
# Guideline Section
{guideline_text_and_images}

# Attachments (if any)
{attachment_text_and_images}

# Document to compare against
{document_text_and_images}
```

**Instruction Logic:**

- **Clause Extraction**: Identify blocks starting with `S` (Standard/Mandatory) or `G` (Guidance/Secondary)
- **Applicability Testing**: Determine if clauses apply to the specific document context
- **Verification Rules**:
  - Word-to-word, paragraph-to-paragraph analysis
  - Strict compliance for `S` clauses, lenient for `G` clauses
  - External references mark as "not-applicable"
  - Any doubt results in "non-complied"

#### 3.3 Structured Output Schema

Using Pydantic models for guaranteed response structure:

```python
class ClauseResult(BaseModel):
    clauseNumber: str      # e.g., "S 16.1"
    clause: str           # Full clause text
    isComplied: ComplianceStatus  # "complied" | "non-complied" | "not-applicable"
    reason: str           # Detailed reasoning
    suggestion: str       # Actionable improvement advice (for non-complied)
```

### 4. Multi-Document Processing

#### 4.1 Parallel Section Processing

```python
for section in guidelines:
    for document_chunk in documents:
        result = chain.invoke({
            "guideline": section["clauses"],
            "attachments": section["attachments"],
            "document": document_chunk
        })
```

#### 4.2 Results Aggregation

- Results flattened by clause number across all document sections
- Each clause gets consolidated assessment from all relevant document parts
- Progress tracking with Streamlit progress bars

### 5. Analysis Logic

#### 5.1 Clause Classification

- **Standard (S) Clauses**: Mandatory requirements, evaluated strictly
- **Guidance (G) Clauses**: Best practices, evaluated leniently but still assessed

#### 5.2 Compliance Determination

- **Complied**: Every requirement fully satisfied with clear evidence
- **Non-Complied**: Missing, unclear, contradicted, or partially satisfied requirements
- **Not-Applicable**: Conditional requirements where conditions aren't met

#### 5.3 Evidence Requirements

- Assessment based solely on provided documents
- No external assumptions or unstated facts
- Textual content prioritized over images
- Deterministic and consistent evaluation

### 6. Output Generation

#### 6.1 Structured Results

```json
{
  "section": "16 Product Disclosure Sheet (PDS)",
  "comparisons": [
    {
      "clauseNumber": "S 16.1",
      "clause": "A FSP shall provide a PDS...",
      "results": [
        {
          "snippet": "Document section text...",
          "isComplied": "non-complied",
          "reason": "Missing required disclosure elements...",
          "suggestion": "Add comprehensive risk warning section..."
        }
      ]
    }
  ]
}
```

#### 6.2 Summary Statistics

- Compliance counts by category (Complied/Non-Complied/Not-Applicable)
- Section-wise breakdown
- Clause-level detail with suggestions

### 7. User Interface Features

#### 7.1 Interactive Elements

- File upload with drag-and-drop
- Multi-select for guideline sections
- Attachment association interface
- Real-time progress indicators

#### 7.2 Results Display

- JSON output with collapsible sections
- Color-coded compliance status
- Detailed reasoning for each assessment
- Downloadable PDF reports (when enabled)

#### 7.3 Session Management

- Unique session IDs for tracking
- Persistent state across interactions
- Model selection dropdown

### 8. Performance Optimization

#### 8.1 Parallel Processing

- Concurrent PDF chunk processing
- ThreadPoolExecutor for API calls
- Optimized worker counts based on document size

#### 8.2 Caching and State Management

- Streamlit session state for processed documents
- Temporary file cleanup
- Progress callback integration

### 9. Error Handling and Validation

#### 9.1 Input Validation

- PDF format verification
- File size limits
- Content structure validation

#### 9.2 Model Response Validation

- Pydantic schema enforcement
- JSON structure verification
- Fallback handling for parsing errors

### 10. Development and Debugging

#### 10.1 Development Mode

Set `ENVIRONMENT=development` for:

- Debug file outputs in `./chunks/`
- Detailed logging
- Intermediate result storage
- Test JSON outputs

#### 10.2 Observability

- Langfuse integration for LLM tracing
- Session tracking with unique IDs
- Performance metrics collection

## Configuration Options

### Model Selection

- Default: `gpt-5`
- Available: OpenAI, Anthropic, Google models
- Temperature control (0.0 for consistency)

### Processing Parameters

- Max workers: 4-12 (based on document size)
- Mode: "image" for visual processing
- Verbosity levels: minimal, medium, full
- Progress callback support

## Best Practices

### For Guideline Documents

- Ensure clear section headers
- Include relevant attachments
- Use documents with well-defined clause structures

### For Compliance Documents

- Provide complete documents
- Include all relevant sections
- Ensure good image quality for visual elements

### Performance Optimization

- Use conservative worker counts in production
- Monitor OpenAI API rate limits
- Implement proper error handling for long documents

## Limitations and Considerations

1. **Token Limits**: Large documents may require chunking
2. **API Dependencies**: Relies on external LLM services
3. **Language Support**: Optimized for English regulatory documents
4. **Visual Processing**: Images supplementary to text analysis
5. **Context Length**: Very long clauses may be truncated

## Integration Points

### External Services

- **OpenAI API**: Primary LLM provider
- **Langfuse**: Observability and tracing
- **Streamlit**: Web interface framework

### File System Structure

```
./guideline_app/          # Processed guideline sections
./compared_doc/           # Processed compliance documents
./chunks/                 # Temporary processing files
./reports/               # Generated reports (when enabled)
```

This documentation provides a comprehensive overview of the guideline comparison process, from document ingestion through final compliance assessment, enabling developers and users to understand and effectively utilize the system.
