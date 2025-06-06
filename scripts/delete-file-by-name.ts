import * as fs from 'fs';
import * as path from 'path';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

function deleteFilesByName(directory: string, targetFileName: string): void {
  // Read all items in the current directory
  const items = fs.readdirSync(directory);

  for (const item of items) {
    const fullPath = path.join(directory, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      // Recursively search in subdirectories
      deleteFilesByName(fullPath, targetFileName);
    } else if (item === targetFileName) {
      // Delete file if name matches
      fs.unlinkSync(fullPath);
      console.log(`Deleted file: ${fullPath}`);
    }
  }
}

// Parse command line arguments using yargs
const argv = yargs(hideBin(process.argv))
  .options({
    dir: {
      alias: 'd',
      description: 'Directory path to start the search from',
      type: 'string',
      demandOption: true,
    },
    file: {
      alias: 'f',
      description: 'Name of the file to delete',
      type: 'string',
      demandOption: true,
    },
  })
  .example('$0 -d ./my-folder -f example.txt', 'Delete all files named example.txt in my-folder')
  .example('$0 --dir ./data --file test.json', 'Delete all files named test.json in data folder')
  .help()
  .alias('help', 'h')
  .version(false)
  .strict()
  .parseSync();

try {
  const startDir = argv.dir;
  const targetFileName = argv.file;

  if (!fs.existsSync(startDir)) {
    throw new Error(`Directory does not exist: ${startDir}`);
  }

  console.log(`Starting deletion of files named '${targetFileName}' from directory: ${startDir}`);
  console.log('Warning: This operation cannot be undone!');

  deleteFilesByName(path.resolve(startDir), targetFileName);
  console.log('Deletion operation completed successfully');
} catch (error) {
  console.error('Error during deletion operation:', error);
  process.exit(1);
}
