import React from 'react';

/**
 * TraceAI Studio Modern Brand Logo Component
 * - Encapsulates the 6-agent neural mesh, continuous validation checkmark, and typography
 * - High-precision vector SVG that scales flawlessly without raster distortion
 * 
 * @param {'full' | 'icon'} variant - Render mode: 'full' (symbol + text) or 'icon' (symbol only)
 * @param {'light' | 'dark' | 'auto'} theme - Color scheme: 'light' (dark text), 'dark' (light text)
 * @param {number | string} size - Height or bounding dimension (default 36)
 * @param {string} className - Additional CSS classes
 */
export default function Logo({
  variant = 'full',
  theme = 'light',
  size = 36,
  className = ''
}) {
  const isDark = theme === 'dark';
  const textPrimary = isDark ? '#F8FAFC' : '#0F172A';
  const textSecondary = isDark ? '#94A3B8' : '#64748B';
  const textAccent = isDark ? '#38BDF8' : '#2563EB';
  const badgeBg = isDark ? '#1E293B' : '#EFF6FF';
  const badgeBorder = isDark ? '#334155' : '#BFDBFE';
  const badgeText = isDark ? '#38BDF8' : '#1D4ED8';
  const nodeStroke = isDark ? '#0B1120' : '#FFFFFF';

  if (variant === 'icon') {
    return (
      <svg
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: size, height: size }}
        className={`shrink-0 select-none ${className}`}
        aria-label="TraceAI Studio Logo"
      >
        <defs>
          <linearGradient id="traceIconGrad" x1="18%" y1="60%" x2="84%" y2="20%">
            <stop offset="0%" stopColor="#06B6D4" />
            <stop offset="50%" stopColor="#3B82F6" />
            <stop offset="100%" stopColor="#8B5CF6" />
          </linearGradient>
          <linearGradient id="traceOrbitGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.4" />
          </linearGradient>
        </defs>

        {/* Ambient Glow */}
        <circle cx="50" cy="50" r="42" fill="url(#traceOrbitGrad)" opacity="0.08" />

        {/* 6-Agent Interconnection Web */}
        <polygon
          points="50,14 82,32 82,68 50,86 18,68 18,32"
          stroke="url(#traceOrbitGrad)"
          strokeWidth="2.5"
          strokeDasharray="4 4"
          fill="none"
        />

        {/* Internal Cross Links */}
        <line x1="50" y1="14" x2="50" y2="86" stroke="#3B82F6" strokeWidth="1.25" strokeOpacity="0.2" />
        <line x1="18" y1="32" x2="82" y2="68" stroke="#3B82F6" strokeWidth="1.25" strokeOpacity="0.2" />
        <line x1="18" y1="68" x2="82" y2="32" stroke="#3B82F6" strokeWidth="1.25" strokeOpacity="0.2" />

        {/* Secondary Trace Pulse */}
        <path
          d="M 26 47 L 43 65 L 75 28"
          stroke="#06B6D4"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeOpacity="0.45"
        />

        {/* Primary Dynamic QA Checkmark */}
        <path
          d="M 23 48 L 43 72 L 81 22"
          stroke="url(#traceIconGrad)"
          strokeWidth="7.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* 6 Collaborative AI Agent Nodes */}
        <circle cx="50" cy="14" r="4" fill="#06B6D4" stroke={nodeStroke} strokeWidth="1.5" />
        <circle cx="82" cy="32" r="4" fill="#8B5CF6" stroke={nodeStroke} strokeWidth="1.5" />
        <circle cx="82" cy="68" r="4" fill="#7C3AED" stroke={nodeStroke} strokeWidth="1.5" />
        <circle cx="50" cy="86" r="4" fill="#2563EB" stroke={nodeStroke} strokeWidth="1.5" />
        <circle cx="18" cy="68" r="4" fill="#3B82F6" stroke={nodeStroke} strokeWidth="1.5" />
        <circle cx="18" cy="32" r="4" fill="#06B6D4" stroke={nodeStroke} strokeWidth="1.5" />

        {/* Sparkle Apex */}
        <circle cx="81" cy="22" r="2.25" fill="#FFFFFF" />
      </svg>
    );
  }

  // Full Variant: Symbol + Typography + Verification Badge
  const height = size;
  const width = typeof size === 'number' ? Math.round(size * 4.4) : 'auto';

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Icon */}
      <svg
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: height, height: height }}
        className="shrink-0"
      >
        <defs>
          <linearGradient id="traceFullGrad" x1="18%" y1="60%" x2="84%" y2="20%">
            <stop offset="0%" stopColor="#06B6D4" />
            <stop offset="50%" stopColor="#3B82F6" />
            <stop offset="100%" stopColor="#8B5CF6" />
          </linearGradient>
          <linearGradient id="orbitFullGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.4" />
          </linearGradient>
        </defs>

        <polygon
          points="50,14 82,32 82,68 50,86 18,68 18,32"
          stroke="url(#orbitFullGrad)"
          strokeWidth="2.5"
          strokeDasharray="4 4"
          fill="none"
        />
        <line x1="50" y1="14" x2="50" y2="86" stroke="#3B82F6" strokeWidth="1.25" strokeOpacity="0.2" />
        <line x1="18" y1="32" x2="82" y2="68" stroke="#3B82F6" strokeWidth="1.25" strokeOpacity="0.2" />
        <line x1="18" y1="68" x2="82" y2="32" stroke="#3B82F6" strokeWidth="1.25" strokeOpacity="0.2" />

        <path
          d="M 23 48 L 43 72 L 81 22"
          stroke="url(#traceFullGrad)"
          strokeWidth="7.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        <circle cx="50" cy="14" r="4" fill="#06B6D4" stroke={nodeStroke} strokeWidth="1.5" />
        <circle cx="82" cy="32" r="4" fill="#8B5CF6" stroke={nodeStroke} strokeWidth="1.5" />
        <circle cx="82" cy="68" r="4" fill="#7C3AED" stroke={nodeStroke} strokeWidth="1.5" />
        <circle cx="50" cy="86" r="4" fill="#2563EB" stroke={nodeStroke} strokeWidth="1.5" />
        <circle cx="18" cy="68" r="4" fill="#3B82F6" stroke={nodeStroke} strokeWidth="1.5" />
        <circle cx="18" cy="32" r="4" fill="#06B6D4" stroke={nodeStroke} strokeWidth="1.5" />
        <circle cx="81" cy="22" r="2.25" fill="#FFFFFF" />
      </svg>

      {/* Typography & Badge */}
      <div className="flex flex-col justify-center leading-none">
        <div className="flex items-center gap-2">
          <span
            className="font-extrabold tracking-tight"
            style={{
              color: textPrimary,
              fontSize: typeof size === 'number' ? Math.max(16, Math.round(size * 0.52)) : '1.15rem',
              letterSpacing: '-0.03em'
            }}
          >
            Trace<span style={{ color: textAccent }}>AI</span>
          </span>
          <span
            className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border"
            style={{
              backgroundColor: badgeBg,
              borderColor: badgeBorder,
              color: badgeText
            }}
          >
            6-AGENTS
          </span>
        </div>
        <span
          className="font-semibold uppercase tracking-widest mt-0.5"
          style={{
            color: textSecondary,
            fontSize: typeof size === 'number' ? Math.max(9, Math.round(size * 0.26)) : '0.65rem',
            letterSpacing: '0.24em'
          }}
        >
          Studio
        </span>
      </div>
    </div>
  );
}
