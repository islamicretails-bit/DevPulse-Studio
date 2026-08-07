/**
 * DevPulse Studio Pro Engine - Multi-API Key Load Balancer & Rotator
 * Path: packages/engine/src/services/ApiKeyRotator.ts
 *
 * Manages an active pool of API keys across multiple providers (Groq, OpenAI, Anthropic).
 * Rotates keys in round-robin fashion, monitors token usage, auto-disables rate-limited keys,
 * and seamlessly switches to available backups.
 */

import { ApiKeyConfig, SupportedProvider } from '../types/engine.types';

export class ApiKeyRotator {
  private keys: ApiKeyConfig[] = [];
  private currentPointer: Map<SupportedProvider | 'global', number> = new Map();

  constructor(initialKeys: ApiKeyConfig[]) {
    if (!initialKeys || initialKeys.length === 0) {
      throw new Error('ApiKeyRotator requires at least one valid API Key configuration.');
    }
    this.keys = initialKeys.map((k) => ({
      ...k,
      requestCount: k.requestCount ?? 0,
      totalTokensUsed: k.totalTokensUsed ?? 0,
      isActive: k.isActive ?? true,
    }));

    this.currentPointer.set('global', 0);
    this.currentPointer.set('groq', 0);
    this.currentPointer.set('openai', 0);
    this.currentPointer.set('anthropic', 0);
  }

  /**
   * Adds a new API key to the active rotation pool at runtime
   */
  public addKey(keyConfig: ApiKeyConfig): void {
    const exists = this.keys.some((k) => k.id === keyConfig.id || k.key === keyConfig.key);
    if (!exists) {
      this.keys.push({
        ...keyConfig,
        requestCount: 0,
        totalTokensUsed: 0,
        isActive: true,
      });
      console.log(`🔑 [ApiKeyRotator] New API Key added successfully for provider: ${keyConfig.provider}`);
    }
  }

  /**
   * Checks and clears expired rate-limit lockouts
   */
  private refreshKeyStatus(): void {
    const now = Date.now();
    for (const key of this.keys) {
      if (key.rateLimitedUntil && now >= key.rateLimitedUntil) {
        key.rateLimitedUntil = undefined;
        key.isActive = true;
        console.log(`🔓 [ApiKeyRotator] Rate limit expired. Re-activating key ID: ${key.id} (${key.provider})`);
      }
    }
  }

  /**
   * Retrieves the next active API Key for a specified provider (or any provider if un-specified)
   */
  public getNextKey(preferredProvider?: SupportedProvider): ApiKeyConfig {
    this.refreshKeyStatus();

    const candidateKeys = preferredProvider
      ? this.keys.filter((k) => k.provider === preferredProvider && k.isActive)
      : this.keys.filter((k) => k.isActive);

    if (candidateKeys.length === 0) {
      // Fallback: If requested provider keys are all limited, pick any active key from other providers
      const fallbackKeys = this.keys.filter((k) => k.isActive);
      if (fallbackKeys.length === 0) {
        throw new Error(
          `❌ [ApiKeyRotator] Exhausted all API Keys! All ${this.keys.length} keys are currently rate-limited or inactive.`
        );
      }

      console.warn(
        `⚠️ [ApiKeyRotator] No active key for '${preferredProvider}'. Falling back to available provider: '${fallbackKeys[0].provider}'`
      );
      return this.selectAndIncrement(fallbackKeys, preferredProvider || 'global');
    }

    return this.selectAndIncrement(candidateKeys, preferredProvider || 'global');
  }

  /**
   * Performs pointer increment and selection logic
   */
  private selectAndIncrement(pool: ApiKeyConfig[], pointerKey: SupportedProvider | 'global'): ApiKeyConfig {
    const currentIndex = this.currentPointer.get(pointerKey) || 0;
    const selectedKey = pool[currentIndex % pool.length];

    // Advance pointer for load balancing
    this.currentPointer.set(pointerKey, (currentIndex + 1) % pool.length);

    selectedKey.requestCount += 1;
    return selectedKey;
  }

  /**
   * Temporarily disables a key when an error or rate limit occurs
   */
  public markKeyRateLimited(keyId: string, cooldownMs: number = 60000): void {
    const key = this.keys.find((k) => k.id === keyId);
    if (key) {
      key.isActive = false;
      key.rateLimitedUntil = Date.now() + cooldownMs;
      console.warn(
        `⚠️ [ApiKeyRotator] Key ID '${key.id}' (${key.provider}) flagged as Rate Limited. Cooldown: ${Math.ceil(cooldownMs / 1000)}s`
      );
    }
  }

  /**
   * Records token consumption metrics for cost and limit tracking
   */
  public recordTokenUsage(keyId: string, tokensUsed: number): void {
    const key = this.keys.find((k) => k.id === keyId);
    if (key) {
      key.totalTokensUsed += tokensUsed;
    }
  }

  /**
   * Returns complete health & usage metrics for all managed keys
   */
  public getPoolStatus(): {
    totalKeys: number;
    activeKeysCount: number;
    rateLimitedKeysCount: number;
    stats: Array<{ id: string; provider: SupportedProvider; requests: number; tokens: number; active: boolean }>;
  } {
    this.refreshKeyStatus();
    const active = this.keys.filter((k) => k.isActive).length;
    const limited = this.keys.length - active;

    return {
      totalKeys: this.keys.length,
      activeKeysCount: active,
      rateLimitedKeysCount: limited,
      stats: this.keys.map((k) => ({
        id: k.id,
        provider: k.provider,
        requests: k.requestCount,
        tokens: k.totalTokensUsed,
        active: k.isActive,
      })),
    };
  }
}
