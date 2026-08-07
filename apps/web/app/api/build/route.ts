import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import { BatchOrchestrator, ApiKeyConfig } from '@devpulse/engine';

// Server-side Engine Instance Tracker
let activeOrchestrator: BatchOrchestrator | null = null;

function collectApiKeys(): ApiKeyConfig[] {
  const keys: ApiKeyConfig[] = [];
  let index = 1;

  while (process.env[`GROQ_API_KEY_${index}`] || (index === 1 && process.env.GROQ_API_KEY)) {
    const key = process.env[`GROQ_API_KEY_${index}`] || process.env.GROQ_API_KEY;
    if (key) {
      keys.push({ id: `groq-${index}`, provider: 'groq', key: key.trim(), isRateLimited: false });
    }
    index++;
  }

  index = 1;
  while (process.env[`OPENAI_API_KEY_${index}`] || (index === 1 && process.env.OPENAI_API_KEY)) {
    const key = process.env[`OPENAI_API_KEY_${index}`] || process.env.OPENAI_API_KEY;
    if (key) {
      keys.push({ id: `openai-${index}`, provider: 'openai', key: key.trim(), isRateLimited: false });
    }
    index++;
  }

  return keys;
}

export async function POST(req: NextRequest) {
  try {
    const { prompt, outputPath } = await req.json();

    if (!prompt) {
      return NextResponse.json({ error: 'پرامپٹ فراہم کرنا ضروری ہے۔' }, { status: 400 });
    }

    const keys = collectApiKeys();
    if (keys.length === 0) {
      return NextResponse.json({ error: 'کوئی API Key نہیں ملی۔ .env فائل چیک کریں۔' }, { status: 500 });
    }

    const targetDir = path.resolve(process.cwd(), outputPath || '../../output/gui-project');

    activeOrchestrator = new BatchOrchestrator({
      keys,
      projectRootPath: targetDir,
      maxParallelWorkers: 3,
      requestCooldownMs: 1500,
      autoHealEnabled: true,
      strictNoTruncation: true,
    });

    // Start execution asynchronously
    activeOrchestrator.buildEnterprisePlatform(prompt).catch((err) => {
      console.error('Engine async build error:', err);
    });

    return NextResponse.json({ message: 'بلڈ کا عمل کامیابی سے شروع کر دیا گیا ہے۔', status: 'started' });
  } catch (error: any) {
    return NextResponse.json({ error: error?.message || 'سرور ایرر' }, { status: 500 });
  }
}

export async function GET() {
  if (!activeOrchestrator) {
    return NextResponse.json({ isRunning: false, diagnostics: null });
  }

  return NextResponse.json({
    isRunning: true,
    diagnostics: activeOrchestrator.getDiagnostics(),
  });
}
