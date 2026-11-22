import React, { useState, useEffect } from 'react';
import {
  PlayCircle,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Terminal,
  Image as ImageIcon,
  X,
  ExternalLink,
  Filter
} from 'lucide-react';
import { api } from '../services/api';

export default function ExecutionResults({ activeRunId, onNavigateToReport }) {
  const [results, setResults] = useState([]);
  const [selectedLog, setSelectedLog] = useState(null);
  const [selectedScreenshot, setSelectedScreenshot] = useState(null);
  const [filter, setFilter] = useState('ALL');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeRunId) return;
    setLoading(true);
    api.getRunResults(activeRunId)
      .then((data) => setResults(data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [activeRunId]);

  const filtered = results.filter((r) => {
    if (filter === 'ALL') return true;
    return r.status?.toUpperCase() === filter;
  });

  const passedCount = results.filter(r => r.status === 'Passed').length;
  const failedCount = results.filter(r => r.status === 'Failed').length;
  const totalCount = results.length;
  const passRate = totalCount > 0 ? Math.round((passedCount / totalCount) * 100) : 0;

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Test Execution Results</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-700 border border-amber-200">
              AGENT 5 (PYTEST)
            </span>
          </div>
          <p className="text-xs text-surface-500 mt-1">
            Executed by Agent 5 (Test Execution Agent) via pytest runner with real-time browser traces.
          </p>
        </div>

        <button
          onClick={onNavigateToReport}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all"
        >
          <span>View Audit Report</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Summary KPI Cards Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-surface-200 rounded-xl p-4 shadow-2xs">
          <div className="text-[10px] uppercase font-mono text-surface-500 font-bold">Total Executed</div>
          <div className="text-2xl font-extrabold text-surface-900 mt-1">{totalCount}</div>
        </div>
        <div className="bg-white border border-surface-200 rounded-xl p-4 shadow-2xs">
          <div className="text-[10px] uppercase font-mono text-emerald-600 font-bold">Passed Tests</div>
          <div className="text-2xl font-extrabold text-emerald-600 mt-1">{passedCount}</div>
        </div>
        <div className="bg-white border border-surface-200 rounded-xl p-4 shadow-2xs">
          <div className="text-[10px] uppercase font-mono text-rose-600 font-bold">Failed Tests</div>
          <div className="text-2xl font-extrabold text-rose-600 mt-1">{failedCount}</div>
        </div>
        <div className="bg-white border border-surface-200 rounded-xl p-4 shadow-2xs">
          <div className="text-[10px] uppercase font-mono text-blue-600 font-bold">Success Rate</div>
          <div className="text-2xl font-extrabold text-blue-600 mt-1">{passRate}%</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-surface-200 pb-2">
        {['ALL', 'PASSED', 'FAILED'].map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              filter === tab
                ? 'bg-blue-50 text-blue-700 border border-blue-200 shadow-2xs'
                : 'text-surface-500 hover:text-surface-900 hover:bg-surface-100'
            }`}
          >
            {tab === 'ALL' ? `All Tests (${totalCount})` : tab === 'PASSED' ? `Passed (${passedCount})` : `Failed (${failedCount})`}
          </button>
        ))}
      </div>

      {/* Execution Results Table */}
      {loading ? (
        <div className="py-20 text-center text-surface-400 text-xs font-mono">Loading execution results...</div>
      ) : filtered.length === 0 ? (
        <div className="py-20 text-center bg-white border border-surface-200 rounded-xl text-surface-400 text-xs shadow-2xs">
          No execution results found for this run.
        </div>
      ) : (
        <div className="bg-white border border-surface-200 rounded-xl shadow-2xs overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-surface-50 border-b border-surface-200 text-surface-500 uppercase font-mono text-[10px]">
                <th className="py-3 px-4 font-semibold">Test Case ID</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold">Duration</th>
                <th className="py-3 px-4 font-semibold">Diagnostic Summary</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-100">
              {filtered.map((item) => {
                const isPassed = item.status === 'Passed';
                return (
                  <tr key={item.id || item.case_id} className="hover:bg-surface-50 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-blue-600">{item.case_id}</td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                        isPassed
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-rose-50 text-rose-700 border-rose-200'
                      }`}>
                        {isPassed ? <CheckCircle2 className="w-3 h-3 text-emerald-600" /> : <XCircle className="w-3 h-3 text-rose-600" />}
                        {item.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-surface-600 font-mono">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-surface-400" />
                        <span>{item.duration_sec}s</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-surface-700 max-w-md truncate font-medium">
                      {item.actual_result || item.error_message || 'Completed successfully'}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      {/* Live Logs Button */}
                      <button
                        onClick={() => setSelectedLog(item)}
                        className="px-2.5 py-1 rounded-lg bg-white border border-surface-200 text-surface-700 hover:text-blue-600 hover:border-blue-300 shadow-2xs transition-colors inline-flex items-center gap-1 text-[11px] font-medium"
                      >
                        <Terminal className="w-3 h-3 text-surface-500" />
                        <span>Logs</span>
                      </button>

                      {/* Screenshot Button */}
                      {item.screenshot_path && (
                        <button
                          onClick={() => setSelectedScreenshot(item.screenshot_path)}
                          className="px-2.5 py-1 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 hover:bg-rose-100 shadow-2xs transition-colors inline-flex items-center gap-1 text-[11px] font-medium"
                        >
                          <ImageIcon className="w-3 h-3 text-rose-600" />
                          <span>Screenshot</span>
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Logs Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-surface-200 rounded-2xl w-full max-w-3xl max-h-[80vh] flex flex-col shadow-elevation overflow-hidden">
            <div className="p-4 px-6 border-b border-surface-200 flex items-center justify-between bg-surface-50">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-surface-900">Execution Console Logs — {selectedLog.case_id}</h3>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="p-1 rounded-lg text-surface-400 hover:text-surface-700 hover:bg-surface-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-5 overflow-y-auto flex-1 font-mono text-xs bg-surface-900 text-surface-100 whitespace-pre-wrap leading-relaxed">
              {selectedLog.log_output || selectedLog.error_message || 'No additional logs captured.'}
            </div>
          </div>
        </div>
      )}

      {/* Screenshot Modal */}
      {selectedScreenshot && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-surface-200 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-elevation overflow-hidden">
            <div className="p-4 px-6 border-b border-surface-200 flex items-center justify-between bg-surface-50">
              <div className="flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-rose-600" />
                <h3 className="text-sm font-bold text-surface-900">Failure Diagnostics Screenshot</h3>
              </div>
              <button
                onClick={() => setSelectedScreenshot(null)}
                className="p-1 rounded-lg text-surface-400 hover:text-surface-700 hover:bg-surface-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-6 overflow-auto flex-1 flex items-center justify-center bg-surface-100">
              <img
                src={selectedScreenshot}
                alt="Test Failure Diagnostic"
                className="max-w-full max-h-[70vh] rounded-lg border border-surface-200 shadow-md"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
