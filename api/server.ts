import express, { Request, Response } from 'express';
import fs from 'fs';
import path from 'path';
import cors from 'cors';

const app = express();
const port = process.env.PORT || 1337;

// Enable CORS for all routes with default settings
app.use(cors());

app.get('/path', (req: Request, res: Response): void => {
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

app.get('/file', (req: Request, res: Response): void => {
  try {
    const requestedPath = req.query.p?.toString() || '';
    const basePath = path.join(__dirname, '../sansad');
    const fullPath = path.join(basePath, requestedPath);

    // Security check: Use path.resolve for better normalization and comparison
    if (!path.resolve(fullPath).startsWith(path.resolve(basePath))) {
      res.status(400).json({ error: 'Invalid path' });
      return;
    }

    if (!fs.existsSync(fullPath) || !fs.statSync(fullPath).isFile()) {
      res.status(404).json({ error: 'File not found' });
      return;
    }

    const fileContent = fs.readFileSync(fullPath, 'utf8');
    res.json({ content: fileContent });
  } catch (error: any) {
    console.error('Error accessing file:', error);
    res.status(500).json({ error: 'Failed to read file' });
  }
});

app.post('/files', express.json(), (req: Request, res: Response): void => {
  try {
    const filePaths = req.body.paths || [];

    if (!Array.isArray(filePaths)) {
      res.status(400).json({ error: 'Invalid request format. Expected "paths" array in request body' });
      return;
    }

    const basePath = path.join(__dirname, '../sansad');
    const results: Record<string, { content: string } | { error: string }> = {};

    for (const requestedPath of filePaths) {
      if (typeof requestedPath !== 'string') {
        results[String(requestedPath)] = { error: 'Invalid path format' };
        continue;
      }

      const fullPath = path.join(basePath, requestedPath);

      // Security check: Use path.resolve for better normalization and comparison
      if (!path.resolve(fullPath).startsWith(path.resolve(basePath))) {
        results[requestedPath] = { error: 'Invalid path' };
        continue;
      }

      try {
        if (!fs.existsSync(fullPath) || !fs.statSync(fullPath).isFile()) {
          results[requestedPath] = { error: 'File not found' };
          continue;
        }

        const fileContent = fs.readFileSync(fullPath, 'utf8');
        results[requestedPath] = { content: fileContent };
      } catch (readError) {
        console.error(`Error reading file ${requestedPath}:`, readError);
        results[requestedPath] = { error: 'Failed to read file' };
      }
    }

    res.json({ files: results });
  } catch (error: any) {
    console.error('Error processing multiple files request:', error);
    res.status(500).json({ error: 'Failed to process request' });
  }
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
