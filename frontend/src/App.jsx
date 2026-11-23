import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import NewRun from './pages/NewRun';
import AgentWorkflow from './pages/AgentWorkflow';
import Requirements from './pages/Requirements';
import Scenarios from './pages/Scenarios';
import TestCases from './pages/TestCases';
import ExecutionResults from './pages/ExecutionResults';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import { api } from './services/api';

export default function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [runs, setRuns] = useState([]);
  const [activeRunId, setActiveRunId] = useState('');
  const [activeRunData, setActiveRunData] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [settings, setSettings] = useState(null);
  const [collapsed, setCollapsed] = useState(false);

  // Load runs, metrics, and settings
  const refreshData = async () => {
    try {
      const [runsList, dbMetrics, sysSettings] = await Promise.all([
        api.getRuns(),
        api.getDashboardMetrics(),
        api.getSettings(),
      ]);

      setRuns(runsList || []);
      setMetrics(dbMetrics || null);
      setSettings(sysSettings || null);

      // Auto-select latest run if activeRunId is not set or not in list
      if (runsList && runsList.length > 0) {
        if (!activeRunId || !runsList.some(r => r.run_id === activeRunId)) {
          setActiveRunId(runsList[0].run_id);
          setActiveRunData(runsList[0]);
        } else {
          const current = runsList.find(r => r.run_id === activeRunId);
          if (current) setActiveRunData(current);
        }
      }
    } catch (_) {}
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 4000);
    return () => clearInterval(interval);
  }, [activeRunId]);

  const handleRunStarted = (newRunId) => {
    setActiveRunId(newRunId);
    setCurrentPage('workflow');
    refreshData();
  };

  const handleSelectRun = (runId) => {
    setActiveRunId(runId);
    setCurrentPage('workflow');
  };

  return (
    <div className="flex h-screen bg-surface-50 text-surface-900 overflow-hidden font-sans">
      {/* Left Sidebar */}
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        activeRunId={activeRunId}
        selectedFramework={activeRunData?.automation_framework || settings?.default_automation_framework}
        generationMode={activeRunData?.ai_provider || activeRunData?.generation_mode || (settings?.gemini_configured ? 'gemini' : settings?.openai_configured ? 'openai' : 'basic')}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <Navbar
          runs={runs}
          activeRunId={activeRunId}
          activeRunData={activeRunData}
          setActiveRunId={(id) => {
            setActiveRunId(id);
            const found = runs.find(r => r.run_id === id);
            if (found) setActiveRunData(found);
          }}
          settings={settings}
          onNewRunClick={() => setCurrentPage('new_run')}
          onRefresh={refreshData}
        />

        {/* Page Views Container */}
        <main className="flex-1 overflow-y-auto bg-surface-50">
          {currentPage === 'dashboard' && (
            <Dashboard
              metrics={metrics}
              runs={runs}
              onSelectRun={handleSelectRun}
              onNewRunClick={() => setCurrentPage('new_run')}
            />
          )}

          {currentPage === 'new_run' && (
            <NewRun
              onRunStarted={handleRunStarted}
              defaultFramework={settings?.default_automation_framework || 'playwright'}
            />
          )}

          {currentPage === 'workflow' && (
            <AgentWorkflow
              activeRunId={activeRunId}
              runData={activeRunData}
              onNavigatePage={(page) => setCurrentPage(page)}
            />
          )}

          {currentPage === 'requirements' && (
            <Requirements
              activeRunId={activeRunId}
              onNavigateToScenarios={() => setCurrentPage('scenarios')}
            />
          )}

          {currentPage === 'scenarios' && (
            <Scenarios
              activeRunId={activeRunId}
              onNavigateToTestCases={() => setCurrentPage('test_cases')}
            />
          )}

          {currentPage === 'test_cases' && (
            <TestCases
              activeRunId={activeRunId}
              onNavigateToExecution={() => setCurrentPage('execution')}
            />
          )}

          {currentPage === 'execution' && (
            <ExecutionResults
              activeRunId={activeRunId}
              onNavigateToReport={() => setCurrentPage('reports')}
            />
          )}

          {currentPage === 'reports' && (
            <Reports activeRunId={activeRunId} />
          )}

          {currentPage === 'settings' && (
            <Settings onSettingsUpdated={refreshData} />
          )}
        </main>
      </div>
    </div>
  );
}
