# Guideline Comparison — Documentation

## What this app does

The Guideline Comparison app evaluates whether a target document complies with clauses in a regulatory guideline (e.g., Bank Negara Malaysia). It:

- Splits the guideline into selectable sections (header + Markdown text + referenced images)
- Extracts every clause that starts with `S` or `G` (e.g., `S 16.1`, `G 16.2`)
- Compares each clause against the target document content (and images), section by section
- Returns per-clause outcomes: `complied` / `non-complied` / `not-applicable`, with reasons and suggestions
- Exports a PDF report of the results

The Streamlit UI entrypoint is `guideline_app.py`.

## Workflow (end-to-end)

1. **Pre-process PDFs into sections** (`documentParseJson/md_extractor.py:extract_layout`)
   - **Input:** Guideline PDF bytes/file and document PDF bytes/file.
   - **Transform:** OpenAI multimodal layout extraction + post-processing into logical sections.
   - **Output files:**
     - `./guideline_app/sections.json`
     - `./compared_doc/sections.json`
   - **Data shape:** each entry is typically:
     - `{"header": "<section title>", "content_md": "<markdown>", "images": ["<path>", ...]}`
2. **Load guideline sections into UI** (`guideline_app.py`)
   - **Input:** `./guideline_app/sections.json`.
   - **Transform:** `json.loads(...)` → `ss.sections` (list of section dicts) and `ss.titles` (list of headers).
   - **Output:** `ss.titles` becomes the options for section selection.
3. **Select sections + attachments** (`guideline_app.py`)
   - **Input:** User selection(s) from `ss.titles`.
   - **Transform:**
     - Selected headers → `ss.clauses` (subset of `ss.sections`)
     - For each selected guideline section, optional attachment headers → attachment section dicts.
   - **Output (in session state):**
     - `ss.clauses`: list of `{header, content_md, images}`
     - Per-section attachment payloads: list of `{header, content_md, images}`
4. **Load document sections to compare** (`guideline_app.py`)
   - **Input:** `./compared_doc/sections.json`.
   - **Transform:** `json.loads(...)` → `documents` list:
     - `{"text": section["content_md"], "images": section.get("images", [])}`
   - **Output:** `documents: List[{"text": str, "images": List[str]}]`
5. **Build comparison input payload** (click **Compare** in `guideline_app.py`)
   - **Input:** `ss.clauses` + selected attachments.
   - **Transform:** Build `ss.guideline_info`:
     - `{"clauses": {"text": <content_md>, "images": <paths>}, "title": <header>, "attachments": [{"text": ..., "images": ..., "header": ...}, ...]}`
   - **Output:** `guidelines: List[GuidelineInfo-like dict]` passed to the chain.
6. **Run LLM per (guideline section × document section)** (`helpers/guideline_comparison.py`)
   - **Input:** one guideline item + one document item.
   - **Transform (prompt building in `formatted_prompt`)**:
     - Image file paths are read → base64 → inserted as `{"type":"image_url","image_url":{"url":"data:image/png;base64,..."}}`
     - Text blocks are inserted as `{"type":"text","text":"..."}`
   - **Model call:** `with_structured_output(ClauseComparisonReport)` ensures the model returns `{"results":[...ClauseResult...]}`.
   - **Output:** For each document section, a parsed `ClauseComparisonReport` that is then converted to JSON and stored with:
     - `snippet = document["text"]`
7. **Aggregate results by clause** (`helpers/guideline_comparison.py:loop_invoke`)
   - **Input:** many `ClauseComparisonReport` objects across all document sections.
   - **Transform:** Flatten into:
     - one entry per `clauseId`, where `results` is a list of `{snippet, isComplied, reason, suggestions}` across document sections.
   - **Output:** `List[FinalComparisonResult]` (Pydantic), returned to `guideline_app.py`.
8. **Render + export** (`guideline_app.py` + `helpers/reports.py`)
   - **Input:** `ss.result: List[FinalComparisonResult]`.
   - **Transform (export):** `MarkdownPDFConverter.generate_guideline_report(...)` builds Markdown → converts to PDF bytes.
   - **Output:** Downloadable `report.pdf`.

## Quickstart

1. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment:

```bash
cp .env.example .env
```

Set at least `OPENAI_API_KEY` (or other supported provider keys; see “Configuration”).

3. Ensure `sections.json` exists for:

- The uploaded guideline: `./guideline_app/sections.json`
- The document being assessed: `./compared_doc/sections.json`

The app currently reads these files directly (see “Pre-processing PDFs into `sections.json`”).

4. Run the app:

```bash
streamlit run guideline_app.py --server.port 8502
```

## Pre-processing PDFs into `sections.json`

`guideline_app.py` expects pre-extracted layout JSON. Layout extraction is implemented in `documentParseJson/md_extractor.py:extract_layout`.

Typical workflow (run once per PDF):

- Guideline PDF → `./guideline_app/sections.json`
- Target document PDF → `./compared_doc/sections.json`

If you prefer automatic generation inside the Streamlit app, `guideline_app.py` already contains commented `extract_layout(...)` calls you can enable.

## How to use (UI)

