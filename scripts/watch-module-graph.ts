#!/usr/bin/env ts-node

/**
 * File watcher for Enhanced Module Graph
 *
 * Watches for changes in relevant files and regenerates docs/index.ts
 */

import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';
import chokidar from 'chokidar';

// Paths to watch for changes
const WATCH_PATHS = [
  'cli/**/*.py',
  'api/**/*.ts',
  'api/**/*.py',
  'workflows/**/*.ts',
  'workflows/**/*.py',
  'package.json',
];

// Target file to regenerate
const TARGET_FILE = 'docs/index.ts';

function logMessage(message: string) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${message}`);
}

function regenerateModuleGraph() {
  try {
    logMessage('🔄 Regenerating module graph...');

    // For now, just touch the file to indicate it needs manual update
    // In the future, this could call an auto-generation script
    const currentTime = new Date().toISOString();
    const comment = `\n// Last auto-check: ${currentTime}\n`;

    fs.appendFileSync(TARGET_FILE, comment);

    logMessage('✅ Module graph check completed');
  } catch (error) {
    logMessage(`❌ Error regenerating module graph: ${error}`);
  }
}

function startWatching() {
  logMessage('👀 Starting file watcher for Enhanced Module Graph...');
  logMessage(`Watching paths: ${WATCH_PATHS.join(', ')}`);

  const watcher = chokidar.watch(WATCH_PATHS, {
    ignored: ['**/node_modules/**', '**/.git/**', '**/dist/**', '**/build/**', '**/__pycache__/**', '**/*.pyc'],
    persistent: true,
    ignoreInitial: true,
  });

  watcher
    .on('add', (filePath) => {
      logMessage(`📁 File added: ${filePath}`);
      regenerateModuleGraph();
    })
    .on('change', (filePath) => {
      logMessage(`📝 File changed: ${filePath}`);
      regenerateModuleGraph();
    })
    .on('unlink', (filePath) => {
      logMessage(`🗑️  File deleted: ${filePath}`);
      regenerateModuleGraph();
    })
    .on('error', (error) => {
      logMessage(`❌ Watcher error: ${error}`);
    });

  logMessage('🚀 File watcher started successfully');

  // Keep the process running
  process.on('SIGINT', () => {
    logMessage('👋 Stopping file watcher...');
    watcher.close();
    process.exit(0);
  });
}

if (require.main === module) {
  startWatching();
}
