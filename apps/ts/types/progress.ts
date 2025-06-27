/**
 * @fileoverview Auto-generated TypeScript types - DO NOT EDIT MANUALLY
 *
 * TypeScript types for question.progress.json file structure
 * These types mirror the Python Pydantic models for frontend consumption
 *
 * Based on: apps/py/types/models.py
 * Generated from Python types with additional TypeScript-specific utilities
 */

// ============================================================================
// ENUMS
// ============================================================================

export enum ProcessingState {
  NOT_STARTED = 'NOT_STARTED',
  INITIALIZED = 'INITIALIZED',
  LOCAL_EXTRACTION = 'LOCAL_EXTRACTION',
  LLM_EXTRACTION = 'LLM_EXTRACTION',
  MANUAL_REVIEW = 'MANUAL_REVIEW',
  PREPARE_DATA = 'PREPARE_DATA',
  CHUNKING = 'CHUNKING',
}

export enum ProcessingStatus {
  SUCCESS = 'SUCCESS',
  FAILED = 'FAILED',
  PARTIAL = 'PARTIAL',
}

export enum QuestionType {
  STARRED = 'STARRED',
  UNSTARRED = 'UNSTARRED',
}

export enum TableType {
  SINGLE_PAGE = 'single_page',
  MULTI_PAGE_START = 'multi_page_start',
  MULTI_PAGE_MIDDLE = 'multi_page_middle',
  MULTI_PAGE_END = 'multi_page_end',
}

export enum TransitionReason {
  AUTOMATIC_PROGRESSION = 'automatic_progression',
  MANUAL_ROLLBACK = 'manual_rollback',
  ERROR_RECOVERY = 'error_recovery',
  MANUAL_ADVANCEMENT = 'manual_advancement',
  SYSTEM_RETRY = 'system_retry',
}

export enum TriggerSource {
  SYSTEM = 'system',
  USER = 'user',
  AUTOMATED_PROCESS = 'automated_process',
  ERROR_HANDLER = 'error_handler',
}

export enum TransitionCondition {
  HAS_TABLES = 'has_tables',
  NO_TABLES = 'no_tables',
}

// ============================================================================
// BASE TYPES
// ============================================================================

export interface TableMetadata {
  table_number: number;
  page: number;
  accuracy: number;
  num_columns: number;
  num_rows: number;
}

export interface IssueFlag {
  type: string; // e.g., "missing_table_extraction", "wrong_table_structure", "custom_issue"
  description: string;
  severity: string; // "high", "medium", "low"
  flagged_by: string;
  flagged_at: string; // ISO date string
}

export interface ProcessingMetadata {
  processing_time_seconds: number;
  pages_processed: number;
  pages_failed: number;
  llm_model_used?: string; // For LLM extraction step
  reviewer?: string; // For manual review step
}

// ============================================================================
// STATE-SPECIFIC DATA TYPES
// ============================================================================

export interface InitializedData {
  status: ProcessingStatus;

  // Question metadata
  question_number: number;
  subjects: string;
  loksabha_number: string;
  member: string[];
  ministry: string;
  type: QuestionType;
  date: string;
  questions_file_path_local: string;
  questions_file_path_web: string;
  questions_file_path_hindi_local?: string;
  questions_file_path_hindi_web?: string;
  question_text?: string;
  answer_text?: string;
  session_number: string;

  // Processing metadata
  started_by?: string;
  notes?: string;
}

export interface LocalExtractionPageData {
  has_tables: boolean;
  num_tables: number;
  text: string;
  errors?: string[];
}

export interface LocalExtractionData {
  status: ProcessingStatus;
  processing_metadata: ProcessingMetadata;
  pages: Record<number, LocalExtractionPageData>;
  extracted_text_path: string;
  extracted_tables_path?: string;
  table_metadata: TableMetadata[];
  error_message?: string;

  // Document-level table summary (aggregated from page-level data)
  has_tables: boolean;
  total_tables: number;
  pages_with_tables: number;
}

