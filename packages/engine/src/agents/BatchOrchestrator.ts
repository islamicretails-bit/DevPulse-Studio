/**
 * DevPulse Studio Pro Engine - Batch Orchestrator
 * Path: packages/engine/src/agents/BatchOrchestrator.ts
 *
 * Core execution engine that coordinates multi-worker generation pipelines,
 * architectural blueprinting, code writing, and automated unit testing.
 */

import * as fs from 'fs';
import * as path from 'path';
import { ApiKeyRotator } from '../services/ApiKeyRotator';
import { RateLimitHandler } from '../services/RateLimitHandler';
import { ArchitectAgent } from './ArchitectAgent';
import { CoderAgent } from './CoderAgent';
import { TesterAgent } from './TesterAgent';
import {
  EngineGlobalConfig,
  EngineEvent,
  EngineEventListener,
  EngineState,
  FileTask,
  ArchitectBlueprint,
} from '../types/engine.types';

export class BatchOrchestrator {
  private config: EngineGlobalConfig;
  private keyRotator: ApiKeyRotator;
  private rateLimiter: RateLimitHandler;
  private architectAgent: ArchitectAgent;
  private coderAgent: CoderAgent;
  private testerAgent: TesterAgent;
  private listeners: EngineEventListener[] = [];
  private isPaused: boolean = false;
  private isExecutionCancelled: boolean = false;

  private state: EngineState = {
    projectName: 'DevPulse-Generated-Platform',
    totalFiles: 0,
    completedCount: 0,
    failedCount: 0,
    isCompleted: false,
    tasks: [],
    metrics: {
      totalTokensConsumed: 0,
      startTime: Date.now(),
    },
  };

  constructor(config: EngineGlobalConfig) {
    this.config = config;

    // Initialize core services
    this.keyRotator = new ApiKeyRotator(config.keys);
    this.rateLimiter = new RateLimitHandler({
      cooldownMs: config.requestCooldownMs || 1500,
    });

    // Initialize autonomous agents
    this.architectAgent = new ArchitectAgent(this.keyRotator, this.rateLimiter);
    this.coderAgent = new CoderAgent(this.keyRotator, this.rateLimiter);
    this.testerAgent = new TesterAgent(this.keyRotator, this.rateLimiter);

    // Create target directory if it does not exist
    if (!fs.existsSync(this.config.projectRootPath)) {
      fs.mkdirSync(this.config.projectRootPath, { recursive: true });
    }
  }

  /**
   * Subscribe to real-time execution events
   */
  public subscribe(listener: EngineEventListener): void {
    this.listeners.push(listener);
  }

  /**
   * Emit event to all registered listeners
   */
  private emitEvent(event: EngineEvent): void {
    this.listeners.forEach((listener) => {
      try {
        listener(event);
      } catch (err) {
        console.error('Error executing event listener:', err);
      }
    });
  }

  /**
   * Pause the orchestrator execution loop
   */
  public pause(): void {
    this.isPaused = true;
    this.emitEvent({
      type: 'PAUSED',
      message: 'Engine execution paused by user.',
      timestamp: Date.now(),
    });
  }

  /**
   * Resume the orchestrator execution loop
   */
  public resume(): void {
    this.isPaused = false;
    this.emitEvent({
      type: 'RESUMED',
      message: 'Engine execution resumed.',
      timestamp: Date.now(),
    });
  }

