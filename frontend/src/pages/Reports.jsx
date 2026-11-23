import React, { useState, useEffect } from 'react';
import {
  FileBarChart,
  Download,
  Printer,
  CheckCircle2,
  XCircle,
  Sparkles,
  Zap,
  Globe,
  Clock,
  Layers,
  AlertTriangle,
  Bot,
  ShieldCheck,
  Check
} from 'lucide-react';
import { api } from '../services/api';

export default function Reports({ activeRunId }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeRunId) return;
    setLoading(true);
    api.getRunReport(activeRunId)
      .then((data) => setReport(data?.summary || null))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [activeRunId]);

  const handleDownloadHTML = () => {
    if (!activeRunId) return;
    window.open(api.getHtmlReportUrl(activeRunId), '_blank');
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-surface-400 text-xs font-mono">
        Generating consolidated report view...
      </div>
    );
  }

  if (!report) {
    return (
      <div className="p-6 md:p-8 max-w-7xl mx-auto">
        <div className="py-20 text-center bg-white border border-surface-200 rounded-xl text-surface-400 text-xs shadow-2xs">
          No audit report generated for this run yet. Run must complete Stage 6.
        </div>
      </div>
    );
  }

  const metrics = report.metrics || {};
  const provider = report.ai_provider || report.generation_mode || 'basic';
  const isGemini = provider === 'gemini';
  const isAi = provider === 'openai' || provider === 'ai';
  const isBasic = !isGemini && !isAi;
  const modelName = report.ai_model;

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header and Download Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-200">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Consolidated QA Report</h1>
            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase border ${
              isGemini
                ? 'bg-blue-50 text-blue-800 border-blue-200'
                : isAi
                ? 'bg-purple-50 text-purple-800 border-purple-200'
                : 'bg-amber-50 text-amber-800 border-amber-200'
            }`}>
              {isGemini ? (
                <>
                  <Sparkles className="w-2.5 h-2.5 text-blue-600" />
                  <span>GEMINI{modelName ? ` — ${modelName}` : ''}</span>
                </>
              ) : isAi ? (
                <>
                  <Bot className="w-2.5 h-2.5 text-purple-600" />
                  <span>OPENAI{modelName ? ` — ${modelName}` : ''}</span>
                </>
              ) : (
                <>
                  <Zap className="w-2.5 h-2.5 text-amber-600" />
                  <span>BASIC MODE</span>
                </>
              )}
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase bg-blue-50 text-blue-700 border border-blue-200">
              {report.automation_framework?.toUpperCase() || 'PLAYWRIGHT'}
            </span>
          </div>
          <p className="text-xs text-surface-500 mt-1">
            Synthesized by Agent 6 (Report Generation Agent) from actual execution results with actionable recommendations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleDownloadHTML}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download HTML Report</span>
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-surface-200 hover:bg-surface-50 text-surface-700 font-semibold text-xs shadow-2xs transition-colors"
          >
            <Printer className="w-3.5 h-3.5 text-surface-500" />
            <span>Print / PDF</span>
          </button>
        </div>
      </div>

      {/* Mode Fallback / Transition Banner if applicable */}
      {report.mode_fallback_reason && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-3 shadow-2xs">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
          <div>
            <span className="font-bold block text-amber-950">Mode Reason</span>
            <span className="text-[11px] text-amber-800 leading-relaxed">
              {report.mode_fallback_reason} All six agents engaged in Basic Testing Mode using deterministic page inspection.
            </span>
          </div>
        </div>
      )}

      {/* KPI Cards Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs">
          <div className="text-[10px] uppercase font-mono text-surface-500 font-bold">Total Test Cases</div>
          <div className="text-3xl font-extrabold text-surface-900 mt-1">{metrics.total_tests || 0}</div>
        </div>
        <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs">
          <div className="text-[10px] uppercase font-mono text-emerald-600 font-bold">Passed Tests</div>
          <div className="text-3xl font-extrabold text-emerald-600 mt-1">{metrics.passed_tests || 0}</div>
        </div>
        <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs">
          <div className="text-[10px] uppercase font-mono text-rose-600 font-bold">Failed Tests</div>
          <div className="text-3xl font-extrabold text-rose-600 mt-1">{metrics.failed_tests || 0}</div>
        </div>
        <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs">
          <div className="text-[10px] uppercase font-mono text-blue-600 font-bold">Overall Pass Rate</div>
          <div className="text-3xl font-extrabold text-blue-600 mt-1">{metrics.pass_percentage || 0}%</div>
        </div>
      </div>

      {/* Executive Summary Card */}
      <div className="bg-white border border-surface-200 rounded-xl p-6 space-y-4 shadow-2xs">
        <div className="flex items-center gap-2 text-surface-900 font-bold text-base">
          <Sparkles className="w-5 h-5 text-blue-600" />
          <h2>Executive Summary</h2>
        </div>
        <p className="text-sm text-surface-700 leading-relaxed bg-surface-50 p-4 rounded-xl border border-surface-200/80">
          {report.summary}
        </p>

        {/* Testing Insights & Recommendations */}
        <div className="pt-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-surface-500 font-mono mb-2.5">
            Testing Insights &amp; Next Steps
          </h3>
          <ul className="space-y-2">
            {(report.recommendations || []).map((rec, i) => (
              <li key={i} className="flex items-start gap-2.5 text-xs text-surface-700 bg-surface-50 p-3.5 rounded-lg border border-surface-200/80">
                <span className="w-5 h-5 rounded-md bg-blue-100 text-blue-700 font-mono text-[10px] flex items-center justify-center shrink-0 font-bold">
                  {i + 1}
                </span>
                <span className="mt-0.5 leading-relaxed">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Target & Metadata Card */}
      <div className="bg-white border border-surface-200 rounded-xl p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs shadow-2xs">
        <div className="p-3 rounded-lg bg-surface-50 border border-surface-200/70">
          <div className="text-surface-500 font-mono text-[10px] uppercase font-bold">Target Website</div>
          <div className="text-surface-900 font-medium truncate mt-0.5">{report.website_url || 'N/A'}</div>
        </div>
        <div className="p-3 rounded-lg bg-surface-50 border border-surface-200/70">
          <div className="text-surface-500 font-mono text-[10px] uppercase font-bold">Jira Story</div>
          <div className="text-surface-900 font-mono font-medium truncate mt-0.5">{report.jira_issue_id || 'None'}</div>
        </div>
        <div className="p-3 rounded-lg bg-surface-50 border border-surface-200/70">
          <div className="text-surface-500 font-mono text-[10px] uppercase font-bold">Automation Framework</div>
          <div className="text-blue-600 font-mono font-bold uppercase mt-0.5">{report.automation_framework}</div>
        </div>
        <div className="p-3 rounded-lg bg-surface-50 border border-surface-200/70">
          <div className="text-surface-500 font-mono text-[10px] uppercase font-bold">Intelligence Engine</div>
          <div className="text-surface-900 font-mono font-bold uppercase mt-0.5">
            {report.generation_mode === 'basic' ? 'Basic (DOM Inspection)' : 'AI-Powered (OpenAI)'}
          </div>
        </div>
      </div>
    </div>
  );
}