export interface LlmExtractionPageData {
  has_tables: boolean;
  num_tables: number;
  text: string;

  // Separate fields for different table types
  single_page_tables: Record<string, any>[];
  multi_page_table_file_path?: string; // Key for multi_page_table_files lookup

  errors?: string[];

  // Table metadata
  has_multi_page_tables: boolean;
  has_multiple_tables: boolean;
  table_file_name?: string;
  text_file_name?: string;
}

export interface LlmExtractionData {
  status: ProcessingStatus;
  processing_metadata: ProcessingMetadata;
  pages: Record<number, LlmExtractionPageData>;
  extracted_text_path: string;
  extracted_tables_path?: string;
  error_message?: string;

  // Table statistics
  total_tables: number;
  successful_tables: number;
  failed_tables: number;
  multi_page_tables: number;
  single_page_tables: number;
  multi_page_table_files?: Record<string, Record<string, any>>;
}

export interface ManualReviewTableData {
  id: string;
  content: Record<string, any>;
  table_type: TableType;
}

export interface ManualReviewPageData {
  text: string;
  has_tables: boolean;
  num_tables: number;
  has_multiple_tables: boolean;
  is_multi_page_table_starting_page: boolean;
  is_multi_page_table_ending_page: boolean;
  is_multi_page_table_middle_page: boolean;
  has_multi_page_tables: boolean;
  tables: ManualReviewTableData[];
  passed_review: boolean;
  flags: IssueFlag[];

  // Granular edit tracking
  text_edited: boolean;
  tables_edited_ids: string[];
}

export interface ManualReviewData {
  status: ProcessingStatus;
  processing_metadata: ProcessingMetadata;
  pages: Record<number, ManualReviewPageData>;
  error_message?: string;
}

export interface PrepareDataData {
  status: ProcessingStatus;
  processing_metadata: ProcessingMetadata;
  data: Record<string, any>;
  error_message?: string;
}

export interface ChunkingData {
  chunks_path: string;
  num_chunks: number;
  chunk_size: number;
  overlap_size: number;
  chunking_strategy: string;
}

// ============================================================================
// UNION TYPES
// ============================================================================

export type PageData = LocalExtractionPageData | LlmExtractionPageData | ManualReviewPageData;

export type PageProcessingData =
  | InitializedData
  | LocalExtractionData
  | LlmExtractionData
  | ManualReviewData
  | PrepareDataData;

// ============================================================================
// MAIN STRUCTURE TYPES
// ============================================================================

export interface StateData {
  status: ProcessingStatus;
  timestamp: string; // ISO date string
  data: Record<string, any>;
  state: ProcessingState;
  meta: Record<string, any>;
  errors: string[];

  // Transition metadata for audit trail
  transition_reason?: TransitionReason; // enum instead of string
  triggered_by?: TriggerSource; // enum instead of string
  previous_state?: ProcessingState; // Previous state (especially useful for rollbacks)
}

export interface BaseProgressFileStructure {
  current_state: string; // ISO date string
  states: StateData[]; // Array of state entries with audit trail
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
}

export interface ProgressFileStructure extends BaseProgressFileStructure {
  current_state: ProcessingState;
  states: StateData[]; // Array of state entries with audit trail
}

// ============================================================================
// STATE TRANSITION TYPES
// ============================================================================

export interface StateTransition {
  from_state: ProcessingState;
  to_state: ProcessingState;
  required_status?: ProcessingStatus;
  condition?: TransitionCondition; // enum instead of string
}

export interface TransitionValidationDetails {
  transition_exists: boolean;
  required_status?: ProcessingStatus;
  condition?: TransitionCondition;
  status_check: string;
  condition_check: string;
}

export interface TransitionValidationResult {
  is_valid: boolean;
  current_state: ProcessingState;
  target_state: ProcessingState;
  error?: string;
  details: TransitionValidationDetails;
}

// ============================================================================
// CONSTANTS
// ============================================================================

