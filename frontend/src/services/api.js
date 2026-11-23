const API_BASE = '/api';

async function fetchJSON(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });
  if (!res.ok) {
    let errMessage = `HTTP ${res.status}`;
    try {
      const errData = await res.json();
      errMessage = errData.detail || errData.message || errMessage;
    } catch (_) {}
    throw new Error(errMessage);
  }
  return res.json();
}

export const api = {
  // Testing Runs
  startTesting: (payload) =>
    fetchJSON('/testing/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getRuns: () => fetchJSON('/testing/runs'),

  getRunStatus: (runId) => fetchJSON(`/testing/${runId}/status`),

  getRunAgents: (runId) => fetchJSON(`/testing/${runId}/agents`),

  getRunRequirements: (runId) => fetchJSON(`/testing/${runId}/requirements`),

  getRunScenarios: (runId) => fetchJSON(`/testing/${runId}/scenarios`),

  getRunTestcases: (runId) => fetchJSON(`/testing/${runId}/testcases`),

  getRunResults: (runId) => fetchJSON(`/testing/${runId}/results`),

  getRunReport: (runId) => fetchJSON(`/testing/${runId}/report`),

  getDashboardMetrics: () => fetchJSON('/testing/dashboard/metrics'),

  // Jira Integration
  getJiraStatus: () => fetchJSON('/jira/status'),

  getJiraProjects: () => fetchJSON('/jira/projects'),

  getJiraIssues: (project = '', query = '') => {
    const params = new URLSearchParams();
    if (project) params.append('project', project);
    if (query) params.append('q', query);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return fetchJSON(`/jira/issues${qs}`);
  },

  // AI Provider & Dynamic Model Discovery
  getAiProviders: () => fetchJSON('/ai/providers'),

  getProviderModels: (provider, refresh = false) =>
    fetchJSON(`/ai/models/${encodeURIComponent(provider || '')}?refresh=${Boolean(refresh)}`),

  validateModel: (provider, modelId) =>
    fetchJSON(`/ai/validate/${encodeURIComponent(provider || '')}`, {
      method: 'POST',
      body: JSON.stringify({ model_id: modelId }),
    }),

  getAiConfiguration: () => fetchJSON('/ai/configuration/status'),

  // Settings & System
  getSettings: () => fetchJSON('/settings'),

  testProviderConnection: (provider) =>
    fetchJSON(`/settings/test-provider?provider=${encodeURIComponent(provider || '')}`, {
      method: 'POST',
    }),

  testOpenAI: () =>
    fetchJSON('/settings/test-provider?provider=openai', { method: 'POST' }),

  updateSettings: (payload) =>
    fetchJSON('/settings', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getHealth: () => fetchJSON('/health'),

  // Download links
  getHtmlReportUrl: (runId) => `/api/reports/${runId}/html`,
  getScreenshotUrl: (path) => path,
};
