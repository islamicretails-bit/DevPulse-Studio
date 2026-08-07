/**
 * DevPulse Studio Pro Engine - Primary Code Generation Agent
 * Path: packages/engine/src/agents/CoderAgent.ts
 *
 * Responsible for writing 100% complete, fully implemented, un-truncated
 * production code for individual files within the enterprise project hierarchy.
 */

import { Groq } from 'groq-sdk';
import OpenAI from 'openai';
import { ApiKeyRotator } from '../services/ApiKeyRotator';
import { RateLimitHandler } from '../services/RateLimitHandler';
import {
  CoderAgentInput,
  CoderAgentResult,
  FileTask,
  ProjectArchitecture,
} from '../types/engine.types';

export class CoderAgent {
  private keyRotator: ApiKeyRotator;
  private rateLimitHandler: RateLimitHandler;

  constructor(keyRotator: ApiKeyRotator, rateLimitHandler: RateLimitHandler) {
    this.keyRotator = keyRotator;
    this.rateLimitHandler = rateLimitHandler;
  }

  /**
   * Constructs strict system prompts ensuring no code truncation or placeholders
   */
  private buildSystemPrompt(input: CoderAgentInput): string {
    const strictRulesList = input.strictRules && input.strictRules.length > 0
      ? input.strictRules.map((rule, idx) => `${idx + 1}. ${rule}`).join('\n')
      : `1. Write 100% full, complete, production-ready source code.
2. ABSOLUTELY NO code truncation, placeholder comments (e.g., '// TODO', '// implement later', '// rest of code'), or abbreviated functions.
3. Include all required imports, TypeScript types, helper functions, and export statements.
4. Ensure full compatibility with Next.js App Router, React, Netlify, and Vercel strict build criteria.
5. Output ONLY raw executable code. Do NOT wrap the code in markdown backticks or natural language headers.`;

    return `You are a Principal Software Architect and Lead Developer.
Your sole mission is to write complete, un-truncated, bug-free, and deployment-ready code for the requested file.

Project Target: ${input.architectureContext.projectName}
Framework: ${input.architectureContext.framework}
Target Deployment Environment: ${input.architectureContext.targetDeployment}

STRICT GENERATION RULES:
${strictRulesList}`;
  }

  /**
   * Constructs user context prompt providing full file and dependency context
   */
  private buildUserPrompt(task: FileTask, architecture: ProjectArchitecture): string {
    return `
Target File Relative Path: ${task.filePath}
Module Classification: ${task.moduleGroup}
File Task Scope & Description: ${task.description}
Internal File Dependencies: ${JSON.stringify(task.dependencies)}

Overall Architecture Overview:
${architecture.architectureOverview}

Write the complete code for '${task.filePath}' now:
`;
  }

  /**
   * Cleans raw LLM response from unwanted markdown formatting or backtick wrappers
   */
  private sanitizeGeneratedCode(rawOutput: string): string {
    if (!rawOutput) return '';

    let cleaned = rawOutput.trim();

    // Strip starting markdown code fences (```typescript, ```javascript, ```tsx, etc.)
    cleaned = cleaned.replace(/^```[a-zA-Z0-9_-]*\n?/, '');

    // Strip ending markdown code fences
    cleaned = cleaned.replace(/\n?```$/, '');

    return cleaned.trim();
  }

