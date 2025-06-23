#!/usr/bin/env node
/**
 * Script to remove duplicate entries from failed_sansad_session_question_download
 * that also exist in downloaded_sansad_session_questions.
 */

import * as fs from 'fs';
import * as path from 'path';
import { promisify } from 'util';

// Promisify fs functions
const readFile = promisify(fs.readFile);
const writeFile = promisify(fs.writeFile);
const copyFile = promisify(fs.copyFile);
const access = promisify(fs.access);
const readdir = promisify(fs.readdir);
const stat = promisify(fs.stat);

// Types
interface FailedQuestionDownload {
  questions_file_path_web: string;
  question_number: number;
  type: 'STARRED' | 'UNSTARRED';
}

interface ParliamentQuestion {
  question_number: number;
  subjects: string;
  loksabha_number: string;
  member: string[];
  ministry: string;
  type: 'STARRED' | 'UNSTARRED';
  date: string;
  questions_file_path_local: string | null;
  questions_file_path_web: string;
  questions_file_path_hindi_local: string | null;
  questions_file_path_hindi_web: string;
  question_text: string | null;
  answer_text: string | null;
  session_number: string;
}

interface PipelineData {
  failed_sansad_session_question_download: FailedQuestionDownload[];
  downloaded_sansad_session_questions: ParliamentQuestion[];
}

interface DataStructure {
  data: PipelineData;
}

// Logger
class Logger {
  private static instance: Logger;
  private logLevel: 'INFO' | 'DEBUG' | 'WARN' | 'ERROR' = 'INFO';

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  setLogLevel(level: 'INFO' | 'DEBUG' | 'WARN' | 'ERROR'): void {
    this.logLevel = level;
  }

  private shouldLog(level: 'INFO' | 'DEBUG' | 'WARN' | 'ERROR'): boolean {
    const levels = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 };
    return levels[level] >= levels[this.logLevel];
  }

  info(message: string): void {
    if (this.shouldLog('INFO')) {
      console.log(`[INFO] ${message}`);
    }
  }

  debug(message: string): void {
    if (this.shouldLog('DEBUG')) {
      console.log(`[DEBUG] ${message}`);
    }
  }

  warn(message: string): void {
    if (this.shouldLog('WARN')) {
      console.warn(`[WARN] ${message}`);
    }
  }

  error(message: string): void {
    if (this.shouldLog('ERROR')) {
      console.error(`[ERROR] ${message}`);
    }
  }
}

const logger = Logger.getInstance();

/**
 * Load JSON file and return the data
 */
async function loadJsonFile(filePath: string): Promise<DataStructure> {
  try {
    const data = await readFile(filePath, 'utf-8');
    return JSON.parse(data) as DataStructure;
  } catch (error) {
    logger.error(`Error loading ${filePath}: ${error}`);
    throw error;
  }
}

/**
 * Save data to JSON file
 */
async function saveJsonFile(filePath: string, data: DataStructure): Promise<void> {
  try {
    await writeFile(filePath, JSON.stringify(data, null, 2), 'utf-8');
    logger.info(`Saved updated data to ${filePath}`);
  } catch (error) {
    logger.error(`Error saving ${filePath}: ${error}`);
    throw error;
  }
}

/**
 * Create a set of unique identifiers for downloaded questions
 */
function createDownloadedQuestionsSet(downloadedQuestions: ParliamentQuestion[]): Set<string> {
  const downloadedSet = new Set<string>();

  for (const question of downloadedQuestions) {
    const questionNumber = question.question_number;
    const questionsFilePathWeb = question.questions_file_path_web;

    if (questionNumber !== undefined && questionsFilePathWeb) {
      const key = `${questionNumber}:${questionsFilePathWeb}`;
      downloadedSet.add(key);
    }
  }

  return downloadedSet;
}

/**
 * Remove failed downloads that also exist in downloaded questions
 */
function deduplicateFailedDownloads(data: DataStructure): DataStructure {
  const pipelineData = data.data;

  // Get the lists
  const failedDownloads = pipelineData.failed_sansad_session_question_download || [];
  const downloadedQuestions = pipelineData.downloaded_sansad_session_questions || [];

  logger.info(`Original failed downloads count: ${failedDownloads.length}`);
  logger.info(`Downloaded questions count: ${downloadedQuestions.length}`);

  // Create set of downloaded questions for efficient lookup
  const downloadedSet = createDownloadedQuestionsSet(downloadedQuestions);

  // Filter out failed downloads that exist in downloaded questions
  const deduplicatedFailedDownloads: FailedQuestionDownload[] = [];
  let removedCount = 0;

  for (const failedDownload of failedDownloads) {
    const questionNumber = failedDownload.question_number;
    const questionsFilePathWeb = failedDownload.questions_file_path_web;

    if (questionNumber !== undefined && questionsFilePathWeb) {
      const key = `${questionNumber}:${questionsFilePathWeb}`;

      if (downloadedSet.has(key)) {
        removedCount++;
        logger.debug(`Removing duplicate: question_number=${questionNumber}, url=${questionsFilePathWeb}`);
      } else {
        deduplicatedFailedDownloads.push(failedDownload);
      }
    } else {
      // Keep entries with missing data for manual review
      logger.warn(`Failed download with missing data: ${JSON.stringify(failedDownload)}`);
      deduplicatedFailedDownloads.push(failedDownload);
    }
  }

  // Update the data
  pipelineData.failed_sansad_session_question_download = deduplicatedFailedDownloads;

  logger.info(`Removed ${removedCount} duplicate entries`);
  logger.info(`Final failed downloads count: ${deduplicatedFailedDownloads.length}`);

  return data;
}

