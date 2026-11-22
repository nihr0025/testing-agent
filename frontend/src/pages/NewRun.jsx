import React, { useState, useEffect } from 'react';
import {
  Globe,
  FileText,
  Cpu,
  Play,
  AlertCircle,
  Sparkles,
  Zap,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  Bot,
  ArrowRight,
  ArrowLeft,
  Settings,
  Layers,
  Code2,
  Check
} from 'lucide-react';
import { api } from '../services/api';

export default function NewRun({ onRunStarted, defaultFramework = 'playwright' }) {
  const [step, setStep] = useState(1);
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [jiraProject, setJiraProject] = useState('');
  const [jiraIssueId, setJiraIssueId] = useState('');
  const [manualRequirements, setManualRequirements] = useState('');
  const [framework, setFramework] = useState(defaultFramework);
  const [mode, setMode] = useState('basic'); // 'basic' or 'ai'
  const [headless, setHeadless] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [jiraIssues, setJiraIssues] = useState([]);
  const [showJiraPicker, setShowJiraPicker] = useState(false);
  const [settings, setSettings] = useState(null);

  useEffect(() => {
    api.getJiraIssues()
      .then((data) => setJiraIssues(data || []))
      .catch(() => {});

    api.getSettings()
      .then((s) => {
        setSettings(s);
        if (s?.openai_configured) {
          setMode('ai');
        } else {
          setMode('basic');
        }
      })
      .catch(() => {});
  }, []);

  const fillDemoUrl = () => {
    setWebsiteUrl('http://127.0.0.1:8000/demo');
    setManualRequirements('Verify navigation, search functionality, and login error handling on Acme Demo Shop.');
  };

  const isAiConfigured = settings?.openai_configured;

  const validateStep1 = () => {
    const url = websiteUrl.trim();
    const issue = jiraIssueId.trim();
    const manual = manualRequirements.trim();
    if (!url && !issue && !manual) {
      setError('Please provide at least a Website URL, a Jira Issue ID, or Manual Requirements to proceed.');
      return false;
    }
    setError('');
    return true;
  };

  const handleNext = () => {
    if (step === 1) {
      if (!validateStep1()) return;
      setStep(2);
    } else if (step === 2) {
      setStep(3);
    }
  };

  const handleBack = () => {
    setError('');
    setStep(Math.max(1, step - 1));
  };

  const handleStartRun = async (e) => {
    if (e) e.preventDefault();
    if (!validateStep1()) {
      setStep(1);
      return;
    }

    setLoading(true);
    setError('');
    try {
      const res = await api.startTesting({
        website_url: websiteUrl.trim(),
        jira_project: jiraProject.trim(),
        jira_issue_id: jiraIssueId.trim(),
        manual_requirements: manualRequirements.trim(),
        automation_framework: framework,
        generation_mode: mode,
      });

      if (res?.run_id) {
        onRunStarted(res.run_id);
      }
    } catch (err) {
      setError(err.message || 'Failed to initiate testing run.');
      setLoading(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-surface-900 tracking-tight">New Testing Run</h1>
        <p className="text-xs text-surface-500 mt-1">
          Configure test target, intelligence mode, and execution framework for the multi-agent QA fleet.
        </p>
      </div>

      {/* Modern 3-Step Wizard Progress Bar */}
      <div className="bg-white border border-surface-200 rounded-xl p-4 shadow-2xs">
        <div className="grid grid-cols-3 gap-2">
          {/* Step 1 Pill */}
          <div
            onClick={() => setStep(1)}
            className={`flex items-center gap-2.5 p-2 rounded-lg cursor-pointer transition-all ${
              step === 1
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : step > 1
                ? 'text-surface-700 hover:bg-surface-50'
                : 'text-surface-400'
            }`}
          >
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
              step === 1 ? 'bg-blue-600 text-white' : step > 1 ? 'bg-emerald-600 text-white' : 'bg-surface-200 text-surface-600'
            }`}>
              {step > 1 ? <Check className="w-3.5 h-3.5" /> : '1'}
            </div>
            <div className="text-left truncate">
              <div className="text-xs font-bold leading-tight">Target</div>
              <div className="text-[10px] text-surface-400 truncate">URL, Jira, or Story</div>
            </div>
          </div>

          {/* Step 2 Pill */}
          <div
            onClick={() => {
              if (validateStep1()) setStep(2);
            }}
            className={`flex items-center gap-2.5 p-2 rounded-lg cursor-pointer transition-all ${
              step === 2
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : step > 2
                ? 'text-surface-700 hover:bg-surface-50'
                : 'text-surface-400'
            }`}
          >
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
              step === 2 ? 'bg-blue-600 text-white' : step > 2 ? 'bg-emerald-600 text-white' : 'bg-surface-200 text-surface-600'
            }`}>
              {step > 2 ? <Check className="w-3.5 h-3.5" /> : '2'}
            </div>
            <div className="text-left truncate">
              <div className="text-xs font-bold leading-tight">Configuration</div>
              <div className="text-[10px] text-surface-400 truncate">AI Mode & Engine</div>
            </div>
          </div>

          {/* Step 3 Pill */}
          <div
            onClick={() => {
              if (validateStep1()) setStep(3);
            }}
            className={`flex items-center gap-2.5 p-2 rounded-lg cursor-pointer transition-all ${
              step === 3
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'text-surface-400'
            }`}
          >
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
              step === 3 ? 'bg-blue-600 text-white' : 'bg-surface-200 text-surface-600'
            }`}>
              3
            </div>
            <div className="text-left truncate">
              <div className="text-xs font-bold leading-tight">Review & Launch</div>
              <div className="text-[10px] text-surface-400 truncate">Summary & Start</div>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2.5 shadow-2xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* STEP 1: TARGET DEFINITION */}
      {step === 1 && (
        <div className="space-y-4">
          {/* URL Input Card */}
          <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-surface-900 uppercase font-mono tracking-wider flex items-center gap-2">
                <Globe className="w-4 h-4 text-blue-600" />
                Target Website URL
              </label>
              <button
                type="button"
                onClick={fillDemoUrl}
                className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1.5 transition-colors"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Use Built-in Sandbox Demo</span>
              </button>
            </div>
            <input
              type="text"
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
              placeholder="e.g. http://127.0.0.1:8000/demo or https://your-website.com"
              className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs font-mono rounded-lg px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
            <p className="text-[11px] text-surface-500">
              Agent 1 directly probes this target to identify forms, buttons, links, and input controls.
            </p>
          </div>

          {/* Jira Integration Card (MCP) */}
          <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-surface-900 uppercase font-mono tracking-wider flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-600" />
                Jira Issue / User Story (MCP)
              </label>
              <button
                type="button"
                onClick={() => setShowJiraPicker(!showJiraPicker)}
                className="text-xs text-purple-600 hover:text-purple-700 font-semibold"
              >
                {showJiraPicker ? 'Hide Jira Picker' : 'Browse Jira Issues'}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-surface-500 block mb-1 font-medium">Jira Project Key</label>
                <input
                  type="text"
                  value={jiraProject}
                  onChange={(e) => setJiraProject(e.target.value)}
                  placeholder="e.g. QA, ECOM, AUTH"
                  className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs font-mono uppercase rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-[11px] text-surface-500 block mb-1 font-medium">Issue ID</label>
                <input
                  type="text"
                  value={jiraIssueId}
                  onChange={(e) => setJiraIssueId(e.target.value)}
                  placeholder="e.g. QA-101"
                  className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs font-mono uppercase rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>
            </div>

            {showJiraPicker && (
              <div className="mt-3 p-3 rounded-lg bg-surface-50 border border-surface-200 space-y-2">
                <div className="text-[10px] text-surface-500 font-bold uppercase font-mono">Available Jira Stories:</div>
                <div className="space-y-1.5 max-h-36 overflow-y-auto">
                  {jiraIssues.length === 0 ? (
                    <div className="text-xs text-surface-400 py-2">No live Jira issues found.</div>
                  ) : (
                    jiraIssues.map((issue) => (
                      <div
                        key={issue.key}
                        onClick={() => {
                          setJiraIssueId(issue.key);
                          setJiraProject(issue.key.split('-')[0]);
                          setManualRequirements(issue.description || issue.summary);
                          setShowJiraPicker(false);
                        }}
                        className="p-2 rounded bg-white hover:bg-blue-50 border border-surface-200 cursor-pointer text-xs flex items-center justify-between transition-colors"
                      >
                        <div>
                          <span className="font-mono font-bold text-blue-600 mr-2">{issue.key}</span>
                          <span className="text-surface-700">{issue.summary}</span>
                        </div>
                        <span className="text-[10px] text-purple-600 font-bold uppercase font-mono">{issue.status}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Manual Requirements Input Card */}
          <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs space-y-3">
            <label className="text-xs font-bold text-surface-900 uppercase font-mono tracking-wider flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-600" />
              Manual Requirements & Custom Testing Objectives
            </label>
            <textarea
              rows={3}
              value={manualRequirements}
              onChange={(e) => setManualRequirements(e.target.value)}
              placeholder="Describe specific functional acceptance criteria, business rules, or test scenarios..."
              className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs rounded-lg p-3.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 leading-relaxed"
            />
          </div>

          {/* Step 1 Actions */}
          <div className="flex justify-end pt-2">
            <button
              type="button"
              onClick={handleNext}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all"
            >
              <span>Continue to Configuration</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: CONFIGURATION */}
      {step === 2 && (
        <div className="space-y-4">
          {/* Intelligence Mode */}
          <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-xs font-bold text-surface-900 uppercase font-mono tracking-wider flex items-center gap-2">
                  <Bot className="w-4 h-4 text-blue-600" />
                  Testing Intelligence Mode
                </label>
                <p className="text-[11px] text-surface-500 mt-0.5">Select how the 6 agents will formulate and analyze test suites</p>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                mode === 'ai' ? 'bg-purple-50 text-purple-700 border-purple-200' : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}>
                {mode.toUpperCase()} MODE
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
              {/* Basic Mode Card */}
              <div
                onClick={() => setMode('basic')}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  mode === 'basic'
                    ? 'bg-amber-50/40 border-amber-400 ring-2 ring-amber-400/20 shadow-2xs'
                    : 'bg-white border-surface-200 hover:border-surface-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="font-bold text-sm text-surface-900 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-amber-600" />
                    Basic Mode (API-Independent)
                  </div>
                  {mode === 'basic' && <CheckCircle2 className="w-4 h-4 text-amber-600" />}
                </div>
                <p className="text-[11px] text-surface-500 mt-2 leading-relaxed">
                  Extracts live HTML DOM controls and uses deterministic Python test logic. 100% offline with zero external API dependencies.
                </p>
                <div className="mt-3 flex items-center gap-2 text-[10px] text-amber-700 font-mono font-semibold">
                  <span>✓ Always Available</span>
                  <span>•</span>
                  <span>✓ No API Key Required</span>
                </div>
              </div>

              {/* AI Mode Card */}
              <div
                onClick={() => setMode('ai')}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  mode === 'ai'
                    ? 'bg-purple-50/40 border-purple-400 ring-2 ring-purple-400/20 shadow-2xs'
                    : 'bg-white border-surface-200 hover:border-surface-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="font-bold text-sm text-surface-900 flex items-center gap-2">
                    <Bot className="w-4 h-4 text-purple-600" />
                    AI Mode (OpenAI Reasoning)
                  </div>
                  {mode === 'ai' && <CheckCircle2 className="w-4 h-4 text-purple-600" />}
                </div>
                <p className="text-[11px] text-surface-500 mt-2 leading-relaxed">
                  Generates exploratory boundary tests and edge-case validations using OpenAI structured schemas.
                </p>
                <div className="mt-3 text-[10px] font-mono">
                  {isAiConfigured ? (
                    <span className="text-emerald-700 font-semibold">✓ OpenAI API Key Configured</span>
                  ) : (
                    <span className="text-amber-700 font-semibold">⚠ Key Missing (Will fallback to Basic)</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Framework Selector */}
          <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-xs font-bold text-surface-900 uppercase font-mono tracking-wider flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-blue-600" />
                  Browser Automation Engine
                </label>
                <p className="text-[11px] text-surface-500 mt-0.5">Engine utilized by Agent 4 (Automation) and Agent 5 (Execution)</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
              <div
                onClick={() => setFramework('playwright')}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  framework === 'playwright'
                    ? 'bg-blue-50/40 border-blue-400 ring-2 ring-blue-400/20 shadow-2xs'
                    : 'bg-white border-surface-200 hover:border-surface-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="font-bold text-sm text-surface-900 flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
                    Playwright (Recommended)
                  </div>
                  {framework === 'playwright' && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
                </div>
                <p className="text-[11px] text-surface-500 mt-2 leading-relaxed">
                  Headless Chromium, auto-waiting locators, native screenshots, and trace recording.
                </p>
              </div>

              <div
                onClick={() => setFramework('selenium')}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  framework === 'selenium'
                    ? 'bg-blue-50/40 border-blue-400 ring-2 ring-blue-400/20 shadow-2xs'
                    : 'bg-white border-surface-200 hover:border-surface-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="font-bold text-sm text-surface-900 flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-600"></span>
                    Selenium WebDriver
                  </div>
                  {framework === 'selenium' && <CheckCircle2 className="w-4 h-4 text-cyan-600" />}
                </div>
                <p className="text-[11px] text-surface-500 mt-2 leading-relaxed">
                  W3C standard WebDriver protocol with explicit WebDriverWait and ChromeManager.
                </p>
              </div>
            </div>
          </div>

          {/* Browser Execution Preferences */}
          <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs space-y-3">
            <label className="text-xs font-bold text-surface-900 uppercase font-mono tracking-wider flex items-center gap-2">
              <Settings className="w-4 h-4 text-surface-600" />
              Runtime Preferences
            </label>
            <div className="flex items-center justify-between py-2 border-b border-surface-100 text-xs">
              <div>
                <span className="font-semibold text-surface-800">Headless Execution</span>
                <p className="text-[11px] text-surface-500">Run browser in background without popping windows</p>
              </div>
              <input
                type="checkbox"
                checked={headless}
                onChange={(e) => setHeadless(e.target.checked)}
                className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-surface-300"
              />
            </div>
            <div className="flex items-center justify-between py-2 text-xs">
              <div>
                <span className="font-semibold text-surface-800">Visual Evidence</span>
                <p className="text-[11px] text-surface-500">Automatically capture failure screenshots and pytest stdout logs</p>
              </div>
              <span className="text-[11px] font-mono font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                ENABLED
              </span>
            </div>
          </div>

          {/* Step 2 Actions */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={handleBack}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg border border-surface-200 bg-white hover:bg-surface-50 text-surface-700 font-semibold text-xs shadow-2xs transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
            <button
              type="button"
              onClick={handleNext}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all"
            >
              <span>Continue to Review</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: REVIEW & LAUNCH */}
      {step === 3 && (
        <div className="space-y-4">
          <div className="bg-white border border-surface-200 rounded-xl p-6 shadow-2xs space-y-5">
            <h2 className="text-base font-bold text-surface-900 border-b border-surface-200 pb-3">
              Testing Run Execution Plan
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3.5 rounded-xl bg-surface-50 border border-surface-200 space-y-2">
                <span className="font-bold text-surface-500 uppercase font-mono text-[10px]">Testing Target</span>
                <div className="font-mono font-semibold text-surface-900 truncate">
                  {websiteUrl || 'No Direct URL'}
                </div>
                {jiraIssueId && (
                  <div className="text-[11px] text-purple-700 font-mono">
                    Jira Issue: {jiraIssueId} ({jiraProject || 'Default'})
                  </div>
                )}
                {manualRequirements && (
                  <div className="text-[11px] text-surface-600 line-clamp-2">
                    Reqs: {manualRequirements}
                  </div>
                )}
              </div>

              <div className="p-3.5 rounded-xl bg-surface-50 border border-surface-200 space-y-2">
                <span className="font-bold text-surface-500 uppercase font-mono text-[10px]">Engine & Settings</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-surface-900 uppercase">{framework}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                    mode === 'basic' ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-purple-50 text-purple-700 border-purple-200'
                  }`}>
                    {mode.toUpperCase()} MODE
                  </span>
                </div>
                <div className="text-[11px] text-surface-500">
                  Headless: {headless ? 'Yes' : 'No'} • Pytest Runner • Screenshots: Auto
                </div>
              </div>
            </div>

            {/* Pipeline Preview */}
            <div className="p-4 rounded-xl border border-surface-200 bg-surface-50/70">
              <span className="text-[10px] font-mono font-bold text-surface-400 uppercase block mb-2">
                Execution Workflow Pipeline
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-center text-xs">
                <div className="p-2 rounded bg-white border border-surface-200 text-surface-700 font-medium">1. Requirements</div>
                <div className="p-2 rounded bg-white border border-surface-200 text-surface-700 font-medium">2. Scenarios</div>
                <div className="p-2 rounded bg-white border border-surface-200 text-surface-700 font-medium">3. Test Cases</div>
                <div className="p-2 rounded bg-white border border-surface-200 text-surface-700 font-medium">4. Automation</div>
                <div className="p-2 rounded bg-white border border-surface-200 text-surface-700 font-medium">5. Pytest Exec</div>
                <div className="p-2 rounded bg-white border border-surface-200 text-surface-700 font-medium">6. Report Audit</div>
              </div>
            </div>

            {/* Start Button */}
            <div className="pt-2">
              <button
                type="button"
                onClick={handleStartRun}
                disabled={loading}
                className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Initiating 6-Agent Collaboration...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>Launch Testing Run ({mode.toUpperCase()} • {framework.toUpperCase()})</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Step 3 Back Button */}
          <div className="flex justify-start">
            <button
              type="button"
              onClick={handleBack}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg border border-surface-200 bg-white hover:bg-surface-50 text-surface-700 font-semibold text-xs shadow-2xs transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Configuration</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