  /**
   * Generates code using Groq LLM Provider
   */
  private async generateWithGroq(
    apiKey: string,
    systemPrompt: string,
    userPrompt: string
  ): Promise<{ code: string; tokens: number }> {
    const groq = new Groq({ apiKey });

    const response = await groq.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      temperature: 0.1,
      max_tokens: 8192,
    });

    const code = response.choices[0]?.message?.content || '';
    const tokens = response.usage?.total_tokens || 0;

    return { code, tokens };
  }

  /**
   * Fallback generation using OpenAI Provider
   */
  private async generateWithOpenAI(
    apiKey: string,
    systemPrompt: string,
    userPrompt: string
  ): Promise<{ code: string; tokens: number }> {
    const openai = new OpenAI({ apiKey });

    const response = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      temperature: 0.1,
    });

    const code = response.choices[0]?.message?.content || '';
    const tokens = response.usage?.total_tokens || 0;

    return { code, tokens };
  }

  /**
   * Main execution function for generating file code with multi-provider fallback and retry logic
   */
  public async generateFileCode(input: CoderAgentInput, attempt: number = 0): Promise<CoderAgentResult> {
    // Ensure engine is not currently paused due to rate limits
    await this.rateLimitHandler.waitUntilResumed();

    const startTime = Date.now();
    const systemPrompt = this.buildSystemPrompt(input);
    const userPrompt = this.buildUserPrompt(input.task, input.architectureContext);

    let selectedKeyConfig = this.keyRotator.getNextKey('groq');

    try {
      console.log(`⚡ [CoderAgent] Writing code for file -> '${input.task.filePath}' using key (${selectedKeyConfig.provider})`);

      let rawResult: { code: string; tokens: number };

      if (selectedKeyConfig.provider === 'groq') {
        rawResult = await this.generateWithGroq(selectedKeyConfig.key, systemPrompt, userPrompt);
      } else {
        rawResult = await this.generateWithOpenAI(selectedKeyConfig.key, systemPrompt, userPrompt);
      }

      const sanitizedCode = this.sanitizeGeneratedCode(rawResult.code);
      const executionTimeMs = Date.now() - startTime;

      // Record metrics
      this.keyRotator.recordTokenUsage(selectedKeyConfig.id, rawResult.tokens);

      console.log(`✅ [CoderAgent] Successfully generated '${input.task.filePath}' (${sanitizedCode.split('\n').length} lines, ${executionTimeMs}ms)`);

      return {
        filePath: input.task.filePath,
        rawCode: sanitizedCode,
        tokensUsed: rawResult.tokens,
        providerUsed: selectedKeyConfig.provider,
        executionTimeMs,
      };

    } catch (error: any) {
      console.error(`❌ [CoderAgent] Error generating code for '${input.task.filePath}':`, error?.message || error);

      // Check if this is a Rate Limit error (HTTP 429)
      if (this.rateLimitHandler.isRateLimitError(error)) {
        this.keyRotator.markKeyRateLimited(selectedKeyConfig.id);

        // Engage rate limit pause & wait handler
        await this.rateLimitHandler.handleRateLimit(error, attempt, selectedKeyConfig);

        // Retry generation after rate limit delay
        if (attempt < 5) {
          console.log(`🔄 [CoderAgent] Retrying file generation for '${input.task.filePath}' (Attempt ${attempt + 1})...`);
          return this.generateFileCode(input, attempt + 1);
        }
      }

      // Fallback Strategy: Switch Provider if Groq fails repeatedly
      if (selectedKeyConfig.provider === 'groq') {
        console.warn(`⚠️ [CoderAgent] Switching provider to OpenAI Fallback for file '${input.task.filePath}'...`);
        try {
          const fallbackKey = this.keyRotator.getNextKey('openai');
          const fallbackResult = await this.generateWithOpenAI(fallbackKey.key, systemPrompt, userPrompt);
          const sanitizedCode = this.sanitizeGeneratedCode(fallbackResult.code);
          
          return {
            filePath: input.task.filePath,
            rawCode: sanitizedCode,
            tokensUsed: fallbackResult.tokens,
            providerUsed: 'openai',
            executionTimeMs: Date.now() - startTime,
          };
        } catch (fallbackError: any) {
          console.error(`❌ [CoderAgent] Fallback provider also failed for '${input.task.filePath}':`, fallbackError?.message);
        }
      }

      throw new Error(`Failed to generate code for file '${input.task.filePath}' after retries. Error: ${error?.message}`);
    }
  }
}
