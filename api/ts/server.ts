import express, { Request, Response } from 'express';
import fs from 'fs';
import path from 'path';
import cors from 'cors';

const BASE_PATH = path.join(__dirname, '../../../../data/loksabha-qna');

const app = express();
const port = process.env.PORT || 1337;

// Enable CORS for all routes with default settings
app.use(cors());

app.get('/path', (req: Request, res: Response): void => {
  try {
    const requestedPath = req.query.p?.toString() || '';
    const recursive = req.query.r === 'true';
    const basePath = BASE_PATH;
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
    const basePath = BASE_PATH;
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

    // Only handle text files
    const ext = path.extname(fullPath).toLowerCase();
    if (ext === '.pdf') {
      res.status(400).json({ error: 'Use /binary endpoint for PDF files' });
      return;
    }

    const fileContent = fs.readFileSync(fullPath, 'utf8');
    res.json({ content: fileContent });
  } catch (error: any) {
    console.error('Error accessing file:', error);
    res.status(500).json({ error: 'Failed to read file' });
  }
});

app.get('/binary', (req: Request, res: Response): void => {
  try {
    const requestedPath = req.query.p?.toString() || '';
    const basePath = BASE_PATH;
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

    const ext = path.extname(fullPath).toLowerCase();
    if (ext !== '.pdf') {
      res.status(400).json({ error: 'Use /file endpoint for text files' });
      return;
    }

    const fileStream = fs.createReadStream(fullPath);
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `inline; filename="${path.basename(fullPath)}"`);
    fileStream.pipe(res);
  } catch (error: any) {
    console.error('Error accessing binary file:', error);
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

    const basePath = BASE_PATH;
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

// ─── Annotation endpoints ─────────────────────────────────────────────────

const ANNOTATION_FILENAME = 'annotations.json';

// GET /annotations/documents?ministry=health-and-family-welfare
// List documents for a ministry with their annotation status
app.get('/annotations/documents', (req: Request, res: Response): void => {
  try {
    const ministry = req.query.ministry?.toString() || 'health-and-family-welfare';
    const loksabha = req.query.loksabha?.toString() || '18';
    const session = req.query.session?.toString() || 'iv';

    const ministryPath = path.join(BASE_PATH, loksabha, session, 'ministries', ministry);

    if (!path.resolve(ministryPath).startsWith(path.resolve(BASE_PATH))) {
      res.status(400).json({ error: 'Invalid path' });
      return;
    }

    if (!fs.existsSync(ministryPath) || !fs.statSync(ministryPath).isDirectory()) {
      res.status(404).json({ error: 'Ministry directory not found' });
      return;
    }

    const entries = fs.readdirSync(ministryPath, { withFileTypes: true });
    const documents = entries
      .filter((e) => e.isDirectory())
      .map((e) => {
        const docDir = path.join(ministryPath, e.name);
        const progressPath = path.join(docDir, 'question.progress.json');
        const annotationPath = path.join(docDir, ANNOTATION_FILENAME);

        let progress: any = null;
        let hasAnnotations = false;
        let subject = '';
        let questionNumber = '';
        let questionType = '';
        let date = '';

        if (fs.existsSync(progressPath)) {
          try {
            progress = JSON.parse(fs.readFileSync(progressPath, 'utf8'));
            // Extract metadata from INITIALIZED state
            const initState = progress.states?.find((s: any) => s.state === 'INITIALIZED');
            if (initState?.data) {
              subject = initState.data.subjects || '';
              questionNumber = String(initState.data.question_number || '');
              questionType = initState.data.type || '';
              date = initState.data.date || '';
            }
          } catch {}
        }

        if (fs.existsSync(annotationPath)) {
          hasAnnotations = true;
        }

        return {
          id: e.name,
          path: `${loksabha}/${session}/ministries/${ministry}/${e.name}`,
          subject,
          question_number: questionNumber,
          question_type: questionType,
          date,
          current_state: progress?.current_state || 'UNKNOWN',
          has_annotations: hasAnnotations,
        };
      })
      .sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true }));

    res.json({ ministry, documents });
  } catch (error: any) {
    console.error('Error listing documents:', error);
    res.status(500).json({ error: 'Failed to list documents' });
  }
});

