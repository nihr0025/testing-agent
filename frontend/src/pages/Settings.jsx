import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Sparkles,
  Cpu,
  Zap,
  Save,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ShieldCheck,
  Bot,
  AlertTriangle,
  Code2,
  Check
} from 'lucide-react';
import { api } from '../services/api';

export default function Settings({ onSettingsUpdated }) {
  const [settings, setSettings] = useState(null);
  const [defaultProvider, setDefaultProvider] = useState('basic');
  const [openaiModel, setOpenaiModel] = useState('');
  const [geminiModel, setGeminiModel] = useState('');
  const [defaultFramework, setDefaultFramework] = useState('playwright');
  const [jiraUrl, setJiraUrl] = useState('');
  const [jiraEmail, setJiraEmail] = useState('');
  const [jiraToken, setJiraToken] = useState('');
  const [mcpUrl, setMcpUrl] = useState('');

  // Dynamic models
  const [openaiModels, setOpenaiModels] = useState([]);
  const [geminiModels, setGeminiModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState({ gemini: false, openai: false });
  const [discoveryErrors, setDiscoveryErrors] = useState({ gemini: null, openai: null });

  // Testing status
  const [testingOpenAi, setTestingOpenAi] = useState(false);
  const [openaiTestResult, setOpenaiTestResult] = useState(null);

  const [testingGemini, setTestingGemini] = useState(false);
  const [geminiTestResult, setGeminiTestResult] = useState(null);

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState('');
  const [jiraStatus, setJiraStatus] = useState(null);

  const fetchModels = async (provider, forceRefresh = false) => {
    setLoadingModels((prev) => ({ ...prev, [provider]: true }));
    setDiscoveryErrors((prev) => ({ ...prev, [provider]: null }));
    try {
      const res = await api.getProviderModels(provider, forceRefresh);
      const list = Array.isArray(res) ? res : res?.models || [];
      if (res?.error) {
        setDiscoveryErrors((prev) => ({ ...prev, [provider]: res.error }));
      }
      if (provider === 'gemini') {
        setGeminiModels(list);
      } else if (provider === 'openai') {
        setOpenaiModels(list);
      }
    } catch (err) {
      setDiscoveryErrors((prev) => ({
        ...prev,
        [provider]: err.message || `Failed to dynamically discover ${provider} models`,
      }));
    } finally {
      setLoadingModels((prev) => ({ ...prev, [provider]: false }));
    }
  };

  const loadData = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
      setDefaultProvider(data.default_testing_mode || 'basic');
      setOpenaiModel(data.openai_model || '');
      setGeminiModel(data.gemini_model || '');
      setDefaultFramework(data.default_automation_framework || 'playwright');
      setJiraUrl(data.jira_url || '');
      setJiraEmail(data.jira_email || '');
      setMcpUrl(data.jira_mcp_url || '');

      // Load Jira status
      api.getJiraStatus().then(setJiraStatus).catch(() => {});

      // Fetch dynamic models from authenticated APIs
      fetchModels('openai', false);
      fetchModels('gemini', false);
    } catch (err) {
      setError('Could not load configuration from server.');
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTestProvider = async (provider) => {
    if (provider === 'openai') {
      setTestingOpenAi(true);
      setOpenaiTestResult(null);
      try {
        const res = await api.testProviderConnection('openai');
        setOpenaiTestResult(res);
      } catch (err) {
        setOpenaiTestResult({
          valid: false,
          error_type: 'NetworkError',
          message: err.message || 'Validation request failed',
        });
      } finally {
        setTestingOpenAi(false);
      }
    } else if (provider === 'gemini') {
      setTestingGemini(true);
      setGeminiTestResult(null);
      try {
        const res = await api.testProviderConnection('gemini');
        setGeminiTestResult(res);
      } catch (err) {
        setGeminiTestResult({
          valid: false,
          error_type: 'NetworkError',
          message: err.message || 'Validation request failed',
        });
      } finally {
        setTestingGemini(false);
      }
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSaveSuccess(false);

    try {
      await api.updateSettings({
        default_testing_mode: defaultProvider,
        openai_model: openaiModel || undefined,
        gemini_model: geminiModel || undefined,
        default_automation_framework: defaultFramework,
        jira_url: jiraUrl,
        jira_email: jiraEmail,
        jira_api_token: jiraToken || undefined,
        jira_mcp_url: mcpUrl,
      });

      setSaveSuccess(true);
      setJiraToken('');
      await loadData();
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
        <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Platform Configuration</h1>
        <p className="text-xs text-surface-500 mt-1">
          Manage AI providers, dynamic model discovery, credentials security, browser automation engines, and Jira integration.
        </p>
      </div>

      {saveSuccess && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2.5 shadow-2xs">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
          <span>Configuration settings updated and persisted successfully!</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2.5 shadow-2xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* CREDENTIALS SECURITY & ENV INSTRUCTION CALLOUT */}
      <div className="bg-white border border-surface-200 rounded-xl p-5 space-y-3 shadow-2xs">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <h2 className="text-xs font-bold text-surface-900 uppercase font-mono tracking-wider">
            Environment-Based Credential Management
          </h2>
        </div>
        <p className="text-xs text-surface-600 leading-relaxed">
          For production security, API keys are <strong>never entered or transmitted from the browser</strong>. They are stored strictly in the backend <code className="bg-surface-100 text-surface-800 px-1.5 py-0.5 rounded font-mono text-[11px]">.env</code> file. Available models are queried dynamically via official provider APIs.
        </p>

        <div className="p-3 bg-surface-900 text-surface-100 rounded-lg text-xs font-mono space-y-1 overflow-x-auto">
          <div className="text-surface-400"># Configure credentials in backend/.env:</div>
          <div>OPENAI_API_KEY=your_openai_api_key_here</div>
          <div>GEMINI_API_KEY=your_gemini_api_key_here</div>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* SECTION 1: AI & BASIC TESTING PROVIDERS */}
        <div className="bg-white border border-surface-200 rounded-xl p-6 space-y-5 shadow-2xs">
          <div>
            <h2 className="text-sm font-bold text-surface-900 flex items-center gap-2">
              <Bot className="w-4 h-4 text-blue-600" />
              Intelligence Providers &amp; Dynamic Model Discovery
            </h2>
            <p className="text-[11px] text-surface-500 mt-0.5">
              Available models are retrieved dynamically from the authenticated provider API. No hardcoded models or simulated catalogs.
            </p>
          </div>

          <div className="space-y-4">
            {/* 1. Basic Mode Card */}
            <div className="p-4 rounded-xl border border-surface-200 bg-surface-50/50 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-amber-600" />
                  <span className="font-bold text-xs text-surface-900">Basic Testing Mode</span>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                    ALWAYS ACTIVE &bull; 100% OFFLINE
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-surface-600 leading-relaxed">
                Requires no API keys or internet connection to external AI services. Agent 1 parses live HTML elements (forms, inputs, buttons, navigation), while Agents 2–6 formulate robust test suites using deterministic QA logic.
              </p>
            </div>

            {/* 2. Google Gemini Card */}
            <div className="p-4 rounded-xl border border-surface-200 bg-white space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-blue-600" />
                  <span className="font-bold text-xs text-surface-900">Google Gemini API</span>
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                    settings?.gemini_configured
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-rose-50 text-rose-700 border-rose-200'
                  }`}>
                    {settings?.gemini_configured ? `KEY IN .ENV (${settings.gemini_masked_key || '***'})` : 'GEMINI_API_KEY MISSING'}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => fetchModels('gemini', true)}
                    disabled={loadingModels.gemini}
                    className="px-2.5 py-1 rounded-lg bg-white border border-surface-200 text-[11px] font-medium text-surface-700 hover:text-surface-900 hover:bg-surface-50 flex items-center gap-1 transition-colors shadow-2xs"
                  >
                    <RefreshCw className={`w-3 h-3 text-blue-600 ${loadingModels.gemini ? 'animate-spin' : ''}`} />
                    <span>Refresh Models</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleTestProvider('gemini')}
                    disabled={testingGemini}
                    className="px-2.5 py-1 rounded-lg bg-surface-50 border border-surface-200 text-[11px] font-medium text-surface-700 hover:text-surface-900 hover:bg-surface-100 flex items-center gap-1 transition-colors self-start sm:self-auto"
                  >
                    {testingGemini ? <RefreshCw className="w-3 h-3 animate-spin text-blue-600" /> : <ShieldCheck className="w-3 h-3 text-blue-600" />}
                    <span>Verify Connection</span>
                  </button>
                </div>
              </div>

              {geminiTestResult && (
                <div className={`p-3 rounded-lg border text-xs flex items-start gap-2 ${
                  geminiTestResult.valid
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : 'bg-amber-50 border-amber-200 text-amber-800'
                }`}>
                  {geminiTestResult.valid ? (
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 mt-0.5" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
                  )}
                  <div>
                    <span className="font-bold block">
                      {geminiTestResult.valid ? `Gemini Verified (${geminiTestResult.latency_ms || 0}ms)` : `Gemini Error (${geminiTestResult.error_type || 'Notice'})`}
                    </span>
                    <span className="text-[11px] text-surface-600">{geminiTestResult.message}</span>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="text-xs text-surface-600 font-medium block mb-1">
                    Preferred Gemini Model (from live API discovery)
                  </label>
                  <select
                    value={geminiModel}
                    onChange={(e) => setGeminiModel(e.target.value)}
                    className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono"
                  >
                    <option value="">-- No model preset (Select at run time) --</option>
                    {geminiModels.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name || m.id} {m.is_free_tier ? '• Free Tier Available' : ''}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center text-[11px] text-surface-500">
                  <span>
                    {discoveryErrors.gemini ? (
                      <span className="text-rose-600 font-medium">{discoveryErrors.gemini}</span>
                    ) : (
                      `Discovered ${geminiModels.length} compatible generation models from Google Gen AI.`
                    )}
                  </span>
                </div>
              </div>
            </div>

            {/* 3. OpenAI Card */}
            <div className="p-4 rounded-xl border border-surface-200 bg-white space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  <span className="font-bold text-xs text-surface-900">OpenAI API</span>
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                    settings?.openai_configured
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-rose-50 text-rose-700 border-rose-200'
                  }`}>
                    {settings?.openai_configured ? `KEY IN .ENV (${settings.openai_masked_key || '***'})` : 'OPENAI_API_KEY MISSING'}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => fetchModels('openai', true)}
                    disabled={loadingModels.openai}
                    className="px-2.5 py-1 rounded-lg bg-white border border-surface-200 text-[11px] font-medium text-surface-700 hover:text-surface-900 hover:bg-surface-50 flex items-center gap-1 transition-colors shadow-2xs"
                  >
                    <RefreshCw className={`w-3 h-3 text-purple-600 ${loadingModels.openai ? 'animate-spin' : ''}`} />
                    <span>Refresh Models</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleTestProvider('openai')}
                    disabled={testingOpenAi}
                    className="px-2.5 py-1 rounded-lg bg-surface-50 border border-surface-200 text-[11px] font-medium text-surface-700 hover:text-surface-900 hover:bg-surface-100 flex items-center gap-1 transition-colors self-start sm:self-auto"
                  >
                    {testingOpenAi ? <RefreshCw className="w-3 h-3 animate-spin text-blue-600" /> : <ShieldCheck className="w-3 h-3 text-blue-600" />}
                    <span>Verify Connection</span>
                  </button>
                </div>
              </div>

              {openaiTestResult && (
                <div className={`p-3 rounded-lg border text-xs flex items-start gap-2 ${
                  openaiTestResult.valid
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : 'bg-amber-50 border-amber-200 text-amber-800'
                }`}>
                  {openaiTestResult.valid ? (
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 mt-0.5" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
                  )}
                  <div>
                    <span className="font-bold block">
                      {openaiTestResult.valid ? `OpenAI Verified (${openaiTestResult.latency_ms || 0}ms)` : `OpenAI Error (${openaiTestResult.error_type || 'Notice'})`}
                    </span>
                    <span className="text-[11px] text-surface-600">{openaiTestResult.message}</span>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="text-xs text-surface-600 font-medium block mb-1">
                    Preferred OpenAI Model (from live API discovery)
                  </label>
                  <select
                    value={openaiModel}
                    onChange={(e) => setOpenaiModel(e.target.value)}
                    className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono"
                  >
                    <option value="">-- No model preset (Select at run time) --</option>
                    {openaiModels.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name || m.id}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center text-[11px] text-surface-500">
                  <span>
                    {discoveryErrors.openai ? (
                      <span className="text-rose-600 font-medium">{discoveryErrors.openai}</span>
                    ) : (
                      `Discovered ${openaiModels.length} compatible generation models from OpenAI.`
                    )}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* SECTION 2: DEFAULT EXECUTION FRAMEWORK & RUNTIME DEFAULTS */}
        <div className="bg-white border border-surface-200 rounded-xl p-6 space-y-4 shadow-2xs">
          <div>
            <h2 className="text-sm font-bold text-surface-900 flex items-center gap-2">
              <Code2 className="w-4 h-4 text-blue-600" />
              Default Automation Framework
            </h2>
            <p className="text-[11px] text-surface-500 mt-0.5">
              Select the default test automation framework pre-configured for new test runs
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
                <span className="font-bold text-sm text-surface-900">Playwright (Recommended)</span>
                {defaultFramework === 'playwright' && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
              </div>
              <p className="text-[11px] text-surface-500 mt-1 leading-relaxed">
                Fast headless Chromium execution, auto-wait locators, and native screenshots.
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
                W3C standard WebDriver protocol with automatic ChromeDriver resolution.
              </p>
            </div>
          </div>
        </div>

        {/* SECTION 3: JIRA MCP & REST CONNECTIVITY */}
        <div className="bg-white border border-surface-200 rounded-xl p-6 space-y-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-surface-900 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-600" />
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
                  placeholder="Enter API token to update..."
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
