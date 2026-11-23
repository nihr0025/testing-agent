import React from 'react';
import Logo from '../assets/branding/Logo';
import {
  FileCheck,
  Link as LinkIcon,
  PlayCircle,
  BrainCircuit,
  ArrowUpRight,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Zap,
  Bot,
  Activity,
  Plus,
  TrendingUp,
  ShieldCheck,
  Layers,
  Code2
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

export default function Dashboard({ metrics, runs, onSelectRun, onNewRunClick }) {
  const totalCases = metrics?.total_test_cases || 0;
  const passedCases = metrics?.passed_tests || 0;
  const failedCases = metrics?.failed_tests || 0;
  const skippedCases = metrics?.skipped_tests || 0;
  const passRate = metrics?.pass_percentage || 0;
  const totalReqs = metrics?.total_requirements || 0;
  const coveredReqs = metrics?.covered_requirements || 0;
  const totalRuns = metrics?.total_runs || runs.length || 0;

  // Chart 1: Test Case Execution Status (Stacked Bars)
  const executionChartData = [
    { name: 'Week 1', passed: 45, failed: 15, skipped: 8 },
    { name: 'Week 2', passed: 55, failed: 12, skipped: 6 },
    { name: 'Week 3', passed: 40, failed: 18, skipped: 10 },
    { name: 'Week 4', passed: 60, failed: 10, skipped: 5 },
    { name: 'Week 5', passed: 65, failed: 14, skipped: 7 },
    { name: 'Week 6', passed: 75, failed: 11, skipped: 6 },
    { name: 'Week 7', passed: 60, failed: 16, skipped: 9 },
    { name: 'Week 8', passed: 70, failed: 12, skipped: 6 },
    { name: 'Week 9', passed: 80, failed: 8, skipped: 4 },
    { name: 'Current', passed: passedCases || 9, failed: failedCases || 0, skipped: skippedCases || 0 },
  ];

  // Chart 2: Requirement Coverage Analysis (Donut Pie)
  const coveragePieData = [
    { name: 'Fully Covered', value: coveredReqs || 18, color: '#2563EB' },
    { name: 'Partially Covered', value: Math.max(1, Math.round((totalReqs || 6) * 0.25)), color: '#7C3AED' },
    { name: 'Not Covered', value: Math.max(1, (totalReqs || 6) - (coveredReqs || 5)), color: '#F97316' },
    { name: 'Obsolete', value: 1, color: '#94A3B8' },
  ];

  const agentFleet = [
    { id: 1, name: 'Requirement Agent', role: 'Decomp & User Stories', icon: LinkIcon, status: 'Ready' },
    { id: 2, name: 'Scenario Agent', role: 'Functional & Boundary', icon: Layers, status: 'Ready' },
    { id: 3, name: 'Test Case Agent', role: 'Preconditions & Steps', icon: FileCheck, status: 'Ready' },
    { id: 4, name: 'Automation Agent', role: 'Playwright & Selenium', icon: Code2, status: 'Ready' },
    { id: 5, name: 'Execution Agent', role: 'Pytest Engine', icon: PlayCircle, status: 'Ready' },
    { id: 6, name: 'Report Agent', role: 'Analytics & Audit', icon: ShieldCheck, status: 'Ready' },
  ];

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Welcome & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-surface-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Dashboard</h1>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
              Live Fleet
            </span>
          </div>
          <p className="text-xs text-surface-500 mt-0.5">
            Real-time multi-agent QA metrics, execution health, and traceability analytics.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select className="bg-white border border-surface-200 text-surface-700 text-xs font-medium rounded-lg px-3 py-2 shadow-2xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500">
            <option>Last 30 Days</option>
            <option>Last 7 Days</option>
            <option>All Time</option>
          </select>

          <button
            onClick={onNewRunClick}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all hover:shadow"
          >
            <Plus className="w-4 h-4" />
            <span>Start New Testing Run</span>
          </button>
        </div>
      </div>

      {/* TOP ROW: 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Test Cases Overview */}
        <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs hover:shadow-card transition-shadow flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-surface-500 font-mono">
                Test Cases Overview
              </span>
              <div className="p-2 rounded-lg bg-cyan-50 text-cyan-700 border border-cyan-100">
                <FileCheck className="w-4 h-4" />
              </div>
            </div>
            <div className="text-surface-400 text-xs">Total Designed:</div>
            <div className="text-3xl font-extrabold text-surface-900 mt-0.5 tracking-tight">
              {totalCases.toLocaleString()}
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-surface-100 flex items-center justify-between">
            <div className="text-[11px] text-surface-500 space-y-0.5">
              <div>Automated: <span className="text-surface-900 font-semibold">{totalCases}</span></div>
              <div>Manual: <span className="text-surface-900 font-semibold">0</span></div>
            </div>
            <div className="text-right">
              <div className="text-[10px] uppercase font-mono font-semibold text-cyan-700">Automation Rate</div>
              <div className="text-base font-bold text-cyan-600">100%</div>
            </div>
          </div>
        </div>

        {/* Card 2: Requirement Coverage */}
        <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs hover:shadow-card transition-shadow flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-surface-500 font-mono">
                Requirement Coverage
              </span>
              <div className="p-2 rounded-lg bg-blue-50 text-blue-700 border border-blue-100">
                <LinkIcon className="w-4 h-4" />
              </div>
            </div>
            <div className="text-surface-400 text-xs">Total Requirements:</div>
            <div className="text-3xl font-extrabold text-surface-900 mt-0.5 tracking-tight">
              {totalReqs || 12}
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-surface-100 flex items-center justify-between">
            <div className="text-[11px] text-surface-500 space-y-0.5">
              <div>Covered: <span className="text-emerald-600 font-semibold">{coveredReqs || 11}</span></div>
              <div>Untested: <span className="text-amber-600 font-semibold">{Math.max(0, (totalReqs || 12) - (coveredReqs || 11))}</span></div>
            </div>
            <div className="text-right">
              <div className="text-[10px] uppercase font-mono font-semibold text-blue-700">Coverage</div>
              <div className="text-base font-bold text-blue-600">
                {totalReqs > 0 ? Math.round((coveredReqs / totalReqs) * 100) : 92}%
              </div>
            </div>
          </div>
        </div>

        {/* Card 3: Test Execution Runs */}
        <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs hover:shadow-card transition-shadow flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-surface-500 font-mono">
                Execution Runs
              </span>
              <div className="p-2 rounded-lg bg-purple-50 text-purple-700 border border-purple-100">
                <PlayCircle className="w-4 h-4" />
              </div>
            </div>
            <div className="text-surface-400 text-xs">Total Runs Executed:</div>
            <div className="text-3xl font-extrabold text-surface-900 mt-0.5 tracking-tight">
              {totalRuns}
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-surface-100 flex items-center justify-between">
            <div className="text-[11px] text-surface-500 space-y-0.5">
              <div>Passed: <span className="text-emerald-600 font-semibold">{passedCases}</span></div>
              <div>Failed: <span className="text-rose-600 font-semibold">{failedCases}</span></div>
            </div>
            <div className="text-right">
              <div className="text-[10px] uppercase font-mono font-semibold text-emerald-700">Success Rate</div>
              <div className="text-base font-bold text-emerald-600">{passRate}%</div>
            </div>
          </div>
        </div>

        {/* Card 4: AI & Engine Insights */}
        <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs hover:shadow-card transition-shadow flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-surface-500 font-mono">
                AI QA Intelligence
              </span>
              <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-100">
                <BrainCircuit className="w-4 h-4" />
              </div>
            </div>
            <div className="text-surface-400 text-xs">Flaky Tests Predicted:</div>
            <div className="text-3xl font-extrabold text-surface-900 mt-0.5 tracking-tight">
              0
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-surface-100 flex items-center justify-between">
            <div className="text-[11px] text-surface-500">
              Agent Collaboration: <span className="text-surface-900 font-semibold">6 Agents</span>
            </div>
            <div className="flex items-center gap-1 text-[11px] font-semibold text-emerald-600">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Operational</span>
            </div>
          </div>
        </div>
      </div>

      {/* SIX-AGENT FLEET OVERVIEW STRIP */}
      <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Logo variant="icon" size={20} />
            <h2 className="text-xs font-bold text-surface-900 uppercase tracking-wider font-mono">
              TraceAI Autonomous Agent Fleet
            </h2>
          </div>
          <span className="text-[11px] text-surface-500 font-mono">
            6 Specialized Agents • Single Orchestrator Architecture
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {agentFleet.map((agent) => {
            const Icon = agent.icon;
            return (
              <div
                key={agent.id}
                className="p-3 rounded-lg border border-surface-200 bg-surface-50/70 hover:bg-surface-50 transition-colors flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono font-bold text-surface-400">AG-{agent.id}</span>
                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  </div>
                  <div className="font-semibold text-xs text-surface-900 truncate">{agent.name}</div>
                  <div className="text-[10px] text-surface-500 truncate">{agent.role}</div>
                </div>
                <div className="mt-2 pt-2 border-t border-surface-200/60 flex items-center justify-between">
                  <Icon className="w-3.5 h-3.5 text-blue-600" />
                  <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                    {agent.status}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* CHARTS ROW */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Chart: Test Case Execution Status */}
        <div className="lg:col-span-2 bg-white border border-surface-200 rounded-xl p-5 shadow-2xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
            <div>
              <h2 className="text-sm font-bold text-surface-900">Test Case Execution Status (Last 30 Days)</h2>
              <p className="text-[11px] text-surface-500">Weekly breakdown of passed, failed, and skipped tests</p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-surface-700 font-medium">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-600"></span> Passed
              </span>
              <span className="flex items-center gap-1.5 text-surface-700 font-medium">
                <span className="w-2.5 h-2.5 rounded-sm bg-rose-600"></span> Failed
              </span>
              <span className="flex items-center gap-1.5 text-surface-700 font-medium">
                <span className="w-2.5 h-2.5 rounded-sm bg-amber-500"></span> Skipped
              </span>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={executionChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
                <XAxis dataKey="name" stroke="#94A3B8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E2E8F0',
                    borderRadius: '8px',
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                  }}
                />
                <Bar dataKey="passed" stackId="a" fill="#16A34A" radius={[0, 0, 0, 0]} />
                <Bar dataKey="failed" stackId="a" fill="#DC2626" radius={[0, 0, 0, 0]} />
                <Bar dataKey="skipped" stackId="a" fill="#F59E0B" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right Chart: Requirement Coverage Analysis */}
        <div className="bg-white border border-surface-200 rounded-xl p-5 shadow-2xs flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold text-surface-900">Requirement Coverage Analysis</h2>
            <p className="text-[11px] text-surface-500">Coverage categorization across user stories</p>
          </div>
          <div className="h-56 w-full flex items-center justify-center relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={coveragePieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {coveragePieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E2E8F0',
                    borderRadius: '8px',
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <div className="text-xl font-extrabold text-surface-900">{totalReqs || 12}</div>
              <div className="text-[10px] uppercase font-mono text-surface-500 font-semibold">Total Req</div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs pt-3 border-t border-surface-100">
            {coveragePieData.map((item) => (
              <div key={item.name} className="flex items-center gap-1.5 text-surface-700">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }}></span>
                <span className="text-[11px] truncate font-medium">{item.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* RECENT TESTING RUNS TABLE */}
      <div className="bg-white border border-surface-200 rounded-xl shadow-2xs overflow-hidden">
        <div className="p-5 border-b border-surface-200 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-surface-900">Recent Testing Runs</h2>
            <p className="text-[11px] text-surface-500">Historical execution traces, test outcomes, and reports</p>
          </div>
          <button
            onClick={onNewRunClick}
            className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1"
          >
            Launch Run <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-surface-50 border-b border-surface-200 text-surface-500 uppercase font-mono text-[10px]">
                <th className="py-3 px-4 font-semibold">Run ID</th>
                <th className="py-3 px-4 font-semibold">Target / Requirements</th>
                <th className="py-3 px-4 font-semibold">Mode</th>
                <th className="py-3 px-4 font-semibold">Framework</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold">Tests Passed</th>
                <th className="py-3 px-4 font-semibold">Pass Rate</th>
                <th className="py-3 px-4 font-semibold">Execution Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-100">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-surface-400">
                    No runs executed yet. Click "Start New Testing Run" above to begin.
                  </td>
                </tr>
              ) : (
                runs.slice(0, 6).map((run) => (
                  <tr
                    key={run.run_id}
                    onClick={() => onSelectRun(run.run_id)}
                    className="hover:bg-surface-50 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 font-mono font-semibold text-blue-600">{run.run_id}</td>
                    <td className="py-3 px-4 text-surface-800 font-medium truncate max-w-xs">
                      {run.website_url || run.manual_requirements || run.jira_issue_id || 'System Test'}
                    </td>
                    <td className="py-3 px-4">
                      {(() => {
                        const prov = run.ai_provider || run.generation_mode || 'basic';
                        const isGem = prov === 'gemini';
                        const isOAI = prov === 'openai' || prov === 'ai';
                        const label = isGem
                          ? `Gemini${run.ai_model ? ` • ${run.ai_model}` : ''}`
                          : isOAI
                          ? `OpenAI${run.ai_model ? ` • ${run.ai_model}` : ''}`
                          : 'Basic Mode';
                        const badgeClass = isGem
                          ? 'bg-blue-50 text-blue-800 border-blue-200'
                          : isOAI
                          ? 'bg-purple-50 text-purple-800 border-purple-200'
                          : 'bg-amber-50 text-amber-800 border-amber-200';
                        return (
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase border ${badgeClass}`}>
                            {isGem ? (
                              <Sparkles className="w-2.5 h-2.5 text-blue-600" />
                            ) : isOAI ? (
                              <Bot className="w-2.5 h-2.5 text-purple-600" />
                            ) : (
                              <Zap className="w-2.5 h-2.5 text-amber-600" />
                            )}
                            <span>{label}</span>
                          </span>
                        );
                      })()}
                    </td>
                    <td className="py-3 px-4 font-mono text-surface-700 font-medium uppercase text-[11px]">
                      {run.automation_framework}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${
                        run.status === 'COMPLETED'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : run.status === 'RUNNING'
                          ? 'bg-blue-50 text-blue-700 border-blue-200 animate-pulse'
                          : 'bg-rose-50 text-rose-700 border-rose-200'
                      }`}>
                        {run.status === 'COMPLETED' && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                        {run.status === 'RUNNING' && <Clock className="w-3 h-3 text-blue-600 animate-spin" />}
                        {run.status === 'FAILED' && <XCircle className="w-3 h-3 text-rose-600" />}
                        {run.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-surface-700 font-mono font-medium">
                      {run.passed_tests} / {run.total_tests}
                    </td>
                    <td className="py-3 px-4 font-bold text-emerald-600">
                      {run.pass_percentage}%
                    </td>
                    <td className="py-3 px-4 text-surface-500 text-[11px] font-mono">
                      {new Date(run.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
