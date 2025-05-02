# Parliament Questions Pipeline

A multi-language pipeline system for processing parliament questions using Temporal.io workflows. The system uses both TypeScript and Python workers to handle different aspects of the pipeline.

## Project Structure

```
├── .vscode/
├── api/
│  └── py/
│  └── ts/
├── apps/
│  └── py/
│  └── ts/
├── prompts/
├── workflows/
│  └── py/
│  └── ts/
├── package.json
```

## Prerequisites

- Node.js (v14+)
- Python (3.12)
- Temporal server running locally

## Setup

1. Install Node.js dependencies:

```bash
npm install
```

2. Set up Python virtual environment:

```bash
uv pip install -e "."
uv pip install -e ".[dev]"
```

## Run Workflow

```
npm run start:workflow:debug
```

once the workflow is running,
