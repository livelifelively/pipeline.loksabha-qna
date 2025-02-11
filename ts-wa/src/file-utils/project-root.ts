const path = require('path');
const fs = require('fs');

export function findProjectRoot() {
  let currentDir = __dirname;
  while (!fs.existsSync(path.join(currentDir, 'package.json'))) {
    const parentDir = path.resolve(currentDir, '..');
    if (parentDir === currentDir) {
      throw new Error('Could not find project root');
    }
    currentDir = parentDir;
  }
  return currentDir;
}

export function kebabCaseNames(name: string) {
  let smallerName = name.trim().split(',').join('').split('and').join('').split('&').join('');
  let kebabCaseString = smallerName.split(' ').join('-').toLowerCase();
  return kebabCaseString;
}

export const filenameGenerator = (url: string, index: number) => {
  const parsedUrl = new URL(url);
  const basename = path.basename(parsedUrl.pathname);
  return basename.endsWith('.pdf') ? basename : `downloaded_file_${index}.pdf`;
};

// const projectRoot = findProjectRoot();
// console.log("Project Root:", projectRoot);
