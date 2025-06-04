import { spawn } from 'child_process';
import { join } from 'path';
import { readFileSync, writeFileSync } from 'fs';

interface ParsedData {
  file_path: string;
  classes: Array<{
    name: string;
    docstring: string | null;
    line_range: { start: number; end: number };
  }>;
  functions: Array<{
    name: string;
    docstring: string | null;
    line_range: { start: number; end: number };
  }>;
}

interface ModuleNode {
  id: string;
  name: string;
  description: string;
  path: string;
  module_id?: string;
}

interface ClassNode extends ModuleNode {
  module_id: string;
  functions: string[];
  inherits_from?: string;
}

interface FunctionNode extends ModuleNode {
  module_id: string;
  class_id?: string;
  instantiates?: string[];
}

interface GraphNodes {
  modules: Record<string, ModuleNode>;
  classes: Record<string, ClassNode>;
  functions: Record<string, FunctionNode>;
}

interface Graph {
  nodes: GraphNodes;
}

interface UpdateGraphOptions {
  file?: string; // Specific file to analyze
  all?: boolean; // Analyze all files
}

async function updateGraph(options: UpdateGraphOptions = {}) {
  try {
    // Load graph from index.ts
    const indexTsPath = join(__dirname, '../index.ts');
    const indexTsContent = readFileSync(indexTsPath, 'utf8');
    const graphMatch = indexTsContent.match(/export const moduleGraph = ({[\s\S]*?});/);
    if (!graphMatch) {
      throw new Error('Could not find moduleGraph in index.ts');
    }
    const graph: Graph = JSON.parse(graphMatch[1]);

    // Get parsed data from Python parser
    const scriptPath = join(__dirname, '../parser/python_parser.py');
    const pythonArgs = [scriptPath];
    if (options.file) {
      pythonArgs.push('--file', options.file);
    } else if (options.all) {
      pythonArgs.push('--all');
    } else {
      pythonArgs.push('--file', 'cli/py/extract_pdf/menu.py');
    }

    const pythonProcess = spawn('python', pythonArgs, {
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    process.stdout.write(
      'Executing Python command: python docs/parser/python_parser.py --file ' + pythonArgs[pythonArgs.length - 1] + '\n'
    );

    let parsedData: ParsedData | undefined;
    let pythonOutput = '';

    // Collect Python script output
    pythonProcess.stdout.on('data', (data) => {
      process.stdout.write('Python stdout: ' + data.toString() + '\n');
      pythonOutput += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      process.stdout.write('Python stderr: ' + data.toString() + '\n');
    });

    // Wait for Python script to complete and parse output
    await new Promise((resolve, reject) => {
      pythonProcess.on('close', (code) => {
        process.stdout.write('Python process exited with code: ' + code + '\n');
        if (code === 0) {
          try {
            process.stdout.write('Python output: ' + pythonOutput + '\n');
            parsedData = JSON.parse(pythonOutput);
            resolve(true);
          } catch (error) {
            reject(new Error(`Failed to parse Python output: ${error}`));
          }
        } else {
          reject(new Error(`Python script exited with code ${code}`));
        }
      });
    });

    if (!parsedData) {
      throw new Error('No data parsed from Python script');
    }

    process.stdout.write('Parsed data: ' + JSON.stringify(parsedData, null, 2) + '\n');

    // Find corresponding module in graph
    const moduleId = Object.entries(graph.nodes.modules).find(
      ([_, mod]) => mod.path === (parsedData as ParsedData).file_path
    )?.[0];

    process.stdout.write('Found module ID: ' + moduleId + '\n');
    process.stdout.write(
      'Module paths in graph: ' + JSON.stringify(Object.values(graph.nodes.modules).map((m) => m.path)) + '\n'
    );

    if (!moduleId) {
      process.stdout.write(`Warning: No module found for ${parsedData.file_path}\n`);
      return;
    }

    // Update class descriptions
    for (const cls of parsedData.classes) {
      const classId = Object.entries(graph.nodes.classes).find(
        ([_, classNode]) => classNode.module_id === moduleId && classNode.name === cls.name
      )?.[0];

      process.stdout.write(`Class match - Name: ${cls.name}, ID: ${classId}, Docstring: ${cls.docstring}\n`);
      if (classId) {
        process.stdout.write('Current description: ' + graph.nodes.classes[classId].description + '\n');
      }

      if (classId && cls.docstring) {
        graph.nodes.classes[classId].description = cls.docstring;
        process.stdout.write('Updated description: ' + graph.nodes.classes[classId].description + '\n');
      }
    }

    // Update function descriptions
    for (const func of parsedData.functions) {
      const funcId = Object.entries(graph.nodes.functions).find(
        ([_, funcNode]) => funcNode.module_id === moduleId && funcNode.name === func.name
      )?.[0];

      process.stdout.write(`Function match - Name: ${func.name}, ID: ${funcId}, Docstring: ${func.docstring}\n`);
      if (funcId) {
        process.stdout.write('Current description: ' + graph.nodes.functions[funcId].description + '\n');
      }

      if (funcId && func.docstring) {
        graph.nodes.functions[funcId].description = func.docstring;
        process.stdout.write('Updated description: ' + graph.nodes.functions[funcId].description + '\n');
      }
    }

    // Write updated graph back to index.ts
    const updatedIndexTsContent = indexTsContent.replace(
      /export const moduleGraph = {[\s\S]*?};/,
      `export const moduleGraph = ${JSON.stringify(graph, null, 2)};`
    );
    writeFileSync(indexTsPath, updatedIndexTsContent);

    process.stdout.write('Graph updated successfully\n');
  } catch (error) {
    console.error('Error updating graph:', error);
    process.exit(1);
  }
}

// Export the command
export const command = {
  name: 'update-graph',
  description: 'Update graph with docstrings from Python files',
  options: [
    {
      name: '--file',
      description: 'Specific Python file to analyze',
      type: 'string',
    },
    {
      name: '--all',
      description: 'Analyze all Python files',
      type: 'boolean',
    },
  ],
  run: updateGraph,
};