// GET /annotations/document?p=18/iv/ministries/health-and-family-welfare/s-64
// Load a document's text and existing annotations
app.get('/annotations/document', (req: Request, res: Response): void => {
  try {
    const requestedPath = req.query.p?.toString() || '';
    const docDir = path.join(BASE_PATH, requestedPath);

    if (!path.resolve(docDir).startsWith(path.resolve(BASE_PATH))) {
      res.status(400).json({ error: 'Invalid path' });
      return;
    }

    if (!fs.existsSync(docDir) || !fs.statSync(docDir).isDirectory()) {
      res.status(404).json({ error: 'Document directory not found' });
      return;
    }

    // Read progress file for text and metadata
    const progressPath = path.join(docDir, 'question.progress.json');
    let text = '';
    let metadata: any = {};

    if (fs.existsSync(progressPath)) {
      const progress = JSON.parse(fs.readFileSync(progressPath, 'utf8'));

      // Get metadata from INITIALIZED state
      const initState = progress.states?.find((s: any) => s.state === 'INITIALIZED');
      if (initState?.data) {
        metadata = initState.data;
      }

      // Get text from LOCAL_EXTRACTION or LLM_EXTRACTION state
      const extractionState =
        progress.states?.find((s: any) => s.state === 'LLM_EXTRACTION' && s.status === 'SUCCESS') ||
        progress.states?.find((s: any) => s.state === 'LOCAL_EXTRACTION' && s.status === 'SUCCESS');

      if (extractionState?.data?.pages) {
        // Combine page texts
        const pageNums = Object.keys(extractionState.data.pages).sort(
          (a, b) => parseInt(a) - parseInt(b)
        );
        text = pageNums
          .map((num) => extractionState.data.pages[num].text || '')
          .join('\n\n')
          .trim();
      }
    }

    // Read existing annotations if any
    const annotationPath = path.join(docDir, ANNOTATION_FILENAME);
    let annotations: any = null;

    if (fs.existsSync(annotationPath)) {
      try {
        annotations = JSON.parse(fs.readFileSync(annotationPath, 'utf8'));
      } catch {}
    }

    res.json({
      path: requestedPath,
      text,
      metadata,
      annotations,
    });
  } catch (error: any) {
    console.error('Error loading document:', error);
    res.status(500).json({ error: 'Failed to load document' });
  }
});

// PUT /annotations/document?p=18/iv/ministries/health-and-family-welfare/s-64
// Save annotations for a document
app.put('/annotations/document', express.json({ limit: '10mb' }), (req: Request, res: Response): void => {
  try {
    const requestedPath = req.query.p?.toString() || '';
    const docDir = path.join(BASE_PATH, requestedPath);

    if (!path.resolve(docDir).startsWith(path.resolve(BASE_PATH))) {
      res.status(400).json({ error: 'Invalid path' });
      return;
    }

    if (!fs.existsSync(docDir) || !fs.statSync(docDir).isDirectory()) {
      res.status(404).json({ error: 'Document directory not found' });
      return;
    }

    const annotations = req.body;

    if (!annotations || typeof annotations !== 'object') {
      res.status(400).json({ error: 'Invalid annotation data' });
      return;
    }

    const annotationPath = path.join(docDir, ANNOTATION_FILENAME);
    fs.writeFileSync(annotationPath, JSON.stringify(annotations, null, 2), 'utf8');

    res.json({ success: true, path: requestedPath });
  } catch (error: any) {
    console.error('Error saving annotations:', error);
    res.status(500).json({ error: 'Failed to save annotations' });
  }
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
