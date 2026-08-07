/**
 * DevPulse Studio Pro Engine - Local State Persistence & Auto-Resume Tracker
 * Path: packages/engine/src/services/StateTracker.ts
 *
 * Persists project build progress to local JSON storage on disk.
 * Enables zero-data-loss resume capability after crashes, system restarts,
 * or rate-limit pauses across 200-300+ file code generation tasks.
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  FileTask,
  ProgressState,
  ProjectArchitecture,
  TaskStatus,
  EngineEvent,
  EngineEventListener,
} from '../types/engine.types';

export class StateTracker {
  private progressFilePath: string;
  private projectRootPath: string;
  private state: ProgressState;
  private listeners: EngineEventListener[] = [];

  constructor(projectRootPath: string, progressFileName: string = '.devpulse_progress.json') {
    this.projectRootPath = projectRootPath;
    this.progressFilePath = path.join(projectRootPath, progressFileName);

    // Initialize default state
    this.state = {
      projectId: `proj_${Date.now()}`,
      projectName: 'NexusVault-Platform',
      projectRootPath,
      currentPhase: 'architecting',
      totalFiles: 0,
      completedCount: 0,
      failedCount: 0,
      isPaused: false,
      tasks: [],
      metrics: {
        startTime: Date.now(),
        totalTokensConsumed: 0,
        totalRateLimitsEncountered: 0,
        successfulFilesCount: 0,
        failedFilesCount: 0,
      },
      lastUpdated: Date.now(),
    };
  }

  /**
   * Subscribe listener for UI state broadcast
   */
  public subscribe(listener: EngineEventListener): void {
    this.listeners.push(listener);
  }

  private emitEvent(type: any, message: string, payload?: any): void {
    const event: EngineEvent = {
      type,
      timestamp: Date.now(),
      message,
      payload,
    };
    this.listeners.forEach((listener) => listener(event));
  }

  /**
   * Loads existing progress file from disk or initializes a new one based on Architecture Blueprint
   */
  public initializeFromArchitecture(architecture: ProjectArchitecture): ProgressState {
    // Ensure target folder exists
    if (!fs.existsSync(this.projectRootPath)) {
      fs.mkdirSync(this.projectRootPath, { recursive: true });
    }

    // Check if progress file already exists for Auto-Resume
    if (fs.existsSync(this.progressFilePath)) {
      try {
        const rawData = fs.readFileSync(this.progressFilePath, 'utf-8');
        const loadedState = JSON.parse(rawData) as ProgressState;

        console.log(`\n📂 [StateTracker] Found existing progress file! Restoring session for project: '${loadedState.projectName}'`);
        console.log(`📊 [StateTracker] Resuming state: ${loadedState.completedCount}/${loadedState.totalFiles} files completed.\n`);

        this.state = loadedState;
        return this.state;
      } catch (err) {
        console.warn(`⚠️ [StateTracker] Corrupt progress file detected. Re-initializing fresh state.`);
      }
    }

    // Transform architecture file blueprints into executable tasks
    const tasks: FileTask[] = architecture.files.map((file, index) => ({
      id: `task_${index + 1}_${file.filePath.replace(/[^a-zA-Z0-9]/g, '_')}`,
      filePath: file.filePath,
      description: file.description,
      moduleGroup: file.moduleGroup,
      dependencies: file.dependencies,
      status: 'pending',
      attempts: 0,
      createdAt: Date.now(),
    }));

    this.state = {
      projectId: `proj_${Date.now()}`,
      projectName: architecture.projectName,
      projectRootPath: this.projectRootPath,
      currentPhase: 'generating',
      totalFiles: tasks.length,
      completedCount: 0,
      failedCount: 0,
      isPaused: false,
      tasks,
      metrics: {
        startTime: Date.now(),
        totalTokensConsumed: 0,
        totalRateLimitsEncountered: 0,
        successfulFilesCount: 0,
        failedFilesCount: 0,
      },
      lastUpdated: Date.now(),
    };

    this.saveToDisk();
    return this.state;
  }

  /**
   * Synchronously persists current state snapshot to disk
   */
  public saveToDisk(): void {
    try {
      this.state.lastUpdated = Date.now();
      const tempPath = `${this.progressFilePath}.tmp`;
      
      // Atomic write to avoid partial file corruptions on unexpected shutdown
      fs.writeFileSync(tempPath, JSON.stringify(this.state, null, 2), 'utf-8');
      fs.renameSync(tempPath, this.progressFilePath);
    } catch (error) {
      console.error(`❌ [StateTracker] Failed to write progress state to disk:`, error);
    }
  }

  /**
   * Updates task status and recalculates system counters
   */
  public updateTaskStatus(
    taskId: string,
    status: TaskStatus,
    generatedCode?: string,
    errorMessage?: string,
    tokensUsed: number = 0
  ): void {
    const task = this.state.tasks.find((t) => t.id === taskId || t.filePath === taskId);
    if (!task) {
      console.warn(`⚠️ [StateTracker] Task not found for update: ${taskId}`);
      return;
    }

    const previousStatus = task.status;
    task.status = status;
    task.attempts += 1;

    if (generatedCode) {
      task.generatedCode = generatedCode;
    }

    if (errorMessage) {
      task.lastErrorMessage = errorMessage;
    }

    if (status === 'completed') {
      task.completedAt = Date.now();
      if (previousStatus !== 'completed') {
        this.state.completedCount += 1;
        this.state.metrics.successfulFilesCount += 1;
      }
    } else if (status === 'failed') {
      if (previousStatus !== 'failed') {
        this.state.failedCount += 1;
        this.state.metrics.failedFilesCount += 1;
      }
    }

    if (tokensUsed > 0) {
      this.state.metrics.totalTokensConsumed += tokensUsed;
    }

    this.saveToDisk();

    this.emitEvent('PROGRESS_UPDATE', `Updated ${task.filePath} status to ${status}`, {
      filePath: task.filePath,
      status,
      completedCount: this.state.completedCount,
      totalFiles: this.state.totalFiles,
    });
  }

  /**
   * Returns list of pending tasks requiring code generation
   */
  public getPendingTasks(): FileTask[] {
    return this.state.tasks.filter((t) => t.status === 'pending' || t.status === 'failed');
  }

  /**
   * Marks phase as completed and optionally cleans up local tracker
   */
  public markProjectCompleted(): void {
    this.state.currentPhase = 'completed';
    this.state.metrics.endTime = Date.now();
    this.saveToDisk();

    console.log(`\n🎉 [StateTracker] All ${this.state.totalFiles} files generated and saved successfully!`);
  }

  /**
   * Returns current active snapshot
   */
  public getState(): ProgressState {
    return this.state;
  }
}
