import * as fs from 'fs';
import * as path from 'path';

interface QuestionProgressState {
  status: string;
  data: {
    timestamp?: string;
    [key: string]: any;
  };
  timestamp?: string;
  meta: any;
  errors: any[];
}

interface QuestionProgress {
  current_state: string;
  states: {
    [stateName: string]: QuestionProgressState;
  };
  created_at: string;
  updated_at: string;
}

function findQuestionProgressFiles(dir: string): string[] {
  const progressFiles: string[] = [];

  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        // Recursively search subdirectories
        progressFiles.push(...findQuestionProgressFiles(fullPath));
      } else if (entry.isFile() && entry.name === 'question.progress.json') {
        // Found a question.progress.json file
        progressFiles.push(fullPath);
      }
    }
  } catch (error) {
    console.warn(`Warning: Could not read directory ${dir}:`, error);
  }

  return progressFiles;
}

function moveTimestamps(inputDirectory: string): void {
  console.log(`Processing directory: ${inputDirectory}`);

  // Check if input directory exists
  if (!fs.existsSync(inputDirectory)) {
    console.error(`Directory does not exist: ${inputDirectory}`);
    process.exit(1);
  }

  // Find all question.progress.json files recursively
  console.log('Searching for question.progress.json files recursively...');
  const progressFiles = findQuestionProgressFiles(inputDirectory);

  console.log(`Found ${progressFiles.length} question.progress.json files`);

  let processedFiles = 0;
  let modifiedFiles = 0;

  // Process each question.progress.json file
  for (const progressFilePath of progressFiles) {
    try {
      // Read and parse the JSON file
      const fileContent = fs.readFileSync(progressFilePath, 'utf-8');
      const progressData: QuestionProgress = JSON.parse(fileContent);

      processedFiles++;
      let fileModified = false;

      // Iterate through all states
      if (progressData.states) {
        for (const [stateName, state] of Object.entries(progressData.states)) {
          // Check if data.timestamp exists
          if (state.data && state.data.timestamp) {
            console.log(`Moving timestamp in ${progressFilePath} for state: ${stateName}`);

            // Move timestamp from data to be a peer of data
            state.timestamp = state.data.timestamp;
            delete state.data.timestamp;

            fileModified = true;
          }
        }
      }

      // Write back to file if modified
      if (fileModified) {
        const updatedContent = JSON.stringify(progressData, null, 2);
        fs.writeFileSync(progressFilePath, updatedContent, 'utf-8');
        modifiedFiles++;
        console.log(`✓ Updated: ${progressFilePath}`);
      } else {
        console.log(`- No changes needed: ${progressFilePath}`);
      }
    } catch (error) {
      console.error(`Error processing ${progressFilePath}:`, error);
    }
  }

  console.log(`\nSummary:`);
  console.log(`- Processed ${processedFiles} files`);
  console.log(`- Modified ${modifiedFiles} files`);
}

// Main execution
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length !== 1) {
    console.error('Usage: ts-node scripts/move-timestamps.ts <directory>');
    process.exit(1);
  }

  const inputDirectory = args[0];
  moveTimestamps(inputDirectory);
}

export { moveTimestamps };

// npm run move-timestamps /Users/dollyparmar/dev/kartvya/smgr/data-pipelines/repos/data/loksabha-qna/17/iii
