import express, { Request, Response } from 'express';
import fs from 'fs';
import path from 'path';

const app = express();
const port = process.env.PORT || 1337;

app.get('/sansad', (req: Request, res: Response): void => {
  try {
    const requestedPath = req.query.p?.toString() || '';
    const recursive = req.query.r === 'true';
    const basePath = path.join(__dirname, '../sansad');
    const fullPath = path.join(basePath, requestedPath);

    // Security check: Use path.resolve for better normalization and comparison
    if (!path.resolve(fullPath).startsWith(path.resolve(basePath))) {
      res.status(400).json({ error: 'Invalid path' });
      return;
    }

    // Check if directory exists
    if (!fs.existsSync(fullPath) || !fs.statSync(fullPath).isDirectory()) {
      res.status(404).json({ error: 'Directory not found' });
      return;
    }

    // Function to get directory contents
    const getDirectoryContents = (dirPath: string, shouldRecurse: boolean): any[] => {
      const items = fs.readdirSync(dirPath, { withFileTypes: true });
      return items.map((item) => {
        const itemPath = path.join(dirPath, item.name);
        const relativePath = path.relative(fullPath, itemPath);

        if (item.isDirectory()) {
          return {
            name: item.name,
            type: 'directory',
            path: relativePath,
            contents: shouldRecurse ? getDirectoryContents(itemPath, true) : [],
          };
        }

        return {
          name: item.name,
          type: 'file',
          path: relativePath,
        };
      });
    };

    const contents = getDirectoryContents(fullPath, recursive);

    res.json({
      path: requestedPath,
      recursive,
      contents,
    });
  } catch (error: any) {
    console.error('Error accessing directory:', error);
    if (error.code === 'ENOENT') {
      res.status(404).json({ error: 'Directory not found' });
    } else if (error.code === 'ENOTDIR') {
      res.status(400).json({ error: 'Path is not a directory' });
    } else {
      res.status(500).json({ error: 'Failed to read directory' });
    }
  }
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
