/**
 * DevPulse Studio Pro Engine - Chief Systems Architect Agent
 * Path: packages/engine/src/agents/ArchitectAgent.ts
 *
 * Analyzes enterprise user requirements and constructs a complete, robust, 
 * scalable file hierarchy and dependency blueprint (200-300+ files)
 * optimized for microservices, Next.js App Router, and production deployments.
 */

import { Groq } from 'groq-sdk';
import OpenAI from 'openai';
import { ApiKeyRotator } from '../services/ApiKeyRotator';
import { RateLimitHandler } from '../services/RateLimitHandler';
import {
  ArchitectAgentInput,
  ProjectArchitecture,
} from '../types/engine.types';

export class ArchitectAgent {
  private keyRotator: ApiKeyRotator;
  private rateLimitHandler: RateLimitHandler;

  constructor(keyRotator: ApiKeyRotator, rateLimitHandler: RateLimitHandler) {
    this.keyRotator = keyRotator;
    this.rateLimitHandler = rateLimitHandler;
  }

  /**
   * Constructs strict system architecture instructions for JSON hierarchy generation
   */
  private buildSystemPrompt(): string {
    return `You are the Chief Software Architect for an Enterprise Multi-Agent AI System.
Your task is to analyze user platform specifications and decompose them into a comprehensive, highly scalable, enterprise-grade file structure (handling 200+ distinct files if required).

Architecture Standards:
1. Target Modern Stack: Next.js (App Router), React, TypeScript, Node.js, Prisma ORM, Redis Caching, Docker, and Netlify/Vercel continuous integration.
2. Structure the platform into logical domains:
   - Frontend UI Components (Atoms, Molecules, Organisms, Dashboards)
   - Route Handlers & API Microservices (Auth, Payment, Search, Inventory, AI Pipelines)
   - Core Engine Services, Utilities, and Helpers
   - Database Models, Schema, and Migration Files
   - Configuration & Deployment Manifests (Netlify, Docker, TypeScript, ESLint)
3. Output MUST be valid JSON only matching the exact schema requested. Do NOT wrap output in markdown fences or append text.

JSON Schema format expected:
{
  "projectName": "string",
  "version": "1.0.0",
  "architectureOverview": "string",
  "framework": "Next.js",
  "targetDeployment": "Netlify",
  "totalFilesCount": number,
  "files": [
    {
      "filePath": "relative/path/to/file.ext",
      "description": "Comprehensive explanation of file scope, exports, and implementation requirements",
      "moduleGroup": "ui | api | database | auth | engine | config",
      "dependencies": ["array of relative file paths imported or relied on"],
      "estimatedLines": number,
      "isCriticalPath": boolean
    }
  ]
}`;
  }

  /**
   * Constructs user context prompt based on input requirements
   */
  private buildUserPrompt(input: ArchitectAgentInput): string {
    return `
Enterprise Platform User Prompt:
"${input.userPrompt}"

Preferred Framework: ${input.frameworkPreference || 'Next.js App Router'}
Target Deployment Platform: ${input.targetDeployment || 'Netlify'}

Generate a fully detailed, production-grade JSON Architecture Blueprint for this platform now:
`;
  }

  /**
   * Cleans raw output string ensuring strict JSON parse readiness
   */
  private sanitizeJsonOutput(rawOutput: string): string {
    if (!rawOutput) return '{}';

    let cleaned = rawOutput.trim();

    // Strip leading markdown block delimiters
    cleaned = cleaned.replace(/^```(?:json)?\s*/i, '');

    // Strip trailing markdown block delimiters
    cleaned = cleaned.replace(/\s*```$/, '');

    return cleaned.trim();
  }

  /**
   * Generates architecture blueprint via Groq LLM
   */
  private async generateWithGroq(
    apiKey: string,
    systemPrompt: string,
    userPrompt: string
  ): Promise<ProjectArchitecture> {
    const groq = new Groq({ apiKey });

    const response = await groq.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      response_format: { type: 'json_object' },
      temperature: 0.2,
      max_tokens: 8192,
    });

    const content = response.choices[0]?.message?.content || '{}';
    const sanitized = this.sanitizeJsonOutput(content);
    return JSON.parse(sanitized) as ProjectArchitecture;
  }

  /**
   * Fallback generation via OpenAI LLM
   */
  private async generateWithOpenAI(
    apiKey: string,
    systemPrompt: string,
    userPrompt: string
  ): Promise<ProjectArchitecture> {
    const openai = new OpenAI({ apiKey });

    const response = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      response_format: { type: 'json_object' },
      temperature: 0.2,
    });

    const content = response.choices[0]?.message?.content || '{}';
    const sanitized = this.sanitizeJsonOutput(content);
    return JSON.parse(sanitized) as ProjectArchitecture;
  }

  /**
   * Main entry method to build the project architecture with rate limit handling and fallbacks
   */
  public async createProjectBlueprint(
    input: ArchitectAgentInput,
    attempt: number = 0
  ): Promise<ProjectArchitecture> {
    await this.rateLimitHandler.waitUntilResumed();

    const systemPrompt = this.buildSystemPrompt();
    const userPrompt = this.buildUserPrompt(input);
    const keyConfig = this.keyRotator.getNextKey('groq');

    try {
      console.log(`🧠 [ArchitectAgent] Decomposing requirements into full project blueprint using (${keyConfig.provider})...`);

      let architecture: ProjectArchitecture;

      if (keyConfig.provider === 'groq') {
        architecture = await this.generateWithGroq(keyConfig.key, systemPrompt, userPrompt);
      } else {
        architecture = await this.generateWithOpenAI(keyConfig.key, systemPrompt, userPrompt);
      }

      // Ensure totalFilesCount is accurately calculated
      architecture.totalFilesCount = architecture.files ? architecture.files.length : 0;

      console.log(`✅ [ArchitectAgent] Architecture blueprint created successfully! Total files planned: ${architecture.totalFilesCount}`);

      return architecture;

    } catch (error: any) {
      console.error(`❌ [ArchitectAgent] Blueprint generation error:`, error?.message || error);

      // Handle HTTP 429 Rate Limits
      if (this.rateLimitHandler.isRateLimitError(error)) {
        this.keyRotator.markKeyRateLimited(keyConfig.id);
        await this.rateLimitHandler.handleRateLimit(error, attempt, keyConfig);

        if (attempt < 5) {
          console.log(`🔄 [ArchitectAgent] Retrying blueprint generation (Attempt ${attempt + 1})...`);
          return this.createProjectBlueprint(input, attempt + 1);
        }
      }

      // Fallback Provider
      if (keyConfig.provider === 'groq') {
        console.warn(`⚠️ [ArchitectAgent] Switching to OpenAI Fallback for ArchitectAgent...`);
        try {
          const fallbackKey = this.keyRotator.getNextKey('openai');
          const fallbackArchitecture = await this.generateWithOpenAI(
            fallbackKey.key,
            systemPrompt,
            userPrompt
          );
          fallbackArchitecture.totalFilesCount = fallbackArchitecture.files ? fallbackArchitecture.files.length : 0;
          return fallbackArchitecture;
        } catch (fallbackError: any) {
          console.error(`❌ [ArchitectAgent] OpenAI Fallback also failed:`, fallbackError?.message);
        }
      }

      throw new Error(`Failed to generate Project Architecture Blueprint. Error: ${error?.message}`);
    }
  }
}
