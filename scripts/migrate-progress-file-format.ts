#!/usr/bin/env node
/**
 * Migration script to convert progress files from dict-based to array-based format.
 *
 * This script:
 * 1. Reads existing progress files with dict-based states
 * 2. Converts them to the new array-based format with audit trail
 * 3. Preserves all existing data
 * 4. Adds reasonable defaults for new fields
 * 5. Creates backup copies of original files
 *
 * Usage:
 *     npx tsx scripts/migrate-progress-file-format.ts [--dry-run] [--backup-dir BACKUP_DIR] [PATH_TO_SEARCH]
 *
 * Examples:
 *     # Dry run to see what would be changed
 *     npx tsx scripts/migrate-progress-file-format.ts --dry-run
 *
 *     # Migrate all progress files, creating backups
 *     npx tsx scripts/migrate-progress-file-format.ts --backup-dir ./backups
 *
 *     # Migrate specific directory
 *     npx tsx scripts/migrate-progress-file-format.ts /path/to/documents
 *
 * Safety Levels Comparison:
 * ┌─────────────────────────────────────┬──────────────────────────┬──────────────┬─────────────────────────────────────┐
 * │ Option                              │ Backup Location          │ Auto-Cleanup │ Safety Level                        │
 * ├─────────────────────────────────────┼──────────────────────────┼──────────────┼─────────────────────────────────────┤
 * │ No flags                            │ Same directory (temp)    │ ✅ Always    │ 🟡 Safe but no recovery after cleanup │
 * │ --backup-dir ./backups              │ Dedicated directory      │ ❌ Never     │ 🟢 Safest - keeps backups             │
 * │ --backup-dir ./backups --cleanup... │ Dedicated directory      │ ✅ After     │ 🟡 Safe during migration             │
 * │ --skip-verification                 │ Same directory (temp)    │ ✅ Always    │ 🔴 Risky - no verification           │
 * └─────────────────────────────────────┴──────────────────────────┴──────────────┴─────────────────────────────────────┘
 */

import * as fs from 'fs';
import * as path from 'path';

// Promisify fs functions
const readdir = fs.promises.readdir;
const stat = fs.promises.stat;

// Define the state order for migration
const STATE_ORDER = [
  'NOT_STARTED',
  'INITIALIZED',
  'LOCAL_EXTRACTION',
  'LLM_EXTRACTION',
  'MANUAL_REVIEW',
  'PREPARE_DATA',
  'CHUNKING',
] as const;

interface MigrationStats {
  filesFound: number;
  filesMigrated: number;
  filesSkipped: number;
  filesFailed: number;
  backupsCreated: number;
  verificationsSucceeded: number;
  verificationsFailed: number;
}

interface MigrationOptions {
  dryRun: boolean;
  backupDir?: string;
  cleanupBackups: boolean;
  skipVerification: boolean;
}

interface OldProgressFile {
  current_state: string;
  states: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface NewStateEntry {
  status: string;
  timestamp: string;
  data: Record<string, any>;
  state: string;
  meta: Record<string, any>;
  errors: string[];
  transition_reason: string;
  triggered_by: string;
  previous_state: string | null;
}

interface NewProgressFile {
  current_state: string;
  states: NewStateEntry[];
  created_at: string;
  updated_at: string;
}

class ProgressFileMigrator {
  private backupDir: string | undefined;
  private migrationStats: MigrationStats;

  constructor(backupDir?: string) {
    this.backupDir = backupDir;
    this.migrationStats = {
      filesFound: 0,
      filesMigrated: 0,
      filesSkipped: 0,
      filesFailed: 0,
      backupsCreated: 0,
      verificationsSucceeded: 0,
      verificationsFailed: 0,
    };
  }

  async findProgressFiles(searchPath: string): Promise<string[]> {
    const progressFiles: string[] = [];

    // Check if searchPath is a specific file
    const searchStat = await stat(searchPath);
    if (searchStat.isFile() && path.basename(searchPath) === 'question.progress.json') {
      progressFiles.push(searchPath);
    } else if (searchStat.isDirectory()) {
      // Recursively search for progress files
      await this.findProgressFilesRecursive(searchPath, progressFiles);
    }

    console.log(`Found ${progressFiles.length} progress files in ${searchPath}`);
    return progressFiles;
  }

  private async findProgressFilesRecursive(dir: string, progressFiles: string[]): Promise<void> {
    try {
      const entries = await readdir(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
          // Recursively search subdirectories
          await this.findProgressFilesRecursive(fullPath, progressFiles);
        } else if (entry.isFile() && entry.name === 'question.progress.json') {
          progressFiles.push(fullPath);
        }
      }
    } catch (error) {
      console.warn(`Warning: Could not access directory ${dir}: ${error}`);
    }
  }

