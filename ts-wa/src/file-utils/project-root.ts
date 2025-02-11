const path = require("path");
const fs = require("fs");

export function findProjectRoot() {
  let currentDir = __dirname;
  while (!fs.existsSync(path.join(currentDir, "package.json"))) {
    const parentDir = path.resolve(currentDir, "..");
    if (parentDir === currentDir) {
      throw new Error("Could not find project root");
    }
    currentDir = parentDir;
  }
  return currentDir;
}

// const projectRoot = findProjectRoot();
// console.log("Project Root:", projectRoot);
