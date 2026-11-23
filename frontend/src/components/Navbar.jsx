import React from 'react';
import Logo from '../assets/branding/Logo';
import { Play, Sparkles, RefreshCw, Cpu, Zap, Bot, ExternalLink, Activity } from 'lucide-react';

export default function Navbar({
  runs,
  activeRunId,
  setActiveRunId,
  activeRunData,
  settings,
  onNewRunClick,
  onRefresh
}) {
  const isOpenAIConfigured = settings?.openai_configured;
  const isGeminiConfigured = settings?.gemini_configured;
  const isJiraConfigured = settings?.jira_configured;
  const provider = activeRunData?.ai_provider || activeRunData?.generation_mode || (isGeminiConfigured ? 'gemini' : isOpenAIConfigured ? 'openai' : 'basic');
  const modelName = activeRunData?.ai_model || (provider === 'gemini' ? settings?.gemini_model : settings?.openai_model);
  const framework = activeRunData?.automation_framework || settings?.default_automation_framework || 'playwright';

  const getProviderBadge = () => {
    if (provider === 'gemini') {
      return {
        label: modelName ? `Gemini: ${modelName}` : 'Gemini API Mode',
        className: 'bg-blue-50 text-blue-800 border-blue-200',
        icon: <Sparkles className="w-3 h-3 text-blue-600" />,
      };
    }
    if (provider === 'openai') {
      return {
        label: modelName ? `OpenAI: ${modelName}` : 'OpenAI API Mode',
        className: 'bg-purple-50 text-purple-800 border-purple-200',
        icon: <Bot className="w-3 h-3 text-purple-600" />,
      };
    }
    return {
      label: 'Basic Mode (Offline)',
      className: 'bg-amber-50 text-amber-800 border-amber-200',
      icon: <Zap className="w-3 h-3 text-amber-600" />,
    };
  };

  const badge = getProviderBadge();

  return (
    <header className="h-16 bg-white border-b border-surface-200 px-6 flex items-center justify-between z-10 shadow-2xs">
      {/* Left: Mobile Brand & Active Run Selector Dropdown */}
      <div className="flex items-center gap-3">
        <div className="lg:hidden shrink-0" title="TraceAI Studio">
          <Logo variant="icon" size={28} />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-surface-400">
            Current Run:
          </span>
          <select
            value={activeRunId || ''}
            onChange={(e) => setActiveRunId(e.target.value)}
            className="bg-surface-50 border border-surface-200 text-surface-900 text-xs font-mono rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-medium"
          >
            {runs.length === 0 && <option value="">No testing runs available</option>}
            {runs.map((r) => {
              const prov = (r.ai_provider || r.generation_mode || 'basic').toUpperCase();
              return (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} — {r.website_url ? r.website_url.replace(/^https?:\/\//, '') : 'Manual / Jira'} ({r.automation_framework?.toUpperCase()} • {prov})
                </option>
              );
            })}
          </select>
        </div>

        <button
          onClick={onRefresh}
          title="Refresh run state"
          className="p-1.5 rounded-lg border border-surface-200 bg-white text-surface-500 hover:text-surface-900 hover:bg-surface-50 transition-colors shadow-2xs"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Right: Operational Status Pills & New Run Action */}
      <div className="flex items-center gap-2.5">
        {/* Active Mode Pill */}
        <div className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${badge.className}`}>
          {badge.icon}
          <span className="font-mono text-[11px] font-semibold">{badge.label}</span>
        </div>

        {/* Jira MCP Indicator */}
        <div className={`hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
          isJiraConfigured
            ? 'bg-blue-50 text-blue-700 border-blue-200'
            : 'bg-surface-100 text-surface-600 border-surface-200'
        }`}>
          <Cpu className="w-3 h-3 text-blue-600" />
          <span className="text-[11px] font-semibold">{isJiraConfigured ? 'Jira MCP Active' : 'Jira Optional'}</span>
        </div>

        {/* Start New Run Primary Button */}
        <button
          onClick={onNewRunClick}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all focus:ring-2 focus:ring-blue-500/20"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>New Testing Run</span>
        </button>
      </div>
    </header>
  );
}