  isOldFormat(progressData: any): progressData is OldProgressFile {
    const states = progressData?.states;

    // Old format: states is a dict with string keys
    // New format: states is a list of objects
    if (states && typeof states === 'object' && !Array.isArray(states)) {
      return true;
    } else if (Array.isArray(states)) {
      return false;
    } else {
      console.warn(`Unknown states format: ${typeof states}`);
      return false;
    }
  }

  createBackup(originalFile: string): string | null {
    if (!this.backupDir) {
      return null;
    }

    // Create backup directory if it doesn't exist
    if (!fs.existsSync(this.backupDir)) {
      fs.mkdirSync(this.backupDir, { recursive: true });
    }

    // Create backup with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '_').replace('T', '_').slice(0, 19);
    const originalName = path.basename(originalFile);
    const backupName = `${path.parse(originalName).name}_${timestamp}${path.parse(originalName).ext}`;
    const backupPath = path.join(this.backupDir, backupName);

    try {
      fs.copyFileSync(originalFile, backupPath);
      this.migrationStats.backupsCreated++;
      console.log(`Created backup: ${backupPath}`);
      return backupPath;
    } catch (error) {
      console.error(`Failed to create backup for ${originalFile}:`, error);
      return null;
    }
  }

  /**
   * Create a temporary backup in the same directory as the original file
   */
  createTemporaryBackup(originalFile: string): string | null {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '_').replace('T', '_').slice(0, 19);
      const dir = path.dirname(originalFile);
      const originalName = path.basename(originalFile);
      const tempBackupName = `${path.parse(originalName).name}_temp_backup_${timestamp}${path.parse(originalName).ext}`;
      const tempBackupPath = path.join(dir, tempBackupName);

