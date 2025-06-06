import * as fs from 'fs';
import * as path from 'path';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

function renameProgressFiles(directory: string, oldName: string, newName: string): void {
  // Read all items in the current directory
  const items = fs.readdirSync(directory);

  for (const item of items) {
    const fullPath = path.join(directory, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      // Recursively process subdirectories
      renameProgressFiles(fullPath, oldName, newName);
    } else if (item === oldName) {
      // Rename file
      const newPath = path.join(directory, newName);
      fs.renameSync(fullPath, newPath);
      console.log(`Renamed: ${fullPath} -> ${newPath}`);
    }
  }
}

const argv = yargs(hideBin(process.argv))
  .options({
    dir: {
      alias: 'd',
      description: 'Directory path to start the search from',
      type: 'string',
      default: '.',
    },
    old: {
      alias: 'o',
      description: 'Original filename to rename',
      type: 'string',
      default: 'progress.json',
    },
    new: {
      alias: 'n',
      description: 'New filename',
      type: 'string',
      default: 'question.progress.json',
    },
  })
  .example('$0 -d ./data', 'Rename all progress.json to question.progress.json in data folder')
  .example('$0 -d ./data -o old.json -n new.json', 'Rename all old.json to new.json in data folder')
  .help()
  .alias('help', 'h')
  .version(false)
  .strict()
  .parseSync();

try {
  const { dir: startDir, old: oldName, new: newName } = argv;
  console.log(`Starting rename operation from directory: ${startDir}`);
  console.log(`Renaming ${oldName} to ${newName}`);
  renameProgressFiles(path.resolve(startDir), oldName, newName);
  console.log('Rename operation completed successfully');
} catch (error) {
  console.error('Error during rename operation:', error);
  process.exit(1);
}