/**
 * Process a single JSON file to deduplicate failed downloads
 */
async function processFile(filePath: string, createBackup: boolean = true): Promise<void> {
  logger.info(`Processing file: ${filePath}`);

  // Create backup if requested
  if (createBackup) {
    const backupPath = filePath + '.backup';
    try {
      await access(backupPath);
      logger.info(`Backup already exists: ${backupPath}`);
    } catch {
      await copyFile(filePath, backupPath);
      logger.info(`Created backup: ${backupPath}`);
    }
  }

  // Load and process the data
  const data = await loadJsonFile(filePath);
  const updatedData = deduplicateFailedDownloads(data);

  // Save the updated data
  await saveJsonFile(filePath, updatedData);
}

/**
 * Process all JSON files in a directory that match the pattern
 */
async function processDirectory(
  directoryPath: string,
  pattern: string = '*.log.json',
  createBackup: boolean = true
): Promise<void> {
  logger.info(`Processing directory: ${directoryPath}`);

  try {
    const files = await readdir(directoryPath);
    const jsonFiles = files.filter((file) => {
      if (pattern === '*.log.json') {
        return file.endsWith('.log.json');
      }
      // Simple pattern matching - can be enhanced if needed
      return file.includes(pattern.replace('*', ''));
    });

    logger.info(`Found ${jsonFiles.length} files matching pattern '${pattern}'`);

    for (const file of jsonFiles) {
      const filePath = path.join(directoryPath, file);
      try {
        await processFile(filePath, createBackup);
      } catch (error) {
        logger.error(`Error processing ${filePath}: ${error}`);
      }
    }
  } catch (error) {
    logger.error(`Error reading directory ${directoryPath}: ${error}`);
    throw error;
  }
}

/**
 * Check if path is a file
 */
async function isFile(filePath: string): Promise<boolean> {
  try {
    const stats = await stat(filePath);
    return stats.isFile();
  } catch {
    return false;
  }
}

/**
 * Check if path is a directory
 */
async function isDirectory(dirPath: string): Promise<boolean> {
  try {
    const stats = await stat(dirPath);
    return stats.isDirectory();
  } catch {
    return false;
  }
}

/**
 * Main function to run the deduplication script
 */
async function main(): Promise<void> {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log(`
Usage: npx ts-node deduplicate_failed_downloads.ts <path> [options]

Arguments:
  path                    Path to JSON file or directory to process

Options:
  --pattern <pattern>     File pattern to match (default: *.log.json)
  --no-backup            Don't create backup files
  --debug                Enable debug logging
  --help                 Show this help message

Examples:
  npx ts-node deduplicate_failed_downloads.ts path/to/your/file.log.json
  npx ts-node deduplicate_failed_downloads.ts path/to/logs/directory/
  npx ts-node deduplicate_failed_downloads.ts path/to/logs/ --pattern "*.json"
  npx ts-node deduplicate_failed_downloads.ts path/to/your/file.log.json --no-backup
`);
    return;
  }

  let filePath = '';
  let pattern = '*.log.json';
  let createBackup = true;

  // Parse arguments
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === '--help') {
      console.log(`
Usage: npx ts-node deduplicate_failed_downloads.ts <path> [options]

Arguments:
  path                    Path to JSON file or directory to process

Options:
  --pattern <pattern>     File pattern to match (default: *.log.json)
  --no-backup            Don't create backup files
  --debug                Enable debug logging
  --help                 Show this help message

Examples:
  npx ts-node deduplicate_failed_downloads.ts path/to/your/file.log.json
  npx ts-node deduplicate_failed_downloads.ts path/to/logs/directory/
  npx ts-node deduplicate_failed_downloads.ts path/to/logs/ --pattern "*.json"
  npx ts-node deduplicate_failed_downloads.ts path/to/your/file.log.json --no-backup
`);
      return;
    } else if (arg === '--pattern') {
      if (i + 1 < args.length) {
        pattern = args[++i];
      } else {
        logger.error('--pattern requires a value');
        return;
      }
    } else if (arg === '--no-backup') {
      createBackup = false;
    } else if (arg === '--debug') {
      logger.setLogLevel('DEBUG');
    } else if (!filePath) {
      filePath = arg;
    }
  }

  if (!filePath) {
    logger.error('No path specified');
    return;
  }

  try {
    if (await isFile(filePath)) {
      await processFile(filePath, createBackup);
    } else if (await isDirectory(filePath)) {
      await processDirectory(filePath, pattern, createBackup);
    } else {
      logger.error(`Path does not exist: ${filePath}`);
    }
  } catch (error) {
    logger.error(`Error processing ${filePath}: ${error}`);
    process.exit(1);
  }
}

// Run the script
if (require.main === module) {
  main().catch((error) => {
    logger.error(`Unhandled error: ${error}`);
    process.exit(1);
  });
}

export {
  deduplicateFailedDownloads,
  processFile,
  processDirectory,
  FailedQuestionDownload,
  ParliamentQuestion,
  PipelineData,
  DataStructure,
};