      fs.copyFileSync(originalFile, tempBackupPath);
      console.log(`Created temporary backup: ${tempBackupPath}`);
      return tempBackupPath;
    } catch (error) {
      console.error(`Failed to create temporary backup for ${originalFile}:`, error);
      return null;
    }
  }

  convertToArrayFormat(oldData: OldProgressFile): NewProgressFile {
    const oldStates = oldData.states || {};
    const currentState = oldData.current_state;

    // Convert states dict to array, preserving order
    const newStates: NewStateEntry[] = [];

    // Process states in the defined order
    for (const stateName of STATE_ORDER) {
      if (stateName in oldStates) {
        const oldStateData = oldStates[stateName];

        // Convert old dict format to new StateData format
        const newStateEntry: NewStateEntry = {
          status: oldStateData.status || 'SUCCESS',
          timestamp: oldStateData.timestamp || new Date().toISOString(),
          data: oldStateData.data || {},
          state: stateName,
          meta: oldStateData.meta || {},
          errors: oldStateData.errors || [],

          // Add new fields with reasonable defaults
          transition_reason: 'automatic_progression',
          triggered_by: 'system',
          previous_state: null, // Will be set below
        };

        // Set previous_state for audit trail
        if (newStates.length > 0) {
          newStateEntry.previous_state = newStates[newStates.length - 1].state;
        }

        newStates.push(newStateEntry);
      }
    }

    // Create new progress file structure
    const newData: NewProgressFile = {
      current_state: currentState,
      states: newStates,
      created_at: oldData.created_at || new Date().toISOString(),
      updated_at: oldData.updated_at || new Date().toISOString(),
    };

    return newData;
  }

  /**
   * Verify that the migration was successful by comparing original and migrated data
   */
  verifyMigration(originalData: OldProgressFile, migratedFile: string): boolean {
    try {
      // Read the migrated file
      const migratedContent = fs.readFileSync(migratedFile, 'utf-8');
      const migratedData: NewProgressFile = JSON.parse(migratedContent);

      // Basic structure validation
      if (!migratedData.current_state || !Array.isArray(migratedData.states)) {
        console.error(`Verification failed: Invalid structure in ${migratedFile}`);
        return false;
      }

      // Verify current state matches
      if (originalData.current_state !== migratedData.current_state) {
        console.error(`Verification failed: Current state mismatch in ${migratedFile}`);
        return false;
      }

      // Verify all original states are preserved
      const originalStates = Object.keys(originalData.states || {});
      const migratedStates = migratedData.states.map((s) => s.state);

      for (const originalState of originalStates) {
        if (!migratedStates.includes(originalState)) {
          console.error(`Verification failed: Missing state ${originalState} in ${migratedFile}`);
          return false;
        }
      }

      // Verify data integrity for each state
      for (const stateEntry of migratedData.states) {
        const originalStateData = originalData.states[stateEntry.state];
        if (!originalStateData) continue;

        // Check that essential data is preserved
        if (originalStateData.status && originalStateData.status !== stateEntry.status) {
          console.error(`Verification failed: Status mismatch for state ${stateEntry.state} in ${migratedFile}`);
          return false;
        }

        // Check that data object is preserved
        if (originalStateData.data && JSON.stringify(originalStateData.data) !== JSON.stringify(stateEntry.data)) {
          console.error(`Verification failed: Data mismatch for state ${stateEntry.state} in ${migratedFile}`);
          return false;
        }
      }

      // Verify audit trail integrity
      for (let i = 1; i < migratedData.states.length; i++) {
        const currentState = migratedData.states[i];
        const previousState = migratedData.states[i - 1];

        if (currentState.previous_state !== previousState.state) {
          console.error(`Verification failed: Audit trail broken at state ${currentState.state} in ${migratedFile}`);
          return false;
        }
      }

      console.log(`✓ Verification passed for ${migratedFile}`);
      return true;
    } catch (error) {
      console.error(`Verification failed: Could not validate ${migratedFile}:`, error);
      return false;
    }
  }

  /**
   * Restore a file from backup
   */
  restoreFromBackup(backupPath: string, originalPath: string): boolean {
    try {
      fs.copyFileSync(backupPath, originalPath);
      console.log(`Restored ${originalPath} from backup ${backupPath}`);
      return true;
    } catch (error) {
      console.error(`Failed to restore ${originalPath} from backup ${backupPath}:`, error);
      return false;
    }
  }

  /**
   * Clean up backup file after successful migration
   */
  cleanupBackup(backupPath: string): boolean {
    try {
      fs.unlinkSync(backupPath);
      console.log(`Cleaned up backup: ${backupPath}`);
      return true;
    } catch (error) {
      console.error(`Failed to cleanup backup ${backupPath}:`, error);
      return false;
    }
  }

  migrateFile(filePath: string, options: MigrationOptions): boolean {
    try {
      // Read the original file
      const fileContent = fs.readFileSync(filePath, 'utf-8');
      const oldData = JSON.parse(fileContent);

      // Check if migration is needed
      if (!this.isOldFormat(oldData)) {
        console.log(`File already in new format: ${filePath}`);
        this.migrationStats.filesSkipped++;
        return true;
      }

      // Convert to new format
      const newData = this.convertToArrayFormat(oldData);

      if (options.dryRun) {
        console.log(`[DRY RUN] Would migrate: ${filePath}`);
        console.log(`[DRY RUN] Old states: ${Object.keys(oldData.states || {})}`);
        console.log(`[DRY RUN] New states: ${newData.states.map((s) => s.state)}`);
        this.migrationStats.filesMigrated++;
        return true;
      }

      // Create backup - either in specified backup dir or temporary backup
      let backupPath: string | null = null;
      let isTemporaryBackup = false;

      if (options.backupDir) {
        // User specified backup directory
        backupPath = this.createBackup(filePath);
        if (!backupPath) {
          console.error(`Failed to create backup for ${filePath}, skipping migration`);
          this.migrationStats.filesFailed++;
          return false;
        }
      } else {
        // No backup directory specified - create temporary backup for safety
        console.warn(`⚠️  No backup directory specified. Creating temporary backup for safety...`);
        backupPath = this.createTemporaryBackup(filePath);
        isTemporaryBackup = true;

        if (!backupPath) {
          console.error(`Failed to create temporary backup for ${filePath}. Migration too risky, aborting.`);
          this.migrationStats.filesFailed++;
          return false;
        }
      }

      // Write the new format
      fs.writeFileSync(filePath, JSON.stringify(newData, null, 2));

      console.log(`Successfully migrated: ${filePath}`);
      this.migrationStats.filesMigrated++;

      // Verify migration success
      if (!options.skipVerification) {
        const verificationPassed = this.verifyMigration(oldData, filePath);
        if (verificationPassed) {
          this.migrationStats.verificationsSucceeded++;
        } else {
          this.migrationStats.verificationsFailed++;

          // Restore from backup if verification fails
          console.log(`Migration verification failed, restoring from backup...`);
          this.restoreFromBackup(backupPath, filePath);
          this.migrationStats.filesFailed++;
          this.migrationStats.filesMigrated--; // Correct the stats
          return false;
        }
      }

      // Handle backup cleanup
      if (isTemporaryBackup) {
        // Always clean up temporary backups after successful migration
        console.log(`Cleaning up temporary backup...`);
        this.cleanupBackup(backupPath);
      } else if (options.cleanupBackups && backupPath) {
        // Clean up regular backups only if requested
        this.cleanupBackup(backupPath);
      }

      return true;
    } catch (error) {
      console.error(`Failed to migrate ${filePath}:`, error);
      this.migrationStats.filesFailed++;
      return false;
    }
  }

  async migrateAll(searchPath: string, options: MigrationOptions): Promise<void> {
    console.log(`Starting migration (dry_run=${options.dryRun}) in: ${searchPath}`);

    const progressFiles = await this.findProgressFiles(searchPath);
    this.migrationStats.filesFound = progressFiles.length;

    for (const filePath of progressFiles) {
      console.log(`Processing: ${filePath}`);
      this.migrateFile(filePath, options);
    }

    // Print summary
    const stats = this.migrationStats;
    console.log('Migration Summary:');
    console.log(`  Files found: ${stats.filesFound}`);
    console.log(`  Files migrated: ${stats.filesMigrated}`);
    console.log(`  Files skipped (already new format): ${stats.filesSkipped}`);
    console.log(`  Files failed: ${stats.filesFailed}`);
    console.log(`  Backups created: ${stats.backupsCreated}`);

    if (!options.skipVerification) {
      console.log(`  Verifications passed: ${stats.verificationsSucceeded}`);
      console.log(`  Verifications failed: ${stats.verificationsFailed}`);
    }

    if (stats.filesMigrated > 0 && stats.verificationsFailed === 0) {
      console.log('✅ All migrations completed successfully!');
    } else if (stats.verificationsFailed > 0) {
      console.log('⚠️  Some migrations failed verification and were restored from backup');
    }
  }
}

