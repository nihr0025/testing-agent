import React, { useState, useEffect } from 'react';
import Logo from '../assets/branding/Logo';
import {
  BrainCircuit,
  CheckCircle2,
  Clock,
  XCircle,
  Code2,
  ChevronRight,
  Eye,
  RefreshCw,
  Sparkles,
  Zap,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  Bot,
  Layers,
  FileCheck,
  Link as LinkIcon,
  PlayCircle,
  Terminal,
  Activity,
  FileText,
  Workflow,
  Radio,
  Cpu
} from 'lucide-react';
import { api } from '../services/api';

export default function AgentWorkflow({ activeRunId, runData, onNavigatePage }) {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [activeTab, setActiveTab] = useState('output'); // 'output' | 'info' | 'log'
  const [polling, setPolling] = useState(true);

  const fetchAgentStates = async () => {
    if (!activeRunId) return;
    try {
      const res = await api.getRunAgents(activeRunId);
      if (res?.agents) {
        setAgents(res.agents);
        if (!selectedAgent) {
          const activeOrFirst = res.agents.find(a => a.status === 'RUNNING') || res.agents[0];
          setSelectedAgent(activeOrFirst);
        } else {
          // Update selected agent reference with latest data
          const updated = res.agents.find(a => a.agent_name === selectedAgent.agent_name);
          if (updated) setSelectedAgent(updated);
        }
      }
    } catch (_) {}
  };

  useEffect(() => {
    fetchAgentStates();
    if (!polling || !activeRunId) return;

    const interval = setInterval(() => {
      fetchAgentStates();
    }, 2000);

    return () => clearInterval(interval);
  }, [activeRunId, polling]);

  const provider = runData?.ai_provider || runData?.generation_mode || 'basic';
  const isGemini = provider === 'gemini';
  const isAi = provider === 'openai' || provider === 'ai';
  const isBasicMode = !isGemini && !isAi;
  const modelName = runData?.ai_model;
  const framework = runData?.automation_framework?.toUpperCase() || 'PLAYWRIGHT';

  const agentMeta = {
    requirement_agent: {
      order: 1,
      name: 'Requirement Analysis Agent',
      shortName: 'Agent 1',
      icon: LinkIcon,
      color: 'blue',
      taskDescription: isBasicMode
        ? 'Inspects website DOM controls (forms, links, buttons, inputs) and builds structured requirements.'
        : isGemini
        ? `Connects to Jira MCP / extracts user stories and acceptance criteria via Gemini reasoning (${modelName || 'Selected Model'}).`
        : `Connects to Jira MCP / extracts user stories and acceptance criteria via OpenAI reasoning (${modelName || 'Selected Model'}).`,
      page: 'requirements',
      pageLabel: 'View Requirements'
    },
    scenario_agent: {
      order: 2,
      name: 'Test Scenario Generation Agent',
      shortName: 'Agent 2',
      icon: Layers,
      color: 'indigo',
      taskDescription: isBasicMode
        ? 'Generates Functional, Negative, and Navigation test scenarios based on inspected DOM elements.'
        : 'Synthesizes exploratory, boundary, and edge-case testing scenarios mapped to requirement IDs.',
      page: 'scenarios',
      pageLabel: 'View Scenarios'
    },
    testcase_agent: {
      order: 3,
      name: 'Test Case Design Agent',
      shortName: 'Agent 3',
      icon: FileCheck,
      color: 'cyan',
      taskDescription: isBasicMode
        ? 'Designs detailed step-by-step test cases, preconditions, and test data for each scenario.'
        : 'Generates step-by-step test cases with expected results, assertions, and traceability.',
      page: 'test_cases',
      pageLabel: 'View Test Cases'
    },
    automation_agent: {
      order: 4,
      name: 'Test Automation Agent',
      shortName: 'Agent 4',
      icon: Code2,
      color: 'violet',
      taskDescription: `Generates executable ${framework} test automation scripts using robust locators and assertions.`,
      page: 'execution',
      pageLabel: 'View Generated Scripts'
    },
    execution_agent: {
      order: 5,
      name: 'Test Execution Agent',
      shortName: 'Agent 5',
      icon: PlayCircle,
      color: 'amber',
      taskDescription: 'Executes pytest test suite in browser, capturing real-time logs, durations, and screenshots.',
      page: 'execution',
      pageLabel: 'View Execution Runs'
    },
    orchestrator_agent: {
      order: 6,
      name: 'Report Generation Agent',
      shortName: 'Agent 6',
      icon: ShieldCheck,
      color: 'emerald',
      taskDescription: 'Consolidates test outcomes, calculates pass rates, and compiles executive audit reports.',
      page: 'reports',
      pageLabel: 'View Audit Report'
    }
  };

  const completedCount = agents.filter(a => a.status === 'COMPLETED').length;
  const runningCount = agents.filter(a => a.status === 'RUNNING').length;
  const failedCount = agents.filter(a => a.status === 'FAILED').length;
  const progressPercent = agents.length > 0 ? Math.round((completedCount / agents.length) * 100) : 0;

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-200">
        <div>
          <div className="flex items-center gap-2.5 flex-wrap">
            <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Agent Command Center</h1>
            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold border ${
              isGemini
                ? 'bg-blue-50 text-blue-800 border-blue-200'
                : isAi
                ? 'bg-purple-50 text-purple-800 border-purple-200'
                : 'bg-amber-50 text-amber-800 border-amber-200'
            }`}>
              {isGemini ? (
                <>
                  <Sparkles className="w-3 h-3 text-blue-600" />
                  <span>GEMINI{modelName ? ` — ${modelName}` : ''}</span>
                </>
              ) : isAi ? (
                <>
                  <Bot className="w-3 h-3 text-purple-600" />
                  <span>OPENAI{modelName ? ` — ${modelName}` : ''}</span>
                </>
              ) : (
                <>
                  <Zap className="w-3 h-3 text-amber-600" />
                  <span>BASIC TESTING MODE</span>
                </>
              )}
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-blue-50 text-blue-700 border border-blue-200">
              {framework}
            </span>
          </div>
          <p className="text-xs text-surface-500 mt-1">
            Real-time visual orchestration pipeline connecting the 6 specialized AI testing agents.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-surface-200 shadow-2xs text-xs font-mono">
            <span className="text-surface-400">Progress:</span>
            <span className="font-bold text-surface-900">{completedCount}/6 Done</span>
            <div className="w-20 bg-surface-100 rounded-full h-2 overflow-hidden ml-1">
              <div
                className="bg-blue-600 h-full rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          <button
            onClick={fetchAgentStates}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-surface-200 text-xs font-medium text-surface-700 hover:text-surface-900 hover:bg-surface-50 shadow-2xs transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Notice Banner if Fallback / Basic Mode */}
      {runData?.mode_reason && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-3 shadow-2xs">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
          <div>
            <span className="font-bold block text-amber-950">Mode Reason</span>
            <span className="text-[11px] text-amber-800 leading-relaxed">
              {runData.mode_reason} All six agents are cooperating in Basic Mode using deterministic heuristics.
            </span>
          </div>
        </div>
      )}

      {/* SIGNATURE VISUAL WORKFLOW BLUEPRINT DIAGRAM */}
      <div className="bg-white border border-surface-200 rounded-2xl p-6 shadow-sm relative overflow-hidden bg-blueprint">
        {/* Orchestrator Master Header Bar */}
        <div className="bg-white/95 backdrop-blur-xs border border-surface-200 rounded-xl p-4 mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-2xs">
          <div className="flex items-center gap-3">
            <div className="shrink-0">
              <Logo variant="icon" size={42} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-surface-900 text-sm">TraceAI Master Orchestrator</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  COORDINATOR
                </span>
              </div>
              <p className="text-[11px] text-surface-500">
                Target: <span className="font-mono text-surface-700 font-medium">{runData?.website_url || runData?.jira_issue_id || runData?.manual_requirements || 'Interactive Target'}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              <span className="text-surface-600 font-medium">Completed ({completedCount})</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse"></span>
              <span className="text-surface-600 font-medium">Working ({runningCount})</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-surface-300"></span>
              <span className="text-surface-600 font-medium">Idle ({Math.max(0, 6 - completedCount - runningCount - failedCount)})</span>
            </div>
            {failedCount > 0 && (
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                <span className="text-rose-600 font-medium">Failed ({failedCount})</span>
              </div>
            )}
          </div>
        </div>

        {/* The 6 Agents Pipeline Cards Connected Horizontally / Responsive */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3.5 relative">
          {agents.map((agent, index) => {
            const meta = agentMeta[agent.agent_name] || {
              order: index + 1,
              name: agent.display_name,
              shortName: `Agent ${index + 1}`,
              icon: Bot,
              taskDescription: 'Testing task'
            };
            const Icon = meta.icon;
            const isSelected = selectedAgent?.agent_name === agent.agent_name;
            const isCompleted = agent.status === 'COMPLETED';
            const isRunning = agent.status === 'RUNNING';
            const isFailed = agent.status === 'FAILED';
            const isIdle = !isCompleted && !isRunning && !isFailed;

            return (
              <div
                key={agent.agent_name}
                onClick={() => setSelectedAgent(agent)}
                className={`relative rounded-xl p-4 cursor-pointer transition-all flex flex-col justify-between bg-white border ${
                  isSelected
                    ? 'border-blue-500 shadow-md ring-2 ring-blue-500/20 translate-y-[-2px]'
                    : isCompleted
                    ? 'border-emerald-200 hover:border-emerald-300 shadow-2xs'
                    : isRunning
                    ? 'border-blue-400 shadow-2xs ring-2 ring-blue-400/20'
                    : isFailed
                    ? 'border-rose-200 hover:border-rose-300 shadow-2xs'
                    : 'border-surface-200 hover:border-surface-300 shadow-2xs opacity-85'
                }`}
              >
                {/* Arrow connector to next agent (desktop) */}
                {index < agents.length - 1 && (
                  <div className="hidden xl:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-white border border-surface-200 text-surface-400 items-center justify-center shadow-2xs">
                    <ChevronRight className="w-3.5 h-3.5" />
                  </div>
                )}

                <div>
                  {/* Top Node Header: Order & Status */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="w-6 h-6 rounded-lg bg-surface-100 text-surface-700 font-mono text-xs flex items-center justify-center font-bold">
                      0{index + 1}
                    </span>

                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                      isCompleted
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : isRunning
                        ? 'bg-blue-50 text-blue-700 border-blue-200 animate-pulse'
                        : isFailed
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : 'bg-surface-100 text-surface-500 border-surface-200'
                    }`}>
                      {isCompleted && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                      {isRunning && <Clock className="w-3 h-3 text-blue-600 animate-spin" />}
                      {isFailed && <XCircle className="w-3 h-3 text-rose-600" />}
                      {isIdle && <span className="w-1.5 h-1.5 rounded-full bg-surface-400"></span>}
                      {agent.status}
                    </span>
                  </div>

                  {/* Agent Icon & Name */}
                  <div className="flex items-center gap-2 mb-1.5">
                    <div className={`p-1.5 rounded-lg ${
                      isCompleted ? 'bg-emerald-50 text-emerald-600' :
                      isRunning ? 'bg-blue-50 text-blue-600' :
                      isFailed ? 'bg-rose-50 text-rose-600' :
                      'bg-surface-100 text-surface-500'
                    }`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] font-mono uppercase font-semibold text-surface-400">
                      {meta.shortName}
                    </span>
                  </div>

                  <h3 className="text-xs font-bold text-surface-900 leading-snug">
                    {agent.display_name}
                  </h3>

                  <p className="text-[11px] text-surface-500 mt-1.5 line-clamp-3 leading-relaxed">
                    {meta.taskDescription}
                  </p>

                  {/* Reliability & Failover Metadata Badges */}
                  {(agent.retries_count > 0 || (agent.actual_model && agent.actual_model !== agent.selected_model) || agent.error_category) && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {agent.retries_count > 0 && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-amber-50 text-amber-700 border border-amber-200">
                          {agent.retries_count} {agent.retries_count === 1 ? 'retry' : 'retries'}
                        </span>
                      )}
                      {agent.actual_model && agent.actual_model !== agent.selected_model && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200" title={`Failover from ${agent.selected_model} to ${agent.actual_model}`}>
                          Alt: {agent.actual_model}
                        </span>
                      )}
                      {agent.error_category && agent.status === 'FAILED' && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200">
                          {agent.error_category}
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Card Footer: Timestamp & Inspect Indicator */}
                <div className="mt-3 pt-2.5 border-t border-surface-100 flex items-center justify-between text-[10px]">
                  <span className="text-surface-400 font-mono truncate max-w-[90px]">
                    {agent.completed_at
                      ? `${new Date(agent.completed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`
                      : agent.started_at
                      ? `Running...`
                      : 'Pending'}
                  </span>
                  <span className={`font-semibold flex items-center gap-0.5 ${
                    isSelected ? 'text-blue-600' : 'text-surface-400'
                  }`}>
                    Inspect
                    <ChevronRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* SELECTED AGENT DETAILS & ACTIVITY LOG PANEL */}
      {selectedAgent && (
        <div className="bg-white border border-surface-200 rounded-xl shadow-sm overflow-hidden">
          {/* Header of Inspector */}
          <div className="p-5 border-b border-surface-200 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-surface-50/50">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center shrink-0">
                {React.createElement(agentMeta[selectedAgent.agent_name]?.icon || Bot, { className: 'w-5 h-5' })}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-surface-900">
                    {selectedAgent.display_name}
                  </h2>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                    selectedAgent.status === 'COMPLETED'
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : selectedAgent.status === 'RUNNING'
                      ? 'bg-blue-50 text-blue-700 border-blue-200 animate-pulse'
                      : selectedAgent.status === 'FAILED'
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : 'bg-surface-100 text-surface-500 border-surface-200'
                  }`}>
                    {selectedAgent.status}
                  </span>
                </div>
                <p className="text-xs text-surface-500 mt-0.5">
                  {agentMeta[selectedAgent.agent_name]?.taskDescription}
                </p>
              </div>
            </div>

            {/* Quick Actions & Navigation Button */}
            <div className="flex items-center gap-2.5">
              {agentMeta[selectedAgent.agent_name]?.page && (
                <button
                  onClick={() => onNavigatePage(agentMeta[selectedAgent.agent_name].page)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold text-xs border border-blue-200 transition-colors"
                >
                  <span>{agentMeta[selectedAgent.agent_name].pageLabel}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Inspector Tabs */}
          <div className="flex items-center px-5 border-b border-surface-200 gap-6 bg-white text-xs font-medium">
            <button
              onClick={() => setActiveTab('output')}
              className={`py-3 border-b-2 flex items-center gap-1.5 transition-colors ${
                activeTab === 'output'
                  ? 'border-blue-600 text-blue-600 font-bold'
                  : 'border-transparent text-surface-500 hover:text-surface-900'
              }`}
            >
              <Code2 className="w-4 h-4" />
              <span>Structured Output (JSON)</span>
            </button>

            <button
              onClick={() => setActiveTab('info')}
              className={`py-3 border-b-2 flex items-center gap-1.5 transition-colors ${
                activeTab === 'info'
                  ? 'border-blue-600 text-blue-600 font-bold'
                  : 'border-transparent text-surface-500 hover:text-surface-900'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>Agent Metadata & Timing</span>
            </button>

            <button
              onClick={() => setActiveTab('log')}
              className={`py-3 border-b-2 flex items-center gap-1.5 transition-colors ${
                activeTab === 'log'
                  ? 'border-blue-600 text-blue-600 font-bold'
                  : 'border-transparent text-surface-500 hover:text-surface-900'
              }`}
            >
              <Terminal className="w-4 h-4" />
              <span>Activity Log</span>
            </button>
          </div>

          {/* Inspector Body Content */}
          <div className="p-5">
            {activeTab === 'output' && (
              <div>
                {selectedAgent.error_message ? (
                  <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs space-y-2.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                        <span className="font-bold text-rose-900 text-sm">
                          Execution Blocked — Failure Isolated
                        </span>
                      </div>
                      {selectedAgent.error_category && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-100 text-rose-800 border border-rose-300">
                          {selectedAgent.error_category}
                        </span>
                      )}
                    </div>
                    <p className="font-mono text-[11px] bg-white/70 p-2.5 rounded-lg border border-rose-200 break-words leading-relaxed">
                      {selectedAgent.error_message}
                    </p>
                    <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] text-rose-700">
                      {selectedAgent.retries_count > 0 && (
                        <span>Retries Attempted: <strong>{selectedAgent.retries_count}</strong></span>
                      )}
                      {selectedAgent.selected_model && (
                        <span>Primary Model: <strong>{selectedAgent.selected_model}</strong></span>
                      )}
                      {selectedAgent.actual_model && selectedAgent.actual_model !== selectedAgent.selected_model && (
                        <span>Alternative Failover: <strong>{selectedAgent.actual_model}</strong></span>
                      )}
                    </div>
                    <div className="pt-2 border-t border-rose-200/80 text-[11px] text-rose-600 flex items-center gap-1.5 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      <span>Failure was safely isolated. Preceding agent artifacts remain fully preserved in database.</span>
                    </div>
                  </div>
                ) : selectedAgent.output_data ? (
                  <div className="relative">
                    <div className="flex items-center justify-between text-xs text-surface-500 mb-2 font-mono">
                      <span>Payload size: {JSON.stringify(selectedAgent.output_data).length} bytes</span>
                      <span className="text-[11px] text-surface-400">Read-only Structured Output</span>
                    </div>
                    <pre className="bg-surface-900 text-surface-100 p-4 rounded-xl text-xs font-mono overflow-x-auto max-h-96 border border-surface-800 shadow-inner">
                      {JSON.stringify(selectedAgent.output_data, null, 2)}
                    </pre>
                  </div>
                ) : (
                  <div className="py-12 text-center text-surface-400 text-xs">
                    Agent is currently awaiting dependent inputs or has not generated output yet.
                  </div>
                )}
              </div>
            )}

            {activeTab === 'info' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-surface-50 border border-surface-200 space-y-2.5">
                  <span className="font-bold text-surface-700 block uppercase font-mono text-[10px]">Timing & Lifecycle</span>
                  <div className="flex justify-between py-1 border-b border-surface-200/60">
                    <span className="text-surface-500">Started At:</span>
                    <span className="font-mono text-surface-800 font-medium">{selectedAgent.started_at ? new Date(selectedAgent.started_at).toLocaleString() : 'N/A'}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-surface-200/60">
                    <span className="text-surface-500">Completed At:</span>
                    <span className="font-mono text-surface-800 font-medium">{selectedAgent.completed_at ? new Date(selectedAgent.completed_at).toLocaleString() : 'N/A'}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-surface-500">Execution Status:</span>
                    <span className="font-mono font-bold text-surface-900">{selectedAgent.status}</span>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-surface-50 border border-surface-200 space-y-2.5">
                  <span className="font-bold text-surface-700 block uppercase font-mono text-[10px]">Intelligence &amp; Model Reliability</span>
                  <div className="flex justify-between py-1 border-b border-surface-200/60">
                    <span className="text-surface-500">Provider:</span>
                    <span className="font-mono text-surface-800 font-bold uppercase">{provider}</span>
                  </div>
                  {selectedAgent.selected_model && (
                    <div className="flex justify-between py-1 border-b border-surface-200/60">
                      <span className="text-surface-500">Selected Primary Model:</span>
                      <span className="font-mono text-surface-800 font-medium">{selectedAgent.selected_model}</span>
                    </div>
                  )}
                  {selectedAgent.actual_model && (
                    <div className="flex justify-between py-1 border-b border-surface-200/60">
                      <span className="text-surface-500">Actual Model Used:</span>
                      <span className={`font-mono font-bold ${
                        selectedAgent.actual_model !== selectedAgent.selected_model
                          ? 'text-blue-600'
                          : 'text-surface-800'
                      }`}>
                        {selectedAgent.actual_model}
                        {selectedAgent.actual_model !== selectedAgent.selected_model && ' (Failover)'}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between py-1 border-b border-surface-200/60">
                    <span className="text-surface-500">Total Retries:</span>
                    <span className="font-mono text-surface-800 font-bold">{selectedAgent.retries_count || 0}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-surface-200/60">
                    <span className="text-surface-500">Target Framework:</span>
                    <span className="font-mono text-surface-800 font-medium">{framework}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-surface-500">Downstream Consumer:</span>
                    <span className="font-mono text-surface-800 font-medium">
                      {agentMeta[selectedAgent.agent_name]?.order < 6
                        ? `Agent ${agentMeta[selectedAgent.agent_name]?.order + 1}`
                        : 'Final Audit Report'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'log' && (
              <div className="space-y-2">
                <div className="p-3 bg-surface-900 rounded-xl font-mono text-xs text-surface-200 space-y-1.5 max-h-72 overflow-y-auto">
                  <div className="text-surface-400">
                    [{new Date(selectedAgent.started_at || Date.now()).toISOString()}] [INFO] Orchestrator invoked {selectedAgent.agent_name}
                  </div>
                  {isBasicMode ? (
                    <div className="text-amber-400">
                      [{new Date(selectedAgent.started_at || Date.now()).toISOString()}] [MODE] Running in Basic Testing Mode with deterministic templates and page inspection
                    </div>
                  ) : (
                    <div className="text-purple-400">
                      [{new Date(selectedAgent.started_at || Date.now()).toISOString()}] [MODE] Running in AI-Powered Mode with OpenAI structured schema
                    </div>
                  )}
                  {selectedAgent.completed_at && (
                    <div className="text-emerald-400">
                      [{new Date(selectedAgent.completed_at).toISOString()}] [SUCCESS] Task completed successfully. Status: {selectedAgent.status}
                    </div>
                  )}
                  {selectedAgent.error_message && (
                    <div className="text-rose-400">
                      [{new Date().toISOString()}] [ERROR] {selectedAgent.error_message}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
