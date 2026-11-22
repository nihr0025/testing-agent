import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Sparkles,
  Cpu,
  Zap,
  Save,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  RefreshCw,
  ShieldCheck,
  Bot,
  AlertTriangle,
  Code2
} from 'lucide-react';
import { api } from '../services/api';

export default function Settings({ onSettingsUpdated }) {
  const [settings, setSettings] = useState(null);
  const [openaiKey, setOpenaiKey] = useState('');
  const [openaiModel, setOpenaiModel] = useState('gpt-4o-mini');
  const [jiraUrl, setJiraUrl] = useState('');
  const [jiraEmail, setJiraEmail] = useState('');
  const [jiraToken, setJiraToken] = useState('');
  const [mcpUrl, setMcpUrl] = useState('');
  const [defaultFramework, setDefaultFramework] = useState('playwright');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState('');
  const [jiraStatus, setJiraStatus] = useState(null);

  // AI Verification state
  const [verifyingAi, setVerifyingAi] = useState(false);
  const [aiTestResult, setAiTestResult] = useState(null);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
      setOpenaiModel(data.openai_model || 'gpt-4o-mini');
      setJiraUrl(data.jira_url || '');
      setJiraEmail(data.jira_email || '');
      setMcpUrl(data.jira_mcp_url || '');
      setDefaultFramework(data.default_automation_framework || 'playwright');

      const jStat = await api.getJiraStatus();
      setJiraStatus(jStat);
    } catch (_) {}
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleTestAiKey = async () => {
    setVerifyingAi(true);
    setAiTestResult(null);
    try {
      const res = await api.testOpenAI();
      setAiTestResult(res);
    } catch (err) {
      setAiTestResult({
        valid: false,
        error_type: 'NetworkError',
        message: err.message || 'Could not reach backend validation endpoint.'
      });
    } finally {
      setVerifyingAi(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSaveSuccess(false);

    try {
      await api.updateSettings({
        openai_api_key: openaiKey || undefined,
        openai_model: openaiModel,
        jira_url: jiraUrl,
        jira_email: jiraEmail,
        jira_api_token: jiraToken || undefined,
        jira_mcp_url: mcpUrl,
        default_automation_framework: defaultFramework,
      });

      setSaveSuccess(true);
      setOpenaiKey('');
      setJiraToken('');
      setAiTestResult(null);
      await loadSettings();
      if (onSettingsUpdated) onSettingsUpdated();
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setError(err.message || 'Failed to update settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="pb-4 border-b border-surface-200">
        <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Platform Settings</h1>
        <p className="text-xs text-surface-500 mt-1">
          Configure AI intelligence providers, Basic Mode preferences, Jira MCP integration, and test frameworks.
        </p>
      </div>

      {saveSuccess && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2.5 shadow-2xs">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
          <span>Platform settings have been successfully updated and persisted!</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2.5 shadow-2xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* DUAL INTELLIGENCE MODES EXPLANATION BANNER */}
      <div className="bg-white border border-surface-200 rounded-xl p-5 space-y-3 shadow-2xs">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-blue-600" />
          <h2 className="text-sm font-bold text-surface-900">
            Dual Testing Intelligence Modes
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-4 rounded-xl bg-amber-50/50 border border-amber-200 space-y-1.5">
            <div className="font-bold text-amber-900 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-amber-600" />
              <span>Basic Testing Mode (API-Independent)</span>
            </div>
            <p className="text-surface-600 text-[11px] leading-relaxed">
              Always active whenever an API key is missing or quota is exhausted. Agent 1 parses live accessible HTML elements (inputs, forms, buttons, links), while Agents 2–6 apply deterministic QA logic. 100% free and offline-capable.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-purple-50/50 border border-purple-200 space-y-1.5">
            <div className="font-bold text-purple-900 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-purple-600" />
              <span>AI-Powered Testing Mode (OpenAI)</span>
            </div>
            <p className="text-surface-600 text-[11px] leading-relaxed">
              Uses OpenAI reasoning (<code className="text-purple-700 font-mono font-semibold">gpt-4o-mini</code>) to analyze edge cases and exploratory scenarios. If quota expires or a key error occurs, TraceAI Studio automatically falls back to Basic Mode without failing your test run.
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* SECTION 1: DEFAULT AUTOMATION FRAMEWORK */}
        <div className="bg-white border border-surface-200 rounded-xl p-6 space-y-4 shadow-2xs">
          <div>
            <h2 className="text-sm font-bold text-surface-900 flex items-center gap-2">
              <Code2 className="w-4 h-4 text-blue-600" />
              Default Browser Automation Framework
            </h2>
            <p className="text-[11px] text-surface-500 mt-0.5">
              Sets the pre-selected engine for newly created testing runs
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            <div
              onClick={() => setDefaultFramework('playwright')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                defaultFramework === 'playwright'
                  ? 'bg-blue-50/40 border-blue-400 ring-2 ring-blue-400/20 shadow-2xs'
                  : 'bg-white border-surface-200 hover:border-surface-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-surface-900">Playwright (Default)</span>
                {defaultFramework === 'playwright' && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
              </div>
              <p className="text-[11px] text-surface-500 mt-1 leading-relaxed">
                Fast headless Chromium execution, auto-wait locators, and native tracing.
              </p>
            </div>

            <div
              onClick={() => setDefaultFramework('selenium')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                defaultFramework === 'selenium'
                  ? 'bg-blue-50/40 border-blue-400 ring-2 ring-blue-400/20 shadow-2xs'
                  : 'bg-white border-surface-200 hover:border-surface-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-surface-900">Selenium WebDriver</span>
                {defaultFramework === 'selenium' && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
              </div>
              <p className="text-[11px] text-surface-500 mt-1 leading-relaxed">
                W3C WebDriver protocol with automated driver management.
              </p>
            </div>
          </div>
        </div>

        {/* SECTION 2: OPENAI API CONFIGURATION */}
        <div className="bg-white border border-surface-200 rounded-xl p-6 space-y-4 shadow-2xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-bold text-surface-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-600" />
                OpenAI API Configuration (AI Mode)
              </h2>
              <p className="text-[11px] text-surface-500 mt-0.5">
                Securely reads OPENAI_API_KEY from backend environment. Keys are never exposed.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className={`text-[10px] font-mono font-semibold uppercase px-2.5 py-1 rounded-full border ${
                settings?.openai_configured
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}>
                {settings?.openai_configured ? 'Key Configured' : 'Missing (Basic Mode Active)'}
              </span>

              <button
                type="button"
                onClick={handleTestAiKey}
                disabled={verifyingAi}
                className="px-2.5 py-1 rounded-lg bg-surface-50 border border-surface-200 text-[11px] font-medium text-surface-700 hover:text-surface-900 hover:bg-surface-100 flex items-center gap-1 transition-colors"
              >
                {verifyingAi ? <RefreshCw className="w-3 h-3 animate-spin text-blue-600" /> : <ShieldCheck className="w-3 h-3 text-blue-600" />}
                <span>Verify Key &amp; Quota</span>
              </button>
            </div>
          </div>

          {/* Verification Result Banner */}
          {aiTestResult && (
            <div className={`p-3.5 rounded-xl border text-xs flex items-start gap-2.5 ${
              aiTestResult.valid
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-amber-50 border-amber-200 text-amber-800'
            }`}>
              {aiTestResult.valid ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 mt-0.5" />
              ) : (
                <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
              )}
              <div>
                <span className="font-bold block">{aiTestResult.valid ? 'Verification Successful' : `OpenAI Notice (${aiTestResult.error_type || 'Notice'})`}</span>
                <span className="text-[11px] text-surface-600">{aiTestResult.message}</span>
              </div>
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="text-xs text-surface-600 font-medium block mb-1">
                OpenAI API Key {settings?.masked_api_key && <span className="text-surface-400 font-mono text-[11px]">(Current: {settings.masked_api_key})</span>}
              </label>
              <div className="relative">
                <input
                  type={showKey ? 'text' : 'password'}
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  placeholder={settings?.masked_api_key ? 'Enter new key to update...' : 'sk-...'}
                  className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs rounded-lg px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-700"
                >
                  {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="text-xs text-surface-600 font-medium block mb-1">AI Model Name</label>
              <input
                type="text"
                value={openaiModel}
                onChange={(e) => setOpenaiModel(e.target.value)}
                placeholder="gpt-4o-mini"
                className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs rounded-lg px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono"
              />
            </div>
          </div>
        </div>

        {/* SECTION 3: JIRA & MCP INTEGRATION */}
        <div className="bg-white border border-surface-200 rounded-xl p-6 space-y-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-surface-900 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-blue-600" />
                Jira MCP &amp; REST Connectivity (Independent)
              </h2>
              <p className="text-[11px] text-surface-500 mt-0.5">
                Connect via Atlassian Jira MCP Server endpoint or direct Jira Cloud credentials.
              </p>
            </div>
            <span className={`text-[10px] font-mono font-semibold uppercase px-2.5 py-1 rounded-full border ${
              jiraStatus?.connected
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-surface-100 text-surface-500 border-surface-200'
            }`}>
              Status: {jiraStatus?.connected ? 'Online' : 'Unconfigured'}
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs text-surface-600 font-medium block mb-1">Jira Cloud / Server URL</label>
              <input
                type="text"
                value={jiraUrl}
                onChange={(e) => setJiraUrl(e.target.value)}
                placeholder="https://your-company.atlassian.net"
                className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs rounded-lg px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-surface-600 font-medium block mb-1">Jira User Email</label>
                <input
                  type="email"
                  value={jiraEmail}
                  onChange={(e) => setJiraEmail(e.target.value)}
                  placeholder="qa-lead@company.com"
                  className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs rounded-lg px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-xs text-surface-600 font-medium block mb-1">Jira API Token</label>
                <input
                  type="password"
                  value={jiraToken}
                  onChange={(e) => setJiraToken(e.target.value)}
                  placeholder="Enter API token..."
                  className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs rounded-lg px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono"
                />
              </div>
            </div>

            <div>
              <label className="text-xs text-surface-600 font-medium block mb-1">Optional Jira MCP Server Endpoint (HTTP / SSE)</label>
              <input
                type="text"
                value={mcpUrl}
                onChange={(e) => setMcpUrl(e.target.value)}
                placeholder="http://localhost:3000"
                className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs rounded-lg px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono"
              />
            </div>
          </div>
        </div>

        {/* SAVE BUTTON */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all disabled:opacity-50"
          >
            {saving ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            <span>Save Configuration</span>
          </button>
        </div>
      </form>
    </div>
  );
}
