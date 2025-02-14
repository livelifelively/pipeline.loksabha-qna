# Parliament Questions Pipeline

A multi-language pipeline system for processing parliament questions using Temporal.io workflows. The system uses both TypeScript and Python workers to handle different aspects of the pipeline.

## Project Structure

```
├── py-wa/ # Python worker application
│ ├── app/ # Main Python application code
│ │ ├── activities/ # Temporal activities
│ │ ├── pipeline/ # Pipeline implementation
│ │ └── utils/ # Utility functions
│ └── tests/ # Python tests
├── ts-wa/ # TypeScript worker application
│ └── src/ # TypeScript source code
├── package.json # Node.js package configuration
└── .vscode/ # VSCode configuration
```

## Prerequisites

- Node.js (v14+)
- Python (3.8+)
- Temporal server running locally

## Setup

1. Install Node.js dependencies:

```bash
npm install
```

2. Set up Python virtual environment:

```bash
cd py-wa
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Application

The application can be run in two modes:

### Normal Mode

To run without debugging:

1. Modify the start:worker-py script in package.json to remove DEBUG_ENABLED:

```json:package.json
startLine: 8
endLine: 8
```

2. Run the workflow:

```bash
npm run start:workflow
```

### Debug Mode

1. Ensure DEBUG_ENABLED is set in package.json:

```json:package.json
startLine: 8
endLine: 8
```

2. Run the workflow:

```bash
npm run start:workflow
```

## Pipeline Architecture

### Core Components

1. **Pipeline Steps**: Defined using PipelineStep model

```python:py-wa/app/pipeline/types.py
startLine: 35
endLine: 46
```

2. **Progress Tracking**: Comprehensive logging system

```python:py-wa/app/pipeline/progress.py
startLine: 77
endLine: 134
```

3. **Pipeline Orchestration**: Handles step execution and resumability

```python:py-wa/app/pipeline/pipeline.py
startLine: 42
endLine: 157
```

### Features

1. **Progress Tracking**

- Each step's progress is logged
- Supports success, failure, and partial completion states
- Maintains detailed execution history

2. **Resumability**

- Can resume from last successful step
- Maintains state between runs
- Prevents redundant processing

3. **Error Handling**

- Comprehensive error tracking
- Detailed error reporting
- Support for manual intervention

4. **Multi-language Support**

- TypeScript worker for web interactions
- Python worker for data processing
- Seamless integration via Temporal

## Debugging

### Configuration Options

The debugger can be configured using environment variables:

- `DEBUG_ENABLED`: Enable/disable debugging (true/false)
- `DEBUG_HOST`: Host to listen on (default: "0.0.0.0")
- `DEBUG_PORT`: Port to listen on (default: 5678)
- `DEBUG_WAIT`: Whether to wait for debugger (default: "true")

### VS Code Integration

1. Launch configuration is provided in `.vscode/launch.json`:

```json:.vscode/launch.json
startLine: 1
endLine: 21
```

2. To debug:
   - Start the application in debug mode
   - Use VS Code's Run and Debug view to attach
   - Look for the "⏳ Waiting for debugger to attach..." message
   - Debug session starts with "🔍 Debugger attached!" message

### Debug Test Example

A test file is provided for debugging:

```python:py-wa/tests/debug_test.py
startLine: 1
endLine: 10
```

## Error Handling

The system implements a hierarchical error handling system:

```python:py-wa/app/pipeline/exceptions.py
startLine: 1
endLine: 5
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

ISC