export const STATE_ORDER: ProcessingState[] = [
  ProcessingState.NOT_STARTED,
  ProcessingState.INITIALIZED,
  ProcessingState.LOCAL_EXTRACTION,
  ProcessingState.LLM_EXTRACTION,
  ProcessingState.MANUAL_REVIEW,
  ProcessingState.PREPARE_DATA,
  ProcessingState.CHUNKING,
];

export const VALID_TRANSITIONS: StateTransition[] = [
  { from_state: ProcessingState.NOT_STARTED, to_state: ProcessingState.INITIALIZED },
  { from_state: ProcessingState.INITIALIZED, to_state: ProcessingState.LOCAL_EXTRACTION },
  {
    from_state: ProcessingState.LOCAL_EXTRACTION,
    to_state: ProcessingState.LLM_EXTRACTION,
    required_status: ProcessingStatus.SUCCESS,
    condition: TransitionCondition.HAS_TABLES,
  },
  {
    from_state: ProcessingState.LOCAL_EXTRACTION,
    to_state: ProcessingState.MANUAL_REVIEW,
    required_status: ProcessingStatus.SUCCESS,
    condition: TransitionCondition.NO_TABLES,
  },
  {
    from_state: ProcessingState.LLM_EXTRACTION,
    to_state: ProcessingState.LLM_EXTRACTION,
  },
  {
    from_state: ProcessingState.LLM_EXTRACTION,
    to_state: ProcessingState.MANUAL_REVIEW,
    required_status: ProcessingStatus.SUCCESS,
  },
  {
    from_state: ProcessingState.MANUAL_REVIEW,
    to_state: ProcessingState.PREPARE_DATA,
    required_status: ProcessingStatus.SUCCESS,
  },
  {
    from_state: ProcessingState.PREPARE_DATA,
    to_state: ProcessingState.CHUNKING,
    required_status: ProcessingStatus.SUCCESS,
  },
];

// ============================================================================
// TYPE GUARDS
// ============================================================================

export function isProcessingState(value: string): value is ProcessingState {
  return Object.values(ProcessingState).includes(value as ProcessingState);
}

export function isProcessingStatus(value: string): value is ProcessingStatus {
  return Object.values(ProcessingStatus).includes(value as ProcessingStatus);
}

export function isQuestionType(value: string): value is QuestionType {
  return Object.values(QuestionType).includes(value as QuestionType);
}

export function isTableType(value: string): value is TableType {
  return Object.values(TableType).includes(value as TableType);
}

export function isTransitionReason(value: string): value is TransitionReason {
  return Object.values(TransitionReason).includes(value as TransitionReason);
}

export function isTriggerSource(value: string): value is TriggerSource {
  return Object.values(TriggerSource).includes(value as TriggerSource);
}

export function isTransitionCondition(value: string): value is TransitionCondition {
  return Object.values(TransitionCondition).includes(value as TransitionCondition);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Type-safe way to get state data from the progress file
 */
export function getStateData<T = any>(progressFile: ProgressFileStructure, state: ProcessingState): T | undefined {
  const stateData = progressFile.states.find((s) => s.state === state);
  return stateData?.data as T;
}

/**
 * Check if a state exists in the progress file
 */
export function hasState(progressFile: ProgressFileStructure, state: ProcessingState): boolean {
  return progressFile.states.some((s) => s.state === state);
}

/**
 * Get the current (active) state data from the states array
 */
export function getCurrentStateEntry(progressFile: ProgressFileStructure): StateData | undefined {
  // The current state is the last entry in the states array
  if (progressFile.states.length === 0) {
    return undefined;
  }

  // Find the last entry matching the current state
  // (in case of rollbacks, we want the most recent entry for that state)
  for (let i = progressFile.states.length - 1; i >= 0; i--) {
    if (progressFile.states[i].state === progressFile.current_state) {
      return progressFile.states[i];
    }
  }

  return undefined;
}

/**
 * Get the current state data with proper typing
 */
export function getCurrentStateData<T = any>(progressFile: ProgressFileStructure): T | undefined {
  const currentEntry = getCurrentStateEntry(progressFile);
  return currentEntry?.data as T;
}
