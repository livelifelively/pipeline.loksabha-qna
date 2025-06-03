# Loksabha QNA Pipeline - Documentation

*This documentation is auto-generated from `docs/diagrams.json`*

**Last updated:** 2025-06-03T09:13:48.780Z
**Total diagrams:** 8

## 🎯 Quick Navigation

### 🖥️ CLI Workflows

- [**Document Processing**](cli/py/extract_pdf/documents.extract_pdf.workflow.mmd) - Individual document processing workflow
- [**Documents.extract Pdf**](cli/py/extract_pdf/documents.extract_pdf.workflow.mmd) - workflow diagram
- [**Extract Pdf**](cli/py/extract_pdf/extract_pdf.workflow.mmd) - workflow diagram
- [**Extract Pdf Contents**](cli/py/extract_pdf/extract_pdf_contents.module.mmd) - module diagram
- [**Extract PDF Workflow**](cli/py/extract_pdf/extract_pdf.workflow.mmd) - Complete PDF text extraction workflow from user selection to results
- [**Fix Tables**](cli/py/extract_pdf/fix_tables.workflow.mmd) - workflow diagram
- [**Fix Tables Workflow**](cli/py/extract_pdf/fix_tables.workflow.mmd) - AI-powered table detection and fixing workflow
- [**Menu**](cli/py/extract_pdf/menu.mmd) - Entry point and navigation flow for PDF processing CLI
- [**Ministry Processing**](cli/py/extract_pdf/ministry.extract_pdf.workflow.mmd) - Ministry-level document processing workflow
- [**Ministry.extract Pdf**](cli/py/extract_pdf/ministry.extract_pdf.workflow.mmd) - workflow diagram
- [**Pdf Page Extraction Ai**](cli/py/extract_pdf/pdf_page_extraction_ai.module.mmd) - module diagram
- [**Pdf Selected Pages Extractor**](cli/py/extract_pdf/pdf_selected_pages_extractor.module.mmd) - module diagram

### ⚙️ Core Components

- [**Page Extractor Module**](cli/py/extract_pdf/pdf_selected_pages_extractor.module.mmd) - Page-level PDF extraction and processing components
- [**PDF Extraction Orchestrator**](cli/py/extract_pdf/pdf_page_extraction_ai.module.mmd) - Core PDF processing engine architecture and component relationships
- [**PDF Extraction Sequence**](cli/py/extract_pdf/pdf_page_extraction_ai.sequence.mmd) - Sequence diagram showing interaction flow in PDF extraction process

### 📊 Domain Logic

- [**PDF Content Extractor**](cli/py/extract_pdf/extract_pdf_contents.module.mmd) - PDF content extraction orchestration and error handling

## 🛠️ Management Commands

```bash
# Discover all diagrams
npm run docs:discover

# Update catalog
npm run docs:update

# Generate this README
npm run docs:generate

# Validate diagram links
npm run docs:validate

# Reorganize files (dry run)
npm run docs:reorganize -- --dry-run
```