  /**
   * Helper to wait if the execution is paused
   */
  private async checkPauseState(): Promise<void> {
    while (this.isPaused) {
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
  }

  /**
   * Main pipeline runner: Architect -> Coder -> Tester -> Disk Persistence
   */
  public async buildEnterprisePlatform(userPrompt: string): Promise<void> {
    this.state.metrics.startTime = Date.now();

    // Step 1: Architect Stage
    this.emitEvent({
      type: 'ARCHITECT_STARTED',
      message: 'Architect Agent is generating project blueprint...',
      timestamp: Date.now(),
    });

    let blueprint: ArchitectBlueprint;
    try {
      blueprint = await this.architectAgent.generateBlueprint(userPrompt);
      this.state.projectName = blueprint.projectName;
      this.state.totalFiles = blueprint.files.length;

      // Populate task queue
      this.state.tasks = blueprint.files.map((file, idx) => ({
        id: `task-${idx + 1}`,
        filePath: file.filePath,
        description: file.description,
        status: 'pending',
        attempts: 0,
      }));

      this.emitEvent({
        type: 'ARCHITECT_COMPLETED',
        message: `Blueprint created for "${blueprint.projectName}" with ${blueprint.files.length} planned files.`,
        payload: { totalFiles: blueprint.files.length },
        timestamp: Date.now(),
      });
    } catch (error: any) {
      this.emitEvent({
        type: 'FILE_ERROR',
        message: `Architect stage failed: ${error?.message || error}`,
        timestamp: Date.now(),
      });
      throw error;
    }

    // Save initial state tracking file
    this.persistStateToDisk();

    // Step 2: Parallel Batch Execution (Coder + Tester)
    const pendingTasks = [...this.state.tasks];
    const workerLimit = this.config.maxParallelWorkers || 3;

    const workerPool = async () => {
      while (pendingTasks.length > 0 && !this.isExecutionCancelled) {
        await this.checkPauseState();

        const task = pendingTasks.shift();
        if (!task) break;

        await this.processSingleTaskPipeline(task, blueprint);
      }
    };

    // Run parallel workers
    const activeWorkers = Array.from({ length: workerLimit }, () => workerPool());
    await Promise.all(activeWorkers);

    // Finalize state
    this.state.isCompleted = true;
    this.state.metrics.endTime = Date.now();
    this.persistStateToDisk();

    this.emitEvent({
      type: 'RESUMED',
      message: `Build finished! Successfully generated ${this.state.completedCount}/${this.state.totalFiles} files with automated tests.`,
      timestamp: Date.now(),
    });
  }

  /**
   * Process a single task through Code Generation and Automated Unit Testing
   */
  private async processSingleTaskPipeline(task: FileTask, blueprint: ArchitectBlueprint): Promise<void> {
    task.status = 'generating';
    task.attempts += 1;
    this.persistStateToDisk();

    try {
      // 1. Code Generation Phase
      const codeResult = await this.coderAgent.generateFileContent({
        projectName: blueprint.projectName,
        filePath: task.filePath,
        fileDescription: task.description,
        techStack: blueprint.techStack,
      });

      // Save source code file
      const fullPath = path.join(this.config.projectRootPath, task.filePath);
      this.saveFileToDisk(fullPath, codeResult.codeContent);

      this.state.metrics.totalTokensConsumed += codeResult.tokensUsed;

      this.emitEvent({
        type: 'FILE_SUCCESS',
        message: `Generated code file: ${task.filePath}`,
        payload: { filePath: task.filePath, tokensUsed: codeResult.tokensUsed },
        timestamp: Date.now(),
      });

      // 2. Unit Testing Phase (Integrated Tester Agent)
      this.emitEvent({
        type: 'TESTER_STARTED',
        message: `Generating unit test for ${task.filePath}...`,
        timestamp: Date.now(),
      });

      const testResult = await this.testerAgent.generateUnitTest({
        filePath: task.filePath,
        codeContent: codeResult.codeContent,
      });

      // Save unit test file
      const testFullPath = path.join(this.config.projectRootPath, testResult.testFilePath);
      this.saveFileToDisk(testFullPath, testResult.testCode);

      this.emitEvent({
        type: 'TESTER_COMPLETED',
        message: `Unit test created at: ${testResult.testFilePath}`,
        timestamp: Date.now(),
      });

      // Mark task as completed
      task.status = 'completed';
      this.state.completedCount += 1;
    } catch (error: any) {
      task.status = 'failed';
      task.errorMessage = error?.message || 'Unknown error occurred';
      this.state.failedCount += 1;

      this.emitEvent({
        type: 'FILE_ERROR',
        message: `Failed processing ${task.filePath}: ${task.errorMessage}`,
        timestamp: Date.now(),
      });
    } finally {
      this.persistStateToDisk();
    }
  }

  /**
   * Write content to filesystem safely
   */
  private saveFileToDisk(filePath: string, content: string): void {
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(filePath, content, 'utf-8');
  }

  /**
   * Persist state to .devpulse_progress.json for CLI/UI status reporting
   */
  private persistStateToDisk(): void {
    const progressPath = path.join(this.config.projectRootPath, '.devpulse_progress.json');
    try {
      fs.writeFileSync(progressPath, JSON.stringify(this.state, null, 2), 'utf-8');
    } catch (err) {
      console.error('Failed to write progress state file:', err);
    }
  }

  /**
   * Get engine state and diagnostic data
   */
  public getDiagnostics() {
    return {
      state: this.state,
      isPaused: this.isPaused,
      activeKeysCount: this.keyRotator.getAvailableKeysCount(),
    };
  }
}
