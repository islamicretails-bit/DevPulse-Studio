#!/usr/bin/env node
/**
 * DevPulse Studio Pro Engine - Command Line Interface (CLI)
 * Path: packages/cli/src/index.ts
 *
 * Interactive CLI runner for executing full enterprise platform generation,
 * viewing real-time task progress, managing API key configurations, and resuming builds.
 */

import * as fs from 'fs';
import * as path from 'path';
import { Command } from 'commander';
import dotenv from 'dotenv';
import { BatchOrchestrator, ApiKeyConfig, EngineEvent } from '@devpulse/engine';

// Load environment variables from .env file
dotenv.config();

const program = new Command();

program
  .name('devpulse-cli')
  .description('DevPulse Studio Pro - Enterprise Multi-Agent AI Platform Builder')
  .version('1.0.0');

/**
 * Utility to extract API keys from environment variables or local configs
 */
function loadApiKeys(): ApiKeyConfig[] {
  const keys: ApiKeyConfig[] = [];

  // Parse Groq Keys from environment variables
  let index = 1;
  while (process.env[`GROQ_API_KEY_${index}`] || (index === 1 && process.env.GROQ_API_KEY)) {
    const key = process.env[`GROQ_API_KEY_${index}`] || process.env.GROQ_API_KEY;
    if (key) {
      keys.push({
        id: `groq-key-${index}`,
        provider: 'groq',
        key: key.trim(),
        isRateLimited: false,
      });
    }
    index++;
  }

  // Parse OpenAI Keys from environment variables
  index = 1;
  while (process.env[`OPENAI_API_KEY_${index}`] || (index === 1 && process.env.OPENAI_API_KEY)) {
    const key = process.env[`OPENAI_API_KEY_${index}`] || process.env.OPENAI_API_KEY;
    if (key) {
      keys.push({
        id: `openai-key-${index}`,
        provider: 'openai',
        key: key.trim(),
        isRateLimited: false,
      });
    }
    index++;
  }

  return keys;
}

/**
 * Primary 'build' command to initiate software generation
 */
program
  .command('build')
  .description('Build a complete enterprise software architecture from a text prompt')
  .option('-p, --prompt <string>', 'Detailed text description of the platform to generate')
  .option('-f, --file <string>', 'Path to a text/markdown file containing full project requirements')
  .option('-o, --output <string>', 'Root directory where code should be generated', './generated-project')
  .option('-w, --workers <number>', 'Number of parallel worker streams', '3')
  .option('-c, --cooldown <number>', 'Delay between LLM API requests in milliseconds', '1500')
  .action(async (options) => {
    let userPrompt = '';

    if (options.file) {
      const filePath = path.resolve(process.cwd(), options.file);
      if (!fs.existsSync(filePath)) {
        console.error(`❌ Error: Requirements file not found at path: ${filePath}`);
        process.exit(1);
      }
      userPrompt = fs.readFileSync(filePath, 'utf-8');
    } else if (options.prompt) {
      userPrompt = options.prompt;
    } else {
      console.error('❌ Error: You must provide either a --prompt string or a --file path.');
      process.exit(1);
    }

    const apiKeys = loadApiKeys();
    if (apiKeys.length === 0) {
      console.error('❌ Error: No API keys found! Please set GROQ_API_KEY or OPENAI_API_KEY in your environment or .env file.');
      process.exit(1);
    }

    const projectRootPath = path.resolve(process.cwd(), options.output);
    const maxWorkers = parseInt(options.workers, 10) || 3;
    const requestCooldownMs = parseInt(options.cooldown, 10) || 1500;

    console.log(`\n======================================================`);
    console.log(`⚡ DevPulse Studio Pro CLI Engine Started`);
    console.log(`======================================================`);
    console.log(`📁 Target Output Directory: ${projectRootPath}`);
    console.log(`🔑 Loaded API Keys: ${apiKeys.length} (${apiKeys.filter((k) => k.provider === 'groq').length} Groq, ${apiKeys.filter((k) => k.provider === 'openai').length} OpenAI)`);
    console.log(`👷 Parallel Worker Streams: ${maxWorkers}`);
    console.log(`======================================================\n`);

    const orchestrator = new BatchOrchestrator({
      keys: apiKeys,
      projectRootPath,
      maxParallelWorkers: maxWorkers,
      requestCooldownMs,
      autoHealEnabled: true,
      strictNoTruncation: true,
    });

    // Subscribe CLI to engine events for real-time logging
    orchestrator.subscribe((event: EngineEvent) => {
      const time = new Date(event.timestamp).toLocaleTimeString();
      switch (event.type) {
        case 'PAUSED':
          console.warn(`\n⚠️  [${time}] ENGINE PAUSED: ${event.message}`);
          break;
        case 'RESUMED':
          console.log(`\n▶️  [${time}] ENGINE RESUMED: ${event.message}`);
          break;
        case 'KEY_ROTATED':
          console.log(`🔄 [${time}] API KEY ROTATED: ${event.message}`);
          break;
        case 'FILE_SUCCESS':
          console.log(`✅ [${time}] ${event.message}`);
          break;
        case 'FILE_ERROR':
          console.error(`❌ [${time}] ${event.message}`);
          break;
        default:
          break;
      }
    });

    try {
      await orchestrator.buildEnterprisePlatform(userPrompt);
    } catch (error: any) {
      console.error(`\n💥 Fatal Engine Execution Failure:`, error?.message || error);
      process.exit(1);
    }
  });

/**
 * Command to inspect current generation state of a project directory
 */
program
  .command('status')
  .description('Check generation status and progress of an existing project build')
  .option('-o, --output <string>', 'Root directory of the generated project', './generated-project')
  .action((options) => {
    const projectRootPath = path.resolve(process.cwd(), options.output);
    const progressFilePath = path.join(projectRootPath, '.devpulse_progress.json');

    if (!fs.existsSync(progressFilePath)) {
      console.log(`ℹ️  No build progress file found at: ${progressFilePath}`);
      return;
    }

    try {
      const data = JSON.parse(fs.readFileSync(progressFilePath, 'utf-8'));
      console.log(`\n======================================================`);
      console.log(`📊 DevPulse Build Diagnostics: ${data.projectName}`);
      console.log(`======================================================`);
      console.log(`• Status: ${data.isCompleted ? '✅ COMPLETED' : '🔄 IN PROGRESS'}`);
      console.log(`• Total Planned Files: ${data.totalFiles}`);
      console.log(`• Successfully Generated: ${data.completedCount}`);
      console.log(`• Failed Tasks: ${data.failedCount}`);
      console.log(`• Tokens Consumed: ${data.metrics?.totalTokensConsumed || 0}`);
      console.log(`======================================================\n`);
    } catch (error: any) {
      console.error(`❌ Error reading state file:`, error?.message);
    }
  });

program.parse(process.argv);
