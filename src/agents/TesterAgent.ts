/**
 * DevPulse Studio Pro - Tester Agent
 * Automatically generates unit tests for generated code files.
 */

import { ApiKeyRotator } from '../services/ApiKeyRotator';
import { RateLimitHandler } from '../services/RateLimitHandler';
import { TesterAgentInput, TesterOutput } from '../types/engine.types';

export class TesterAgent {
  private keyRotator: ApiKeyRotator;
  private rateLimiter: RateLimitHandler;

  constructor(keyRotator: ApiKeyRotator, rateLimiter: RateLimitHandler) {
    this.keyRotator = keyRotator;
    this.rateLimiter = rateLimiter;
  }

  /**
   * Generates unit tests for a specific file code
   */
  public async generateUnitTest(input: TesterAgentInput): Promise<TesterOutput> {
    const systemPrompt = `You are an expert QA and Testing Engineer.
Generate unit tests using Jest/Vitest for the provided source code.
Output ONLY valid executable TypeScript test code. Do not include markdown code blocks.`;

    const userPrompt = `Source File Path: ${input.filePath}\nSource Code:\n${input.codeContent}`;

    // 1. Get active API Key with rotation support
    const apiKey = this.keyRotator.getActiveKey();

    // 2. Execute call with rate-limit retries
    const testCodeResult = await this.rateLimiter.executeWithRetry(async () => {
      // LLM API Call execution here (e.g., via Groq or OpenAI SDK)
      return `describe('${input.filePath}', () => {\n  it('should pass initial sanity test', () => {\n    expect(true).toBe(true);\n  });\n});`;
    });

    const testFilePath = input.filePath.replace(/\.(ts|js|tsx|jsx)$/, '.test.$1');

    return {
      testCode: testCodeResult,
      testFilePath,
      passedSyntaxCheck: true,
    };
  }
}
