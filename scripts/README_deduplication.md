# Failed Downloads Deduplication Script (TypeScript)

This script removes duplicate entries from `failed_sansad_session_question_download` that also exist in `downloaded_sansad_session_questions`.

## Problem

When processing parliament questions, some questions might appear in both:

- `failed_sansad_session_question_download`: Questions that failed to download initially
- `downloaded_sansad_session_questions`: Questions that were successfully downloaded

This creates inconsistencies in the data. The script removes these duplicates from the failed downloads list.

## Prerequisites

- Node.js 14+
- TypeScript support (ts-node or compiled JavaScript)

## Installation

If you don't have ts-node installed globally:

```bash
npm install -g ts-node
# or
npm install -g typescript ts-node
```

## Usage

### Process a single file

```bash
npx ts-node deduplicate_failed_downloads.ts path/to/your/file.log.json
```

### Process all log files in a directory

```bash
npx ts-node deduplicate_failed_downloads.ts path/to/logs/directory/
```

### Process with custom file pattern

```bash
npx ts-node deduplicate_failed_downloads.ts path/to/logs/directory/ --pattern "*.json"
```

### Process without creating backups

```bash
npx ts-node deduplicate_failed_downloads.ts path/to/your/file.log.json --no-backup
```

### Enable debug logging

```bash
npx ts-node deduplicate_failed_downloads.ts path/to/your/file.log.json --debug
```

### Show help

```bash
npx ts-node deduplicate_failed_downloads.ts --help
```

## How it works

1. **Loads JSON data** from the specified file(s)
2. **Creates a lookup set** from `downloaded_sansad_session_questions` using `(question_number, questions_file_path_web)` as the unique key
3. **Filters failed downloads** by removing entries that exist in the downloaded questions set
4. **Saves the updated data** back to the file (with optional backup)

## Example

### Before deduplication:

```json
{
  "data": {
    "failed_sansad_session_question_download": [
      {
        "questions_file_path_web": "https://example.com/question1.pdf",
        "question_number": 1001,
        "type": "STARRED"
      },
      {
        "questions_file_path_web": "https://example.com/question2.pdf",
        "question_number": 1002,
        "type": "UNSTARRED"
      }
    ],
    "downloaded_sansad_session_questions": [
      {
        "question_number": 1001,
        "questions_file_path_web": "https://example.com/question1.pdf",
        "type": "STARRED"
        // ... other fields
      }
    ]
  }
}
```

### After deduplication:

```json
{
  "data": {
    "failed_sansad_session_question_download": [
      {
        "questions_file_path_web": "https://example.com/question2.pdf",
        "question_number": 1002,
        "type": "UNSTARRED"
      }
    ],
    "downloaded_sansad_session_questions": [
      {
        "question_number": 1001,
        "questions_file_path_web": "https://example.com/question1.pdf",
        "type": "STARRED"
        // ... other fields
      }
    ]
  }
}
```

## TypeScript Features

- **Strong typing**: Full TypeScript interfaces for all data structures
- **Type safety**: Compile-time checking for data structure consistency
- **Modern async/await**: Clean asynchronous file operations
- **Modular design**: Exportable functions for use in other TypeScript modules

## Safety Features

- **Automatic backups**: Creates `.json.backup` files before processing (unless `--no-backup` is used)
- **Error handling**: Continues processing other files if one fails
- **Logging**: Provides detailed information about what was removed
- **Validation**: Checks for required fields before processing
- **Type checking**: Ensures data structure integrity

## Requirements

- Node.js 14+
- TypeScript support (ts-node or compiled JavaScript)
- No external dependencies (uses only Node.js standard library)

## File Structure

The script expects JSON files with this structure:

```json
{
  "data": {
    "failed_sansad_session_question_download": [...],
    "downloaded_sansad_session_questions": [...]
  }
}
```

## Type Definitions

The script includes TypeScript interfaces for type safety:

```typescript
interface FailedQuestionDownload {
  questions_file_path_web: string;
  question_number: number;
  type: 'STARRED' | 'UNSTARRED';
}

interface ParliamentQuestion {
  question_number: number;
  subjects: string;
  loksabha_number: string;
  member: string[];
  ministry: string;
  type: 'STARRED' | 'UNSTARRED';
  date: string;
  questions_file_path_local: string | null;
  questions_file_path_web: string;
  questions_file_path_hindi_local: string | null;
  questions_file_path_hindi_web: string;
  question_text: string | null;
  answer_text: string | null;
  session_number: string;
}
```

## Troubleshooting

### Common Issues

1. **"ts-node not found"**

   ```bash
   npm install -g ts-node typescript
   ```

2. **"Permission denied"**

   ```bash
   # Make sure you have write permissions to the target directory
   chmod +w path/to/your/directory/
   ```

3. **"No files found"**

   - Check that the file pattern matches your files
   - Use `--debug` flag to see what files are being processed

4. **"Invalid JSON"**
   - The script will skip files with invalid JSON
   - Check the file format and ensure it's valid JSON

### Debug Mode

Use the `--debug` flag to get detailed information about:

- Which files are being processed
- What duplicates are being removed
- Any validation errors

### Backup Files

Backup files are created with `.backup` extension. If a backup already exists, the script will not overwrite it. To force a new backup, delete the existing backup file first.

## Integration

The script can be imported and used in other TypeScript modules:

```typescript
import { deduplicateFailedDownloads, processFile } from './deduplicate_failed_downloads';

// Use the deduplication function directly
const updatedData = deduplicateFailedDownloads(originalData);

// Process a file programmatically
await processFile('path/to/file.json', true);
```