async function main(): Promise<number> {
  const args = process.argv.slice(2);

  // Simple argument parsing
  let searchPath = process.cwd();
  let dryRun = false;
  let backupDir: string | undefined;
  let cleanupBackups = false;
  let skipVerification = false;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === '--dry-run') {
      dryRun = true;
    } else if (arg === '--backup-dir') {
      backupDir = args[i + 1];
      i++; // Skip next argument
    } else if (arg === '--cleanup-backups') {
      cleanupBackups = true;
    } else if (arg === '--skip-verification') {
      skipVerification = true;
    } else if (arg === '--help' || arg === '-h') {
      console.log(`
Migration script to convert progress files from dict-based to array-based format.

Usage:
    npx tsx scripts/migrate-progress-file-format.ts [OPTIONS] [PATH_TO_SEARCH]

Options:
    --dry-run                 Show what would be changed without actually modifying files
    --backup-dir BACKUP_DIR   Directory to store backup copies of original files
                             (if not specified, temporary backups are created and auto-cleaned)
    --cleanup-backups        Delete backup files after successful migration and verification
                             (only applies to --backup-dir, temporary backups are always cleaned)
    --skip-verification      Skip post-migration data integrity verification
    --help, -h               Show this help message

Examples:
    # Dry run to see what would be changed
    npx tsx scripts/migrate-progress-file-format.ts --dry-run

    # Migrate with backups and cleanup after success
    npx tsx scripts/migrate-progress-file-format.ts --backup-dir ./backups --cleanup-backups

    # Migrate specific directory with verification
    npx tsx scripts/migrate-progress-file-format.ts /path/to/documents

    # Fast migration without verification (not recommended)
    npx tsx scripts/migrate-progress-file-format.ts --skip-verification

Safety Features:
    - Creates backups before migration (if --backup-dir specified)
    - Verifies data integrity after migration (unless --skip-verification)
    - Automatically restores from backup if verification fails
    - Can clean up backups after successful migration (with --cleanup-backups)
      `);
      return 0;
    } else if (!arg.startsWith('--')) {
      searchPath = arg;
    }
  }

  // Validate search path
  try {
    await stat(searchPath);
  } catch (error) {
    console.error(`Search path does not exist: ${searchPath}`);
    return 1;
  }

  // Create migrator and run
  const migrator = new ProgressFileMigrator(backupDir);

  // Safety warning if no backup directory specified
  if (!backupDir && !dryRun) {
    console.warn(`
⚠️  WARNING: No backup directory specified!
- Temporary backups will be created in the same directory as each file
- These temporary backups will be automatically cleaned up after successful migration
- Consider using --backup-dir for safer, persistent backups

Continue? (Ctrl+C to abort, or wait 3 seconds to proceed...)
    `);

    // Give user 3 seconds to abort
    await new Promise((resolve) => setTimeout(resolve, 3000));
  }

  const options: MigrationOptions = {
    dryRun,
    backupDir,
    cleanupBackups: cleanupBackups,
    skipVerification: skipVerification,
  };
  await migrator.migrateAll(searchPath, options);

  return 0;
}

if (require.main === module) {
  main()
    .then((code) => process.exit(code))
    .catch((error) => {
      console.error('Migration failed:', error);
      process.exit(1);
    });
}
