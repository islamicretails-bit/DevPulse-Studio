'use client';

import React, { useState, useEffect } from 'react';
import { Play, Pause, RefreshCw, Terminal, CheckCircle2, AlertCircle, Cpu, HardDrive } from 'lucide-react';

export default function Dashboard() {
  const [prompt, setPrompt] = useState('');
  const [isBuilding, setIsBuilding] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [progress, setProgress] = useState<any>({
    totalFiles: 0,
    completedCount: 0,
    failedCount: 0,
    metrics: { totalTokensConsumed: 0 },
    tasks: [],
  });

  // Poll state from engine backend
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isBuilding) {
      interval = setInterval(async () => {
        try {
          const res = await fetch('/api/build');
          const data = await res.json();
          if (data.diagnostics?.state) {
            setProgress(data.diagnostics.state);
            setIsPaused(data.diagnostics.isPaused);
            if (data.diagnostics.state.isCompleted) {
              setIsBuilding(false);
            }
          }
        } catch (err) {
          console.error('Error fetching progress state:', err);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isBuilding]);

  const handleStartBuild = async () => {
    if (!prompt) return;
    setIsBuilding(true);
    try {
      await fetch('/api/build', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
    } catch (err) {
      alert('بلڈ شروع کرنے میں ناکامی ہوئی!');
      setIsBuilding(false);
    }
  };

  const handleTogglePause = async () => {
    const action = isPaused ? 'resume' : 'pause';
    await fetch('/api/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    });
    setIsPaused(!isPaused);
  };

  const percentage = progress.totalFiles > 0
    ? Math.round((progress.completedCount / progress.totalFiles) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans" dir="rtl">
      {/* Header */}
      <header className="max-w-7xl mx-auto flex items-center justify-between pb-8 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-600/20 text-indigo-400 rounded-xl border border-indigo-500/30">
            <Cpu className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-wide">DevPulse Studio Pro</h1>
            <p className="text-sm text-slate-400">Enterprise Autonomous Software Engine Dashboard</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className={`px-4 py-1.5 rounded-full text-xs font-semibold flex items-center gap-2 ${
            isBuilding
              ? isPaused ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
              : 'bg-slate-800 text-slate-400'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isBuilding ? isPaused ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400 animate-ping' : 'bg-slate-500'}`} />
            {isBuilding ? (isPaused ? 'پاز شدہ (Paused)' : 'ایکٹیو بلڈ (Generating)') : 'آئڈل (Idle)'}
          </span>
        </div>
      </header>

      {/* Main Grid */}
      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
        
        {/* Left Input & Status Panel */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Terminal className="w-5 h-5 text-indigo-400" />
              پروگرامنگ پرامپٹ درج کریں
            </h2>
            <textarea
              disabled={isBuilding}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="مثال: ایک مکمل ای کامرس پلیٹ فارم بنائیں جس میں Next.js 14، PostgreSQL Prisma، اور Stripe انٹیگریشن شامل ہو..."
              className="w-full h-44 bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition disabled:opacity-50 resize-none"
            />
            
            <div className="flex gap-3 mt-4">
              {!isBuilding ? (
                <button
                  onClick={handleStartBuild}
                  disabled={!prompt}
                  className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white font-medium rounded-xl transition flex items-center justify-center gap-2"
                >
                  <Play className="w-4 h-4 fill-current" />
                  بلڈ جنریشن شروع کریں
                </button>
              ) : (
                <button
                  onClick={handleTogglePause}
                  className={`w-full py-3 font-medium rounded-xl transition flex items-center justify-center gap-2 ${
                    isPaused
                      ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                      : 'bg-amber-600 hover:bg-amber-500 text-white'
                  }`}
                >
                  {isPaused ? <Play className="w-4 h-4 fill-current" /> : <Pause className="w-4 h-4 fill-current" />}
                  {isPaused ? 'دوبارہ شروع کریں (Resume)' : 'کام روکیں (Pause)'}
                </button>
              )}
            </div>
          </div>

          {/* Metrics Card */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl">
            <h3 className="text-sm font-medium text-slate-400 mb-4">انجن میٹرکس (Engine Metrics)</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-950/60 border border-slate-800/80 p-4 rounded-xl">
                <span className="text-xs text-slate-500 block">مکمل فائلیں</span>
                <span className="text-2xl font-bold text-emerald-400">{progress.completedCount} / {progress.totalFiles}</span>
              </div>
              <div className="bg-slate-950/60 border border-slate-800/80 p-4 rounded-xl">
                <span className="text-xs text-slate-500 block">استعمال شدہ ٹوکنز</span>
                <span className="text-2xl font-bold text-indigo-400">{progress.metrics?.totalTokensConsumed?.toLocaleString() || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Execution Monitor */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <HardDrive className="w-5 h-5 text-indigo-400" />
                لائیو جنریشن سٹریمنگ (Live Pipeline)
              </h2>
              <span className="text-sm font-semibold text-indigo-400">{percentage}%</span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden mb-6 border border-slate-800">
              <div
                className="bg-gradient-to-l from-indigo-500 to-emerald-400 h-full transition-all duration-500"
                style={{ width: `${percentage}%` }}
              />
            </div>

            {/* File List Stream */}
            <div className="space-y-3 max-h-[460px] overflow-y-auto pr-2 custom-scrollbar">
              {progress.tasks && progress.tasks.length > 0 ? (
                progress.tasks.map((task: any) => (
                  <div
                    key={task.id}
                    className="flex items-center justify-between p-3.5 bg-slate-950/70 border border-slate-800/60 rounded-xl hover:border-slate-700 transition"
                  >
                    <div className="flex items-center gap-3">
                      {task.status === 'completed' && <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />}
                      {task.status === 'generating' && <RefreshCw className="w-5 h-5 text-indigo-400 animate-spin shrink-0" />}
                      {task.status === 'failed' && <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />}
                      {task.status === 'pending' && <span className="w-2 h-2 rounded-full bg-slate-600 shrink-0 mr-1.5" />}

                      <div>
                        <p className="text-sm font-mono text-slate-200">{task.filePath}</p>
                        <p className="text-xs text-slate-500">{task.description}</p>
                      </div>
                    </div>

                    <span className={`text-xs px-2.5 py-1 rounded-md font-mono ${
                      task.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                      task.status === 'generating' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' :
                      task.status === 'failed' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                      'bg-slate-800 text-slate-400'
                    }`}>
                      {task.status}
                    </span>
                  </div>
                ))
              ) : (
                <div className="text-center py-16 text-slate-500 text-sm">
                  کوئی ایکٹیو بلڈ ٹاسک نہیں ہے۔ پرامپٹ درج کر کے جنریشن شروع کریں۔
                </div>
              )}
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}
