# Parliament Questions Pipeline

A multi-language pipeline system for processing parliament questions using Temporal.io workflows. The system uses both TypeScript and Python workers to handle different aspects of the pipeline.

## Project Structure

```
├── api/
│  └── py/                  # FastAPI REST API
│  └── ts/                  # Express API
├── apps/
│  └── py/                  # Python application logic
│     ├── documents/        # PDF extractors (Marker, Camelot)
│     ├── parliament_questions/  # Document processing & discovery
│     ├── pipeline/         # sansad_session_pipeline entry point
│     ├── types/            # Pydantic models, state machine
│     └── utils/            # Gemini API, PDF utils, project root
│  └── ts/                  # TypeScript application logic
├── cli/
│  └── py/                  # Interactive CLI (InquirerPy)
│     └── extract_pdf/      # PDF extraction & table fix workflows
├── prompts/                # CrewAI pipeline prompts
├── workflows/
│  └── py/                  # Python Temporal worker & activities
│  └── ts/                  # TypeScript Temporal worker & activities
```

## Data Directory

Data lives as a sibling to the `code/` directory under `implementation/`:

```
ls-qna-pipeline/
├── implementation/
│   ├── code/
│   │   └── pipeline.loksabha-qna/   # ← this project (project root)
│   └── data/
│       └── loksabha-qna/            # ← data root
│           └── <sansad>/            # e.g. 17
│               └── <session>/       # e.g. i, ii, iii
│                   └── ministries/
│                       └── <ministry-name>/
│                           └── <question-dir>/
│                               ├── *.pdf
│                               ├── extracted_text.md
│                               └── question.progress.json
```

The path is resolved in `apps/py/utils/project_root.py` relative to the `.project-root` marker:
`project_root.parent (code/) .parent (implementation/) / "data" / "loksabha-qna"`

If the `data/loksabha-qna/` directory doesn't exist, create it before running the pipeline.

## Prerequisites

- Node.js (v22+)
- Python (3.12)
- Temporal server running locally (for workflows only, not needed for CLI)

## Setup

1. Install Node.js dependencies:

```bash
npm install
```

2. Set up and activate Python virtual environment:

```bash
uv venv
source .venv/bin/activate
```

```bash
uv pip install -e "."
uv pip install -e ".[dev]"
```

## PDF Processing Pipeline

The pipeline has two independent stages that run separately.

### Stage 1: Local Extraction (text + table detection)

Extracts text using Marker PDF and detects tables using Camelot. Runs locally, no LLM/API costs.

```bash
npm run start:cli
# → PDF Tools → Extract Text from PDF
```

The CLI presents interactive prompts to select sansad, session, and ministries from whatever directories exist under `data/loksabha-qna/`. Documents already extracted are automatically skipped.

Output per document:

- `extracted_text.md` — full text in Markdown
- `question.progress.json` — state set to `LOCAL_EXTRACTION` with table metadata

### Stage 2: LLM Table Extraction (conditional, Gemini)

Only processes documents where tables were detected in Stage 1. Uses the Gemini vision API; the model name comes from `GEMINI_MODEL` (default `gemini-3.1-flash-lite`, since earlier flash models have been retired or closed to new users).

```bash
npm run start:cli
# → PDF Tools → Fix Tables in Using AI
```

Allows processing all documents, by ministry, or a single document.

### Processing States

```
NOT_STARTED → INITIALIZED → LOCAL_EXTRACTION
                                ├─ has_tables=true  → LLM_EXTRACTION → MANUAL_REVIEW → ...
                                └─ has_tables=false → MANUAL_REVIEW → ...
```

## Initial Processing (Temporal Workflows)

The initial processing step (downloading questions, creating directory structure) runs via Temporal workflows.

**Note:** The sansad and session values are currently hardcoded in the workflow activities:

- `workflows/ts/activities/index.ts` — `sansadSessionPipeline('17', 'iii')`
- `workflows/py/activities/parliament.py` — `sansad_session_pipeline(sansad="17", session="i")`

To process a different sansad/session, update these values before running.

```bash
npm run start:workflow:debug
```

This starts TypeScript and Python Temporal workers concurrently and triggers the workflow.

## Reports

```bash
npm run start:cli
# → Reports
```

Available reports:

- Processing Status Overview
- Ministry Breakdown Report
- Document Details Report

## Commit Data Changes

Commit by ministry in the data repo. Easy to revert if needed.
