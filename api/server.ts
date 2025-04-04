import express, { Request, Response } from 'express';
import fs from 'fs';
import path from 'path';

const app = express();
const port = process.env.PORT || 1337;

app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Pipeline API is running' });
});

app.get('/sansad', (req: Request, res: Response): void => {
  try {
    const requestedPath = req.query.path?.toString() || '';
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

    const items = fs.readdirSync(fullPath, { withFileTypes: true });
    const contents = items.map((item) => ({
      name: item.name,
      type: item.isDirectory() ? 'directory' : 'file',
    }));

    res.json({
      path: requestedPath,
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
