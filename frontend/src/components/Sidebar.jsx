import React, { useState } from 'react';
import Logo from '../assets/branding/Logo';
import {
  LayoutDashboard,
  PlusCircle,
  BrainCircuit,
  FileText,
  Network,
  FileCheck,
  PlayCircle,
  FileBarChart,
  Settings as SettingsIcon,
  Layers,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Zap,
  Bot
} from 'lucide-react';

export default function Sidebar({
  currentPage,
  setCurrentPage,
  activeRunId,
  selectedFramework,
  generationMode,
  collapsed,
  setCollapsed
}) {
  const sections = [
    {
      title: 'Workspace',
      items: [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'new_run', label: 'New Testing Run', icon: PlusCircle, badge: 'New', badgeColor: 'bg-blue-50 text-blue-700 border-blue-200' },
      ]
    },
    {
      title: 'Test Management',
      items: [
        { id: 'workflow', label: 'Agent Command Center', icon: BrainCircuit, badge: activeRunId ? 'Active' : null, badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
        { id: 'requirements', label: 'Requirements', icon: FileText },
        { id: 'scenarios', label: 'Test Scenarios', icon: Network },
        { id: 'test_cases', label: 'Test Cases', icon: FileCheck },
        { id: 'execution', label: 'Execution Runs', icon: PlayCircle },
      ]
    },
    {
      title: 'System',
      items: [
        { id: 'reports', label: 'Reports & Analytics', icon: FileBarChart },
        { id: 'settings', label: 'Settings', icon: SettingsIcon },
      ]
    }
  ];

  const isBasic = generationMode === 'basic';
  const isGemini = generationMode === 'gemini';
  const isAi = generationMode === 'openai' || generationMode === 'ai';

  const getModeBadge = () => {
    if (isGemini) {
      return <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold border shadow-2xs bg-blue-50 text-blue-700 border-blue-200">GEMINI</span>;
    }
    if (isAi) {
      return <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold border shadow-2xs bg-purple-50 text-purple-700 border-purple-200">OPENAI</span>;
    }
    return <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold border shadow-2xs bg-amber-50 text-amber-700 border-amber-200">BASIC</span>;
  };

  return (
    <aside
      className={`bg-white border-r border-surface-200 flex flex-col shrink-0 transition-all duration-300 z-20 select-none ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-surface-200">
        <div className="flex items-center gap-2.5 overflow-hidden">
          {collapsed ? (
            <div className="mx-auto" title="TraceAI Studio">
              <Logo variant="icon" size={32} />
            </div>
          ) : (
            <div className="truncate">
              <Logo variant="full" size={32} />
            </div>
          )}
        </div>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-lg hover:bg-surface-100 text-surface-400 hover:text-surface-600 transition-colors hidden lg:flex"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
        {sections.map((section, sIdx) => (
          <div key={sIdx} className="space-y-1">
            {!collapsed && (
              <div className="px-3 text-[11px] font-semibold text-surface-400 uppercase tracking-wider font-mono">
                {section.title}
              </div>
            )}
            <div className="space-y-0.5 pt-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentPage(item.id)}
                    title={collapsed ? item.label : undefined}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 font-semibold shadow-sm border border-blue-100'
                        : 'text-surface-600 hover:text-surface-900 hover:bg-surface-100'
                    } ${collapsed ? 'justify-center px-0' : ''}`}
                  >
                    <div className="flex items-center gap-3 truncate">
                      <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-blue-600' : 'text-surface-400'}`} />
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </div>
                    {!collapsed && item.badge && (
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${item.badgeColor || 'bg-surface-100 text-surface-600 border-surface-200'}`}>
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Bottom Run Status Widget */}
      {!collapsed && (
        <div className="p-3.5 m-3 rounded-xl border border-surface-200 bg-surface-50 text-xs space-y-2.5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-surface-500 uppercase font-mono">Engine & Mode</span>
            <div className="flex items-center gap-1.5">
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-white text-blue-700 border border-blue-200 shadow-2xs">
                {selectedFramework?.toUpperCase() || 'PLAYWRIGHT'}
              </span>
              {getModeBadge()}
            </div>
          </div>

          <div className="bg-white p-2 rounded-lg border border-surface-200">
            <div className="text-[10px] font-mono text-surface-400 uppercase">Active Testing Run</div>
            <div className="text-surface-900 font-mono font-semibold truncate text-[11px] mt-0.5">
              {activeRunId || 'No active run'}
            </div>
          </div>

          <div className="pt-2 border-t border-surface-200/80 flex items-center justify-between text-[11px] text-surface-500">
            <span>Demo Sandbox</span>
            <a
              href="http://127.0.0.1:8000/demo"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 text-blue-600 hover:text-blue-700 font-medium"
            >
              <span>Target App</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      )}
    </aside>
  );
}
