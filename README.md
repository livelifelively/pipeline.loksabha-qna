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

- Node.js (v22+)
- Python (3.12)
- Temporal server running locally

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

## Run CLI

```
npm run start:cli
```

### Pdf extract flow

follow the flow, choose
sansad number (pointer and enter)
session and (pointer and enter)
ministry (select multiple using pointer and space. enter to continue)
enter.

### Commit data changes in data repo

commit by ministry. easy to revert if needed.

## Run Workflows

```
npm run start:workflow:debug
```

once the workflow is running,
