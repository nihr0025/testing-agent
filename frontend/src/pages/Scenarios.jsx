import React, { useState, useEffect } from 'react';
import {
  Network,
  Filter,
  ArrowRight,
  Tag,
  Layers,
  Search,
  Zap,
  Bot
} from 'lucide-react';
import { api } from '../services/api';

export default function Scenarios({ activeRunId, onNavigateToTestCases }) {
  const [scenarios, setScenarios] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeRunId) return;
    setLoading(true);
    api.getRunScenarios(activeRunId)
      .then((data) => setScenarios(data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [activeRunId]);

  const filteredScenarios = scenarios.filter((s) => {
    const matchesSearch =
      s.scenario_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.req_id?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'ALL' || s.scenario_type?.toUpperCase() === typeFilter;
    const matchesPriority = priorityFilter === 'ALL' || s.priority?.toUpperCase() === priorityFilter;
    return matchesSearch && matchesType && matchesPriority;
  });

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Test Scenarios</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
              AGENT 2
            </span>
          </div>
          <p className="text-xs text-surface-500 mt-1">
            Synthesized by Agent 2 (Test Scenario Generation Agent) covering functional, negative, boundary, and navigation flows.
          </p>
        </div>

        <button
          onClick={onNavigateToTestCases}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all"
        >
          <span>View Test Cases</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="bg-white border border-surface-200 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-3 shadow-2xs">
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-surface-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search scenarios or Req ID..."
            className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Type Filter */}
          <div className="flex items-center gap-1.5 text-xs text-surface-500">
            <span>Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-surface-50 border border-surface-200 text-surface-800 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-medium"
            >
              <option value="ALL">All Types</option>
              <option value="FUNCTIONAL">Functional</option>
              <option value="NEGATIVE">Negative</option>
              <option value="BOUNDARY">Boundary</option>
              <option value="INTEGRATION">Integration</option>
              <option value="NAVIGATION">Navigation</option>
            </select>
          </div>

          {/* Priority Filter */}
          <div className="flex items-center gap-1.5 text-xs text-surface-500">
            <span>Priority:</span>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-surface-50 border border-surface-200 text-surface-800 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-medium"
            >
              <option value="ALL">All Priorities</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Scenarios Grid */}
      {loading ? (
        <div className="py-20 text-center text-surface-400 text-xs font-mono">Loading scenarios...</div>
      ) : filteredScenarios.length === 0 ? (
        <div className="py-20 text-center bg-white border border-surface-200 rounded-xl text-surface-400 text-xs shadow-2xs">
          No scenarios matching the selected filters.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredScenarios.map((sc) => (
            <div
              key={sc.scenario_id}
              className="bg-white border border-surface-200 rounded-xl p-5 flex flex-col justify-between shadow-2xs hover:shadow-card transition-shadow space-y-4"
            >
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded font-mono text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200 shadow-2xs">
                      {sc.scenario_id}
                    </span>
                    <span className="text-[10px] font-mono font-medium text-surface-500 bg-surface-100 px-1.5 py-0.5 rounded">
                      Req: {sc.req_id}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-semibold uppercase border ${
                      sc.generation_mode === 'basic'
                        ? 'bg-amber-50 text-amber-800 border-amber-200'
                        : 'bg-purple-50 text-purple-800 border-purple-200'
                    }`}>
                      {sc.generation_mode === 'basic' ? 'Basic' : 'AI'}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                      sc.scenario_type === 'Negative'
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : sc.scenario_type === 'Boundary'
                        ? 'bg-amber-50 text-amber-700 border-amber-200'
                        : sc.scenario_type === 'Integration' || sc.scenario_type === 'Navigation'
                        ? 'bg-purple-50 text-purple-700 border-purple-200'
                        : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    }`}>
                      {sc.scenario_type}
                    </span>
                  </div>
                </div>

                <h3 className="text-sm font-bold text-surface-900 tracking-tight leading-snug">
                  {sc.title}
                </h3>
                <p className="text-xs text-surface-600 mt-2 leading-relaxed">
                  {sc.description}
                </p>
              </div>

              <div className="pt-3 border-t border-surface-100">
                <div className="text-[10px] uppercase font-mono text-surface-400 font-semibold mb-1">
                  Expected Behavior:
                </div>
                <div className="text-xs text-surface-700 font-medium leading-relaxed bg-surface-50 p-3 rounded-lg border border-surface-200/70">
                  {sc.expected_behavior || 'System behaves gracefully and maintains data integrity.'}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
