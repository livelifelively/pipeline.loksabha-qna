#!/usr/bin/env ts-node

/**
 * Mermaid Diagram Management Tool
 *
 * TypeScript-based tool for managing Mermaid diagrams across the project.
 * Integrates with the existing package.json scripts and project structure.
 *
 * Features:
 * - Auto-discover all .mmd files
 * - Update diagrams.json catalog
 * - Generate documentation
 * - Validate diagram links and references
 * - Perform planned reorganizations
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { glob } from 'glob';

interface DiagramMetadata {
  generated_at: string;
  version: string;
  description: string;
  project: string;
  total_diagrams: number;
}

interface Category {
  name: string;
  description: string;
  base_path: string;
  icon: string;
}

interface Diagram {
  file: string;
  title: string;
  type: 'workflow' | 'module' | 'sequence' | 'component' | 'other';
  category: string;
  description: string;
  entry_point?: boolean;
  links_to?: string[];
  related_to?: string[];
  components?: string[];
  target_location?: string;
  last_modified: string;
  file_size?: number;
  discovered?: boolean;
}

interface Navigation {
  entry_points: string[];
  workflow_chains: string[][];
  component_hierarchy: Record<string, string[]>;
}

interface ReorganizationMove {
  from: string;
  to: string;
  reason: string;
}

interface DiagramCatalog {
  metadata: DiagramMetadata;
  categories: Record<string, Category>;
  diagrams: Record<string, Diagram>;
  navigation: Navigation;
  planned_reorganization: {
    enabled: boolean;
    moves: ReorganizationMove[];
  };
  scripts: Record<string, string>;
}

class DiagramManager {
  private projectRoot: string;
  private catalogPath: string;

  private diagramPatterns = {
    workflow: /\.workflow\.mmd$/,
    module: /\.module\.mmd$/,
    sequence: /\.sequence\.mmd$/,
    component: /\.component\.mmd$/,
    other: /\.mmd$/,
  };

  constructor(projectRoot: string = process.cwd()) {
    this.projectRoot = projectRoot;
    this.catalogPath = path.join(projectRoot, 'docs', 'diagrams.json');
  }

  /**
   * Auto-discover all .mmd files in the project
   */
  async discoverDiagrams(): Promise<Record<string, Diagram>> {
    const mmdFiles = await glob('**/*.mmd', {
      cwd: this.projectRoot,
      ignore: ['node_modules/**', '.venv/**', 'build/**', 'out/**'],
    });

    const discovered: Record<string, Diagram> = {};

    for (const filePath of mmdFiles) {
      const fullPath = path.join(this.projectRoot, filePath);
      const stats = await fs.stat(fullPath);

      // Determine type based on filename
      const diagramType = this.determineDiagramType(filePath);

      // Determine category based on path
      const category = this.determineCategory(filePath);

      // Extract metadata from file content
      const metadata = await this.extractMetadata(fullPath);

      // Generate unique ID
      const diagramId = this.generateId(path.basename(filePath, '.mmd'));

      discovered[diagramId] = {
        file: filePath,
        title: metadata.title || this.titleFromFilename(path.basename(filePath, '.mmd')),
        type: diagramType,
        category,
        description: metadata.description || `${diagramType} diagram`,
        components: metadata.components || [],
        links_to: metadata.links_to || [],
        last_modified: stats.mtime.toISOString(),
        file_size: stats.size,
        discovered: true,
      };
    }

    return discovered;
  }

  /**
   * Determine diagram type from filename pattern
   */
  private determineDiagramType(filePath: string): Diagram['type'] {
    for (const [type, pattern] of Object.entries(this.diagramPatterns)) {
      if (pattern.test(filePath)) {
        return type as Diagram['type'];
      }
    }
    return 'other';
  }

  /**
   * Determine category based on file path
   */
  private determineCategory(filePath: string): string {
    if (filePath.includes('cli/')) return 'cli_workflows';
    if (filePath.includes('documents/extractors')) return 'core_components';
    if (filePath.includes('parliament_questions')) return 'domain_logic';
    if (filePath.includes('workflows/')) return 'workflows';
    if (filePath.includes('api/')) return 'api';
    return 'other';
  }

  /**
   * Extract metadata from .mmd file content
   */
  private async extractMetadata(filePath: string): Promise<Partial<Diagram>> {
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const metadata: Partial<Diagram> = {};

      // Look for title in comments
      const titleMatch = content.match(/%% title:\s*(.+)/i);
      if (titleMatch) {
        metadata.title = titleMatch[1].trim();
      }

      // Look for description
      const descMatch = content.match(/%% description:\s*(.+)/i);
      if (descMatch) {
        metadata.description = descMatch[1].trim();
      }

      // Extract component references (class names, function names)
      // Look for text in brackets [ClassName] or quotes "ClassName"
      const bracketMatches = content.match(/\[([A-Z][a-zA-Z0-9_]+)\]/g);
      const quoteMatches = content.match(/"([A-Z][a-zA-Z0-9_]+)"/g);

      const components = new Set<string>();

      if (bracketMatches) {
        bracketMatches.forEach((match) => {
          const component = match.replace(/[\[\]]/g, '');
          components.add(component);
        });
      }

      if (quoteMatches) {
        quoteMatches.forEach((match) => {
          const component = match.replace(/[\"]/g, '');
          if (/^[A-Z][a-zA-Z0-9_]+$/.test(component)) {
            components.add(component);
          }
        });
      }

      metadata.components = Array.from(components);

      // Look for click references to other diagrams
      const clickMatches = content.match(/click\s+\w+\s+"([^"]+)"/g);
      if (clickMatches) {
        metadata.links_to = clickMatches
          .map((match) => match.match(/click\s+\w+\s+"([^"]+)"/)?.[1])
          .filter((link): link is string => link !== undefined && link.endsWith('.mmd'))
          .map((link) => path.basename(link, '.mmd'));
      }

      return metadata;
    } catch (error) {
      console.warn(`Warning: Could not parse ${filePath}:`, error);
      return {};
    }
  }

  /**
   * Generate consistent ID from filename
   */
  private generateId(filename: string): string {
    return filename
      .replace(/\.(workflow|module|sequence|component)/, '')
      .replace(/[^a-zA-Z0-9_]/g, '_')
      .toLowerCase();
  }

  /**
   * Generate human-readable title from filename
   */
  private titleFromFilename(filename: string): string {
    const cleanName = filename.replace(/\.(workflow|module|sequence|component)/, '').replace(/[_-]/g, ' ');

    return cleanName
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  /**
   * Load current catalog
   */
  async loadCatalog(): Promise<DiagramCatalog> {
    try {
      const content = await fs.readFile(this.catalogPath, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      console.warn(`Warning: Could not load ${this.catalogPath}, creating new catalog`);
      return this.createEmptyCatalog();
    }
  }

  /**
   * Create empty catalog structure
   */
  private createEmptyCatalog(): DiagramCatalog {
    return {
      metadata: {
        generated_at: new Date().toISOString(),
        version: '1.0.0',
        description: 'Auto-generated catalog of Mermaid diagrams',
        project: 'pipeline.loksabha-qna',
        total_diagrams: 0,
      },
      categories: {},
      diagrams: {},
      navigation: {
        entry_points: [],
        workflow_chains: [],
        component_hierarchy: {},
      },
      planned_reorganization: {
        enabled: false,
        moves: [],
      },
      scripts: {},
    };
  }

  /**
   * Update catalog with discovered diagrams
   */
  async updateCatalog(discovered?: Record<string, Diagram>): Promise<DiagramCatalog> {
    if (!discovered) {
      discovered = await this.discoverDiagrams();
    }

    const catalog = await this.loadCatalog();

    // Update metadata
    catalog.metadata.generated_at = new Date().toISOString();
    catalog.metadata.total_diagrams = Object.keys(discovered).length;

    // Merge discovered diagrams with existing ones
    for (const [diagramId, diagramInfo] of Object.entries(discovered)) {
      if (catalog.diagrams[diagramId]) {
        // Update existing entry, preserving manual metadata
        const existing = catalog.diagrams[diagramId];
        catalog.diagrams[diagramId] = {
          ...diagramInfo,
          description: existing.description || diagramInfo.description,
          links_to: existing.links_to || diagramInfo.links_to,
          target_location: existing.target_location,
        };
      } else {
        catalog.diagrams[diagramId] = diagramInfo;
      }
    }

    // Update navigation
    this.updateNavigation(catalog);

    return catalog;
  }

  /**
   * Update navigation information
   */
  private updateNavigation(catalog: DiagramCatalog): void {
    const entryPoints: string[] = [];
    const workflowChains: string[][] = [];

    for (const [diagramId, info] of Object.entries(catalog.diagrams)) {
      if (info.entry_point) {
        entryPoints.push(diagramId);
      }

      if (info.type === 'workflow' && diagramId.includes('menu')) {
        const chain = this.buildWorkflowChain(catalog, diagramId);
        if (chain.length > 1) {
          workflowChains.push(chain);
        }
      }
    }

    catalog.navigation.entry_points = entryPoints;
    catalog.navigation.workflow_chains = workflowChains;
  }

  /**
   * Build workflow chain starting from given diagram
   */
  private buildWorkflowChain(catalog: DiagramCatalog, startId: string): string[] {
    const chain = [startId];
    const visited = new Set([startId]);
    let current = startId;

    while (true) {
      const links = catalog.diagrams[current]?.links_to || [];
      const nextWorkflow = links.find((link) => !visited.has(link) && catalog.diagrams[link]?.type === 'workflow');

      if (nextWorkflow) {
        chain.push(nextWorkflow);
        visited.add(nextWorkflow);
        current = nextWorkflow;
      } else {
        break;
      }
    }

    return chain;
  }

  /**
   * Save catalog to file
   */
  async saveCatalog(catalog: DiagramCatalog): Promise<void> {
    // Ensure docs directory exists
    await fs.mkdir(path.dirname(this.catalogPath), { recursive: true });

    await fs.writeFile(this.catalogPath, JSON.stringify(catalog, null, 2));

    console.log(`✅ Updated ${this.catalogPath}`);
  }

  /**
   * Generate README content from catalog
   */
  generateReadme(catalog: DiagramCatalog): string {
    const lines = [
      '# Loksabha QNA Pipeline - Documentation',
      '',
      '*This documentation is auto-generated from `docs/diagrams.json`*',
      '',
      `**Last updated:** ${catalog.metadata.generated_at}`,
      `**Total diagrams:** ${catalog.metadata.total_diagrams}`,
      '',
      '## 🎯 Quick Navigation',
    ];

    // Group by category
    const categories: Record<string, Array<[string, Diagram]>> = {};
    for (const [diagramId, info] of Object.entries(catalog.diagrams)) {
      if (!categories[info.category]) {
        categories[info.category] = [];
      }
      categories[info.category].push([diagramId, info]);
    }

    for (const [categoryKey, diagrams] of Object.entries(categories)) {
      const categoryInfo = catalog.categories[categoryKey];
      const icon = categoryInfo?.icon || '📄';
      const name = categoryInfo?.name || categoryKey.replace(/_/g, ' ');

      lines.push('', `### ${icon} ${name}`, '');

      diagrams
        .sort(([, a], [, b]) => a.title.localeCompare(b.title))
        .forEach(([, info]) => {
          lines.push(`- [**${info.title}**](${info.file}) - ${info.description}`);
        });
    }

    // Add workflow chains
    if (catalog.navigation.workflow_chains.length > 0) {
      lines.push('', '## 🔄 Workflow Chains', '');

      catalog.navigation.workflow_chains.forEach((chain, i) => {
        const chainTitles = chain.map((id) => catalog.diagrams[id]?.title || id);
        lines.push(`${i + 1}. ${chainTitles.join(' → ')}`);
      });
    }

    // Add management commands
    lines.push(
      '',
      '## 🛠️ Management Commands',
      '',
      '```bash',
      '# Discover all diagrams',
      'npm run docs:discover',
      '',
      '# Update catalog',
      'npm run docs:update',
      '',
      '# Generate this README',
      'npm run docs:generate',
      '',
      '# Validate diagram links',
      'npm run docs:validate',
      '',
      '# Reorganize files (dry run)',
      'npm run docs:reorganize -- --dry-run',
      '```'
    );

    return lines.join('\n');
  }

  /**
   * Validate diagram links and references
   */
  async validateLinks(catalog: DiagramCatalog): Promise<string[]> {
    const errors: string[] = [];

    for (const [diagramId, info] of Object.entries(catalog.diagrams)) {
      const filePath = path.join(this.projectRoot, info.file);

      // Check if file exists
      try {
        await fs.access(filePath);
      } catch {
        errors.push(`❌ ${diagramId}: File not found: ${info.file}`);
        continue;
      }

      // Check if linked diagrams exist
      for (const link of info.links_to || []) {
        if (!catalog.diagrams[link]) {
          errors.push(`❌ ${diagramId}: Links to non-existent diagram: ${link}`);
        }
      }
    }

    return errors;
  }

  /**
   * Execute planned reorganization moves
   */
  async reorganizeFiles(catalog: DiagramCatalog, dryRun = true): Promise<string[]> {
    const results: string[] = [];
    const moves = catalog.planned_reorganization?.moves || [];

    for (const move of moves) {
      const fromPath = path.join(this.projectRoot, move.from);
      const toPath = path.join(this.projectRoot, move.to);

      try {
        await fs.access(fromPath);
      } catch {
        results.push(`❌ Source file not found: ${move.from}`);
        continue;
      }

      if (dryRun) {
        results.push(`🔄 Would move: ${move.from} → ${move.to}`);
      } else {
        try {
          // Create target directory if needed
          await fs.mkdir(path.dirname(toPath), { recursive: true });

          // Move file
          await fs.rename(fromPath, toPath);
          results.push(`✅ Moved: ${move.from} → ${move.to}`);

          // Update catalog
          for (const [diagramId, info] of Object.entries(catalog.diagrams)) {
            if (info.file === move.from) {
              info.file = move.to;
              break;
            }
          }
        } catch (error) {
          results.push(`❌ Failed to move ${move.from}: ${error}`);
        }
      }
    }

    return results;
  }
}

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  const manager = new DiagramManager();

  switch (command) {
    case 'discover':
      const discovered = await manager.discoverDiagrams();
      console.log(`📊 Discovered ${Object.keys(discovered).length} diagrams:`);
      for (const [id, info] of Object.entries(discovered)) {
        console.log(`  - ${id}: ${info.file} (${info.type})`);
      }
      break;

    case 'update':
      const catalog = await manager.updateCatalog();
      await manager.saveCatalog(catalog);
      break;

    case 'generate-readme':
      const currentCatalog = await manager.loadCatalog();
      const readme = manager.generateReadme(currentCatalog);
      const readmePath = path.join(process.cwd(), 'docs', 'README.md');
      await fs.mkdir(path.dirname(readmePath), { recursive: true });
      await fs.writeFile(readmePath, readme);
      console.log(`📝 Generated README: ${readmePath}`);
      break;

    case 'validate':
      const catalogToValidate = await manager.loadCatalog();
      const errors = await manager.validateLinks(catalogToValidate);
      if (errors.length > 0) {
        console.log('❌ Validation errors:');
        errors.forEach((error) => console.log(`  ${error}`));
        process.exit(1);
      } else {
        console.log('✅ All diagram links are valid');
      }
      break;

    case 'reorganize':
      const dryRun = args.includes('--dry-run');
      const catalogToReorganize = await manager.loadCatalog();
      const results = await manager.reorganizeFiles(catalogToReorganize, dryRun);
      results.forEach((result) => console.log(result));

      if (!dryRun) {
        await manager.saveCatalog(catalogToReorganize);
      }
      break;

    default:
      console.log('Usage: diagram-manager.ts <command>');
      console.log('Commands:');
      console.log('  discover        - Discover all .mmd files');
      console.log('  update          - Update diagrams.json catalog');
      console.log('  generate-readme - Generate README from catalog');
      console.log('  validate        - Validate diagram links');
      console.log('  reorganize      - Execute planned reorganization');
      console.log('');
      console.log('Options:');
      console.log('  --dry-run       - Show what would be done (for reorganize)');
      break;
  }
}

if (require.main === module) {
  main().catch(console.error);
}

export { DiagramManager };
