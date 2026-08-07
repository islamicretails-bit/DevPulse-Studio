/**
 * DevPulse Studio Pro Engine - Rate Limit & Pause/Resume Handler
 * Path: packages/engine/src/services/RateLimitHandler.ts
 *
 * This service monitors API rate limits (HTTP 429), handles exponential backoff,
 * pauses background batch processing safely, and triggers automatic resumption.
 */

import { ApiKeyConfig, EngineEvent, EngineEventListener } from '../types/engine.types';

export interface RateLimitOptions {
  baseDelayMs: number;       // Default wait time when limit is hit (e.g., 60,000ms = 1 min)
  maxDelayMs: number;        // Maximum wait ceiling (e.g., 300,000ms = 5 mins)
  maxRetries: number;        // Max retry attempts per file task
  backoffFactor: number;     // Exponential multiplier (e.g., 2x)
}

export class RateLimitHandler {
  private options: RateLimitOptions;
  private listeners: EngineEventListener[] = [];
  private isPaused: boolean = false;
  private pausePromise: Promise<void> | null = null;
  private pauseResolver: (() => void) | null = null;

  constructor(options?: Partial<RateLimitOptions>) {
    this.options = {
      baseDelayMs: options?.baseDelayMs ?? 60000,   // Default 1 minute
      maxDelayMs: options?.maxDelayMs ?? 300000,    // Max 5 minutes
      maxRetries: options?.maxRetries ?? 10,
      backoffFactor: options?.backoffFactor ?? 2,
    };
  }

  /**
   * Register Event Listeners for UI notification
   */
  public subscribe(listener: EngineEventListener): void {
    this.listeners.push(listener);
  }

  private emitEvent(event: EngineEvent): void {
    this.listeners.forEach((listener) => listener(event));
  }

  /**
   * Helper utility to wait for specified milliseconds
   */
  public delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Inspects thrown error to check if it's a Rate Limit / Too Many Requests error
   */
  public isRateLimitError(error: any): boolean {
    if (!error) return false;

    const statusCode = error?.status || error?.statusCode || error?.response?.status;
    const errorMessage = (error?.message || error?.toString() || '').toLowerCase();

    // Check status 429 or explicit rate limit keywords
    if (statusCode === 429) return true;
    if (errorMessage.includes('rate_limit') || errorMessage.includes('rate limit')) return true;
    if (errorMessage.includes('too many requests')) return true;
    if (errorMessage.includes('tokens per minute') || errorMessage.includes('tpm')) return true;
    if (errorMessage.includes('requests per minute') || errorMessage.includes('rpm')) return true;

    return false;
  }

  /**
   * Calculates exponential delay based on attempt number
   */
  public calculateBackoffDelay(attempt: number): number {
    const delay = this.options.baseDelayMs * Math.pow(this.options.backoffFactor, attempt);
    return Math.min(delay, this.options.maxDelayMs);
  }

  /**
   * Called when a Rate Limit error is detected. Pauses execution and waits before auto-resuming.
   */
  public async handleRateLimit(error: any, attempt: number, apiKeyConfig?: ApiKeyConfig): Promise<void> {
    const waitTimeMs = this.calculateBackoffDelay(attempt);
    const waitTimeSec = Math.ceil(waitTimeMs / 1000);

    console.warn(`\n⚠️ [RateLimitHandler] API Limit Triggered on Provider: ${apiKeyConfig?.provider || 'Unknown'}`);
    console.warn(`⏳ [RateLimitHandler] Auto-pausing execution for ${waitTimeSec} seconds... (Attempt ${attempt + 1}/${this.options.maxRetries})\n`);

    // Mark key as rate limited if key object provided
    if (apiKeyConfig) {
      apiKeyConfig.rateLimitedUntil = Date.now() + waitTimeMs;
      apiKeyConfig.isActive = false;
    }

    this.emitEvent({
      type: 'RATE_LIMIT_HIT',
      timestamp: Date.now(),
      message: `API Rate Limit reached. Engine auto-pausing for ${waitTimeSec} seconds.`,
      payload: { waitTimeMs, attempt, provider: apiKeyConfig?.provider },
    });

    // Pause worker loops
    this.pauseExecution(`Rate limit reached on ${apiKeyConfig?.provider || 'API'}`);

    // Wait for backoff duration
    await this.delay(waitTimeMs);

    // Re-enable key
    if (apiKeyConfig) {
      apiKeyConfig.isActive = true;
      apiKeyConfig.rateLimitedUntil = undefined;
    }

    // Auto-resume worker loops
    this.resumeExecution();
  }

  /**
   * Manually or programmatically pause all active background processing
   */
  public pauseExecution(reason: string = 'User requested pause'): void {
    if (this.isPaused) return;

    this.isPaused = true;
    this.pausePromise = new Promise((resolve) => {
      this.pauseResolver = resolve;
    });

    console.log(`⏸️ [RateLimitHandler] Engine execution PAUSED. Reason: ${reason}`);

    this.emitEvent({
      type: 'AUTO_PAUSE',
      timestamp: Date.now(),
      message: `Engine paused: ${reason}`,
      payload: { reason },
    });
  }

  /**
   * Resume paused background processing
   */
  public resumeExecution(): void {
    if (!this.isPaused) return;

    this.isPaused = false;
    if (this.pauseResolver) {
      this.pauseResolver();
      this.pauseResolver = null;
      this.pausePromise = null;
    }

    console.log(`▶️ [RateLimitHandler] Engine execution RESUMED.`);

    this.emitEvent({
      type: 'AUTO_RESUME',
      timestamp: Date.now(),
      message: 'Engine successfully resumed execution.',
    });
  }

  /**
   * Workers call this method before processing each task.
   * If engine is paused, this halts execution safely until resumed.
   */
  public async waitUntilResumed(): Promise<void> {
    if (this.isPaused && this.pausePromise) {
      console.log(`💤 [Worker] Waiting for rate-limit cooldown / pause resolver...`);
      await this.pausePromise;
    }
  }

  /**
   * Check if engine is currently in a paused state
   */
  public getIsPaused(): boolean {
    return this.isPaused;
  }
}
