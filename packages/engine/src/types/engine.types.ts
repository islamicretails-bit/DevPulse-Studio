/**
 * DevPulse Studio Pro Engine - Enterprise Core Types
 * Path: packages/engine/src/types/engine.types.ts
 *
 * This file defines all system models, agent communication payloads, 
 * state persistence structures, and execution metrics.
 */

// ==========================================
// 1. API Configuration & Key Management
// ==========================================

export type SupportedProvider = 'groq' | 'openai' | 'anthropic';

export interface ApiKeyConfig {
  id: string;
  provider: SupportedProvider;
  key: string;
  rateLimitedUntil?: number; // Timestamp when key resets
  requestCount: number;
  totalTokensUsed: number;
  isActive: boolean;
}

export interface EngineGlobalConfig {
  projectRootPath: string;
  progressFilePath: string;
  keys: ApiKeyConfig[];
  maxParallelWorkers: number;
  requestCooldownMs: number;
  autoHealEnabled: boolean;
  strictNoTruncation: boolean;
}

// ==========================================
// 2. Project Blueprint & File Architecture
// ==========================================

export interface FileBlueprint {
  filePath: string; // Relative path, e.g., 'apps/web/src/components/Header.tsx'
  description: string;
  moduleGroup: string; // E.g., 'ui', 'api', 'database', 'auth'
  dependencies: string[]; // List of relative file paths this file imports/depends on
  estimatedLines: number;
  isCriticalPath: boolean;
}

export interface ProjectArchitecture {
  projectName: string;
  version: string;
  architectureOverview: string;
  framework: 'Next.js' | 'Node.js' | 'Express' | 'Custom';
  targetDeployment: 'Netlify' | 'Vercel' | 'Docker';
  totalFilesCount: number;
  files: FileBlueprint[];
}

// ==========================================
// 3. File Execution & Task Tracking
// ==========================================

export type TaskStatus = 'pending' | 'generating' | 'healing' | 'completed' | 'failed' | 'paused';

export interface FileTask {
  id: string;
  filePath: string;
  description: string;
  moduleGroup: string;
  dependencies: string[];
  status: TaskStatus;
  attempts: number;
  lastErrorMessage?: string;
  generatedCode?: string;
  createdAt: number;
  completedAt?: number;
}

// ==========================================
// 4. Progress & State Persistence (Auto-Resume)
// ==========================================

export interface ExecutionMetrics {
  startTime: number;
  endTime?: number;
  totalTokensConsumed: number;
  totalRateLimitsEncountered: number;
  successfulFilesCount: number;
  failedFilesCount: number;
}

export interface ProgressState {
  projectId: string;
  projectName: string;
  projectRootPath: string;
  currentPhase: 'architecting' | 'generating' | 'healing' | 'completed';
  totalFiles: number;
  completedCount: number;
  failedCount: number;
  isPaused: boolean;
  pauseReason?: string;
  tasks: FileTask[];
  metrics: ExecutionMetrics;
  lastUpdated: number;
}

// ==========================================
// 5. Agent Input / Output Payloads
// ==========================================

export interface ArchitectAgentInput {
  userPrompt: string;
  frameworkPreference?: string;
  targetDeployment?: string;
  existingFilesContext?: string[];
}

export interface CoderAgentInput {
  task: FileTask;
  architectureContext: ProjectArchitecture;
  importedTypesContext?: string;
  strictRules: string[];
}

export interface CoderAgentResult {
  filePath: string;
  rawCode: string;
  tokensUsed: number;
  providerUsed: SupportedProvider;
  executionTimeMs: number;
}

export interface AutoHealInput {
  filePath: string;
  code: string;
  buildErrorLog?: string;
}

export interface AutoHealResult {
  filePath: string;
  fixedCode: string;
  wasModified: boolean;
  healedErrors: string[];
}

// ==========================================
// 6. Engine Event Listeners (For UI Progress)
// ==========================================

export type EngineEventType =
  | 'PROGRESS_UPDATE'
  | 'RATE_LIMIT_HIT'
  | 'AUTO_PAUSE'
  | 'AUTO_RESUME'
  | 'FILE_SUCCESS'
  | 'FILE_ERROR';

export interface EngineEvent {
  type: EngineEventType;
  timestamp: number;
  message: string;
  payload?: any;
}

export type EngineEventListener = (event: EngineEvent) => void;
// 1. نئے ایونٹ کی اقسام شامل کریں
export type EngineEventType =
  | 'ARCHITECT_STARTED'
  | 'ARCHITECT_COMPLETED'
  | 'TESTER_STARTED'      // 👈 نیا ایونٹ: Tester Agent
  | 'TESTER_COMPLETED'    // 👈 نیا ایونٹ
  | 'FILE_SUCCESS'
  | 'FILE_ERROR';

// 2. نئے ایجنٹ کے انپٹ کا انٹرفیس بنائیں
export interface TesterAgentInput {
  filePath: string;
  codeContent: string;
}

// 3. ایجنٹ کے آؤٹ پٹ کی ساخت متعین کریں
export interface TesterOutput {
  testCode: string;
  testFilePath: string;
  passedSyntaxCheck: boolean;
}
