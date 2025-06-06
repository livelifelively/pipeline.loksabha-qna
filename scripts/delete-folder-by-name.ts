import * as fs from 'fs';
import * as path from 'path';

function deleteFolderRecursive(folderPath: string): void {
  if (fs.existsSync(folderPath)) {
    fs.readdirSync(folderPath).forEach((file) => {
      const curPath = path.join(folderPath, file);
      if (fs.lstatSync(curPath).isDirectory()) {
        // Recurse if directory
        deleteFolderRecursive(curPath);
      } else {
        // Delete file
        fs.unlinkSync(curPath);
      }
    });
    // Delete the empty directory
    fs.rmdirSync(folderPath);
  }
}

function findAndDeletePagesFolders(directory: string): void {
  // Read all items in the current directory
  const items = fs.readdirSync(directory);

  for (const item of items) {
    const fullPath = path.join(directory, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      if (item === 'pages') {
        console.log(`Deleting pages folder: ${fullPath}`);
        deleteFolderRecursive(fullPath);
      } else {
        // Recursively search in other directories
        findAndDeletePagesFolders(fullPath);
      }
    }
  }
}

// Get the directory to start from (default to current directory if no argument provided)
const startDir = process.argv[2] || '.';

try {
  console.log(`Starting deletion of 'pages' folders from directory: ${startDir}`);
  findAndDeletePagesFolders(path.resolve(startDir));
  console.log('Deletion operation completed successfully');
} catch (error) {
  console.error('Error during deletion operation:', error);
  process.exit(1);
}
