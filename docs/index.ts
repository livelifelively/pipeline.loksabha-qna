/**
 * Enhanced Module Graph for AI Context - Minimal Prototype
 */

import type { EnhancedModuleGraph } from './types';

export const moduleGraph: EnhancedModuleGraph = {
  metadata: {
    system_name: 'Loksabha Data Pipelines',
    description: 'Knowledge graph building system for the Lok Sabha Question and Answer documents',
    version: '1.0.0',
  },

  nodes: {
    applications: {
      APP001: {
        id: 'APP001',
        name: 'Document Processing System',
        description: 'System for processing parliamentary documents',
        domain: 'Document Processing',
        interfaces: ['INT001'],
        modules: ['MOD001', 'MOD002'],
      },
    },

    interfaces: {
      INT001: {
        id: 'INT001',
        name: 'Document Processing CLI',
        description: 'Command-line interface for processing parliamentary documents',
        interface_type: 'cli',
        entry_module: 'MOD001',
        entry_function: 'FUN003',
        execution: {
          command: 'CMD001',
          working_directory: '/',
          description: 'Run the CLI interface (activates venv and runs python -m cli.py.main)',
        },
        application: 'APP001',
        commands: ['CMD001'],
        used_by: ['ACT001'],
      },
    },

    actors: {
      ACT001: {
        id: 'ACT001',
        name: 'Human User',
        description: 'Human operator',
        category: 'human',
        uses_interfaces: ['INT001'],
      },
      ACT002: {
        id: 'ACT002',
        name: 'System',
        description: 'Automated components',
        category: 'system',
      },
      ACT003: {
        id: 'ACT003',
        name: 'AI',
        description: 'AI processing',
        category: 'ai',
      },
    },

    commands: {
      CMD001: {
        id: 'CMD001',
        name: 'Start CLI',
        description: 'Launch the main CLI interface for document processing',
        command: 'npm run start:cli',
        working_directory: '/',
        executable_by: ['ACT001'],
      },
    },

    modules: {
      MOD001: {
        id: 'MOD001',
        name: 'main.py',
        description: 'Main CLI entry point',
        path: 'cli/py/main.py',
        application: 'APP001',
        entry_for_interfaces: ['INT001'],
        imports: ['MOD002'],
        functions: ['FUN003', 'FUN004'],
        classes: [],
      },
      MOD002: {
        id: 'MOD002',
        name: 'menu.py',
        description: 'PDF extraction menu interface',
        path: 'cli/py/extract_pdf/menu.py',
        application: 'APP001',
        imported_by: ['MOD001'],
        functions: ['FUN001', 'FUN002'],
        classes: ['CLS001', 'CLS002'],
      },
    },

    classes: {
      CLS001: {
        id: 'CLS001',
        name: 'BaseWorkflow',
        description: 'Base workflow class',
        module_id: 'MOD002',
        functions: [],
      },
      CLS002: {
        id: 'CLS002',
        name: 'ExtractPDFWorkflow',
        description: 'PDF extraction workflow',
        module_id: 'MOD002',
        inherits_from: 'CLS001',
        functions: ['FUN002'],
      },
    },

    functions: {
      FUN001: {
        id: 'FUN001',
        name: 'pdf_menu',
        description: 'PDF extraction menu function',
        module_id: 'MOD002',
      },
      FUN002: {
        id: 'FUN002',
        name: 'extract_pdf_workflow',
        description: 'PDF extraction entry point',
        module_id: 'MOD002',
        class_id: 'CLS002',
        instantiates: ['CLS002'],
      },
      FUN003: {
        id: 'FUN003',
        name: 'main',
        description: 'Main CLI entry point function with menu selection',
        module_id: 'MOD001',
      },
      FUN004: {
        id: 'FUN004',
        name: 'pdf_menu (imported)',
        description: 'Imported pdf_menu function from extract_pdf.menu',
        module_id: 'MOD001',
      },
    },

    use_cases: {
      UC001: {
        id: 'UC001',
        name: 'Extract Text from PDFs',
        description: 'Extract text from PDF documents',
        primary_actor: 'ACT001',
        entry_function: 'FUN003',
        entry_class: 'CLS002',
        entry_module: 'MOD001',
      },
    },
  },
};