1. Upload a guideline PDF (“Central Bank Guideline Document”)
2. Select one or more guideline sections to compare
3. Optionally select “attachments” (additional sections) per selected guideline section
4. Upload the target document PDF (used to enable the Compare button; document parsing currently reads from `./compared_doc/sections.json`)
5. Click **Compare**
6. Review results and download the PDF report

## Output shape

The in-memory result is a list of `FinalComparisonResult` items (`helpers/models.py`):

```json
[
  {
    "section": "Guideline section title",
    "comparisons": [
      {
        "clauseId": "S 16.1",
        "clause": "S 16.1 ...full clause text...",
        "results": [
          {
            "snippet": "Document excerpt (one document section)",
            "isComplied": "non-complied",
            "reason": "...",
            "suggestions": ["...", "..."]
          }
        ]
      }
    ]
  }
]
```

The PDF report is generated by `helpers/reports.py:MarkdownPDFConverter.generate_guideline_report`.

## How it works (code map)

- `guideline_app.py`: Streamlit UI, section selection, attachment selection, report download
- `helpers/guideline_comparison.py:GuidelineComparisonChain`
  - Builds a multimodal prompt containing:
    - Guideline section text + images
    - Attachment text + images (optional)
    - Document section text + images
  - Uses structured outputs (`helpers/models.py:ClauseComparisonReport`) to enforce JSON shape
  - Aggregates results across all document sections and flattens them by `clauseId`
- `helpers/models.py`: Pydantic models for:
  - Per-clause structured output (`ClauseResult`)
  - Final aggregated output (`FinalComparisonResult`)

## Function reference

### `guideline_app.py` (Streamlit UI)

- Session/state initialization:

  - Creates/clears `ss.result`, `ss.chat_id`, `ss.sections`, `ss.clauses`, `ss.titles`, `ss.guideline_info`, etc.
  - Uses `ss.out_dir = Path("./guideline_app").resolve()` and `ss.compared_doc_dir = Path("./compared_doc").resolve()`.

- Guideline upload + section list:

  - Reads `output_file = f"{ss.out_dir}/sections.json"` and populates:
    - `ss.sections` (raw JSON objects)
    - `ss.titles` (section headers)
  - `st.multiselect(..., options=ss.titles)` selects which sections become `ss.clauses`.

- Attachments:

  - For each selected guideline section, the UI allows selecting additional section headers as attachments.
  - Attachment payload used later is a list of `{text, images, header}`.

- Compare action (`compare_btn`):

  - Builds `ss.guideline_info` (selected sections + attachments + images).
  - Loads the document sections from `./compared_doc/sections.json` into a list of `{text, images}`.
  - Calls `GuidelineComparisonChain.invoke_chain(guidelines=..., documents=..., chat_id=...)`.

- Results rendering + export:
  - Iterates `FinalComparisonResult` objects and shows compliance status per snippet.
  - Exports via `MarkdownPDFConverter.generate_guideline_report(...)`.

### `helpers/guideline_comparison.py:GuidelineComparisonChain`

- `__init__(chat_model_name="gpt-5", temperature=0.0, instruction=None)`

  - Constructs the LLM via `helpers/llm_integrations.py:get_llm`.
  - Constructs a `DocumentProcessor` (not required for the core loop, but available).

- `_guideline_comparison_chain() -> Runnable`

  - Defines two important inner functions:
    - `formatted_prompt(_input) -> ChatPromptTemplate`
      - Creates the multimodal user message:
        - Guideline text + base64-encoded images from file paths
        - Attachment text + images (optional)
        - Document section text + images
      - Provides a strict system instruction to:
        - Extract clauses starting with `S`/`G`
        - Return one result per clause with `clauseId`, `clause`, `isComplied`, `reason`, `suggestions`
        - Output only JSON
    - `loop_invoke(_input) -> List[FinalComparisonResult]`
      - Iterates `guidelines` × `documents`.
      - Invokes the model with `with_structured_output(ClauseComparisonReport)`.
      - Attaches the current document section’s text as `snippet`.
      - Flattens all results by `clauseId` across document sections so each clause has many `results`.
  - Returns `RunnableLambda(loop_invoke)`.

- `invoke_chain(guidelines, documents, chat_id=None) -> List[FinalComparisonResult]`
  - Invokes `_guideline_comparison_chain()` with Langfuse callbacks.
  - Returns the aggregated `FinalComparisonResult` list.

### `documentParseJson/md_extractor.py` (layout extraction)

- `extract_layout(pdf, outdir, mode="pdf"|"image", pages_per_chunk=1, max_workers=4, model="gpt-5-nano", ...) -> dict`
  - Splits a PDF into chunks (PDF chunks or page images depending on `mode`).
  - Calls an OpenAI model in parallel to extract structured layout.
  - Writes artifacts into `outdir` and produces a sectioned JSON (used by the app as `sections.json`).

## Configuration

Environment variables are defined in `.env.example`:

- `OPENAI_API_KEY`: required for OpenAI models
- `GOOGLE_API_KEY`: required if you select a Gemini model in the sidebar
- `ANTHROPIC_API_KEY`: required if you use Claude models
- `LANGFUSE_*`: optional (Langfuse tracing via callbacks)
- `ENVIRONMENT`: optional (some extra logging/output is gated by `ENVIRONMENT=development`)
