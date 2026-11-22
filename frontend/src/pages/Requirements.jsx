import React, { useState, useEffect } from 'react';
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Tag,
  ArrowRight,
  Zap,
  Bot,
  Search,
  Filter,
  Check
} from 'lucide-react';
import { api } from '../services/api';

export default function Requirements({ activeRunId, onNavigateToScenarios }) {
  const [requirements, setRequirements] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeRunId) return;
    setLoading(true);
    api.getRunRequirements(activeRunId)
      .then((data) => setRequirements(data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [activeRunId]);

  const filteredRequirements = requirements.filter((req) => {
    const matchesSearch =
      req.req_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      req.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesPriority =
      priorityFilter === 'ALL' || req.priority?.toUpperCase() === priorityFilter;
    return matchesSearch && matchesPriority;
  });

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Structured Requirements</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200">
              AGENT 1
            </span>
          </div>
          <p className="text-xs text-surface-500 mt-1">
            Synthesized by Agent 1 (Requirement Analysis Agent) via MCP Jira extraction or accessible DOM structure.
          </p>
        </div>

        <button
          onClick={onNavigateToScenarios}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all"
        >
          <span>View Test Scenarios</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="bg-white border border-surface-200 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-2xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-surface-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search requirements by ID or text..."
            className="w-full bg-surface-50 border border-surface-200 text-surface-900 text-xs rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <span className="text-xs text-surface-500 font-medium whitespace-nowrap">Filter Priority:</span>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-surface-50 border border-surface-200 text-surface-800 text-xs rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-medium"
          >
            <option value="ALL">All Priorities</option>
            <option value="HIGH">High Priority</option>
            <option value="MEDIUM">Medium Priority</option>
            <option value="LOW">Low Priority</option>
          </select>
        </div>
      </div>

      {/* Requirements List */}
      {loading ? (
        <div className="py-20 text-center text-surface-400 text-xs font-mono">Loading requirements...</div>
      ) : filteredRequirements.length === 0 ? (
        <div className="py-20 text-center bg-white border border-surface-200 rounded-xl text-surface-400 text-xs shadow-2xs">
          {requirements.length === 0
            ? 'No requirements found for the current run. Please initiate a testing run first.'
            : 'No requirements matching the filter criteria.'}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredRequirements.map((req) => {
            const isBasic = req.generation_mode === 'basic';
            return (
              <div
                key={req.req_id}
                className="bg-white border border-surface-200 rounded-xl p-5 md:p-6 space-y-4 shadow-2xs hover:shadow-card transition-shadow"
              >
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 font-mono text-xs font-bold shadow-2xs">
                      {req.req_id}
                    </span>
                    <h3 className="text-sm md:text-base font-bold text-surface-900 tracking-tight">
                      {req.description}
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase border ${
                      isBasic
                        ? 'bg-amber-50 text-amber-800 border-amber-200'
                        : 'bg-purple-50 text-purple-800 border-purple-200'
                    }`}>
                      {isBasic ? <Zap className="w-2.5 h-2.5 text-amber-600" /> : <Bot className="w-2.5 h-2.5 text-purple-600" />}
                      <span>{isBasic ? 'Basic Mode' : 'AI-Generated'}</span>
                    </span>

                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                      req.priority === 'High'
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : 'bg-amber-50 text-amber-700 border-amber-200'
                    }`}>
                      {req.priority || 'Medium'} Priority
                    </span>
                  </div>
                </div>

                {/* Acceptance Criteria & Business Rules */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                  {/* Acceptance Criteria */}
                  <div className="bg-surface-50 rounded-xl p-4 border border-surface-200/80">
                    <h4 className="text-xs font-bold text-surface-700 uppercase font-mono tracking-wider mb-2.5 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>Acceptance Criteria</span>
                    </h4>
                    <ul className="space-y-2 text-xs text-surface-700">
                      {(Array.isArray(req.acceptance_criteria) ? req.acceptance_criteria : []).map((ac, i) => (
                        <li key={i} className="flex items-start gap-2 leading-relaxed">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 shrink-0"></span>
                          <span>{ac}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Business Rules */}
                  <div className="bg-surface-50 rounded-xl p-4 border border-surface-200/80">
                    <h4 className="text-xs font-bold text-surface-700 uppercase font-mono tracking-wider mb-2.5 flex items-center gap-1.5">
                      <ShieldAlert className="w-4 h-4 text-purple-600" />
                      <span>Business Rules &amp; Constraints</span>
                    </h4>
                    <ul className="space-y-2 text-xs text-surface-700">
                      {(Array.isArray(req.business_rules) ? req.business_rules : []).map((br, i) => (
                        <li key={i} className="flex items-start gap-2 leading-relaxed">
                          <span className="w-1.5 h-1.5 rounded-full bg-purple-600 mt-1.5 shrink-0"></span>
                          <span>{br}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Missing Information / Ambiguities */}
                {Array.isArray(req.missing_information) && req.missing_information.length > 0 && (
                  <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-2.5">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
                    <div>
                      <strong className="font-bold block text-amber-950">Missing or Ambiguous Requirements Flagged:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-0.5 text-[11px] text-amber-800">
                        {req.missing_information.map((m, i) => (
                          <li key={i}>{m}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
