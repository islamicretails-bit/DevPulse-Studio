/**
 * DevPulse Studio Pro Engine - Programmatic Integration Example
 * Path: examples/build-platform.ts
 *
 * Demonstrates how to instantiate and run the BatchOrchestrator programmatically
 * from any Node.js/TypeScript application with live event listeners.
 */

import * as path from 'path';
import dotenv from 'dotenv';
import {
  BatchOrchestrator,
  ApiKeyConfig,
  EngineEvent,
} from '@devpulse/engine';

// Load environment variables from .env
dotenv.config();

/**
 * Helper to collect API Keys from environment variables
 */
function getApiKeysFromEnv(): ApiKeyConfig[] {
  const keys: ApiKeyConfig[] = [];

  // Load Groq Keys
  let i = 1;
  while (process.env[`GROQ_API_KEY_${i}`] || (i === 1 && process.env.GROQ_API_KEY)) {
    const key = process.env[`GROQ_API_KEY_${i}`] || process.env.GROQ_API_KEY;
    if (key) {
      keys.push({
        id: `groq-key-${i}`,
        provider: 'groq',
        key: key.trim(),
        isRateLimited: false,
      });
    }
    i++;
  }

  // Load OpenAI Fallback Keys
  i = 1;
  while (process.env[`OPENAI_API_KEY_${i}`] || (i === 1 && process.env.OPENAI_API_KEY)) {
    const key = process.env[`OPENAI_API_KEY_${i}`] || process.env.OPENAI_API_KEY;
    if (key) {
      keys.push({
        id: `openai-key-${i}`,
        provider: 'openai',
        key: key.trim(),
        isRateLimited: false,
      });
    }
    i++;
  }

  return keys;
}

async function runProgrammaticBuild() {
  console.log(`\n======================================================`);
  console.log(`🚀 Starting Programmatic Build Execution Example`);
  console.log(`======================================================\n`);

  // 1. Gather API Keys
  const keys = getApiKeysFromEnv();
  if (keys.length === 0) {
    console.error(`❌ Error: No API keys configured in .env file!`);
    process.exit(1);
  }

  // 2. Specify Output Path & Requirements
  const targetOutputFolder = path.resolve(__dirname, '../output/mystorium-store');

  const promptRequirements = `
Build a full-stack Enterprise E-Commerce & Inventory Management Platform named "Mystorium Store".
Include:
1. Next.js 14 App Router for modern frontend UI (Storefront, Product Catalog, Cart, Checkout).
2. Admin Dashboard with Analytics Charts, Order Tracking, and Real-time Inventory Management.
3. PostgreSQL Prisma ORM Schema for Users, Products, Orders, Inventories, and Transactions.
4. Microservices API Route Handlers for Auth (JWT/NextAuth), Payment processing (Stripe integration), and Search filtering.
5. Docker compose and Netlify configuration files for instant production setup.
`;

  // 3. Initialize the Batch Orchestrator
  const orchestrator = new BatchOrchestrator({
    keys,
    projectRootPath: targetOutputFolder,
    maxParallelWorkers: 3,
    requestCooldownMs: 1200,
    autoHealEnabled: true,
    strictNoTruncation: true,
  });

  // 4. Attach Live Event Listeners for Dashboard / Real-Time Logging
  orchestrator.subscribe((event: EngineEvent) => {
    const timestamp = new Date(event.timestamp).toLocaleTimeString();

    switch (event.type) {
      case 'ARCHITECT_STARTED':
        console.log(`🧠 [${timestamp}] Architect Agent creating full architecture blueprint...`);
        break;

      case 'ARCHITECT_COMPLETED':
        console.log(`✅ [${timestamp}] Architecture blueprint complete! Total planned files: ${event.payload?.totalFiles}`);
        break;

      case 'FILE_SUCCESS':
        console.log(`📝 [${timestamp}] [SUCCESS] Generated: ${event.payload?.filePath} (${event.payload?.tokensUsed} tokens)`);
        break;

      case 'FILE_ERROR':
        console.error(`❌ [${timestamp}] [ERROR] Failed to generate: ${event.payload?.filePath} - ${event.payload?.error}`);
        break;

      case 'PAUSED':
        console.warn(`⏸️ [${timestamp}] [PAUSED] Orchestrator paused: ${event.message}`);
        break;

      case 'RESUMED':
        console.log(`▶️ [${timestamp}] [RESUMED] Orchestrator resumed execution.`);
        break;

      case 'KEY_ROTATED':
        console.log(`🔄 [${timestamp}] [KEY ROTATION] Switched API Key: ${event.message}`);
        break;

      default:
        console.log(`ℹ️ [${timestamp}] [EVENT: ${event.type}] ${event.message}`);
        break;
    }
  });

  // 5. Execute Build Pipeline
  try {
    console.log(`⚙️ Invoking buildEnterprisePlatform()...\n`);
    await orchestrator.buildEnterprisePlatform(promptRequirements);

    // 6. Fetch Final Build Diagnostics
    const diagnostics = orchestrator.getDiagnostics();
    console.log(`\n======================================================`);
    console.log(`🎉 Build Finished Successfully!`);
    console.log(`📊 Completed Files: ${diagnostics.state.completedCount}/${diagnostics.state.totalFiles}`);
    console.log(`📊 Total Consumed Tokens: ${diagnostics.state.metrics.totalTokensConsumed}`);
    console.log(`======================================================\n`);

  } catch (error: any) {
    console.error(`\n💥 Build process encountered a fatal error:`, error?.message || error);
  }
}

// Execute the example script
runProgrammaticBuild();
