import React from 'react';

/**
 * LankaAlpha Official Brand Logo Component
 * Combines a sleek Greek Alpha (α) breakout swoosh, ascending data bars,
 * and modern financial gradients tailored for Sri Lanka & CSE intelligence.
 */
export default function Logo({
  size = 'md',
  showText = false,
  subtitle = 'Colombo Stock Exchange AI',
  className = '',
}) {
  const sizeMap = {
    xs: { icon: 'w-6 h-6', text: 'text-xs', sub: 'text-[9px]' },
    sm: { icon: 'w-8 h-8', text: 'text-sm', sub: 'text-[10px]' },
    md: { icon: 'w-10 h-10', text: 'text-base', sub: 'text-xs' },
    lg: { icon: 'w-12 h-12', text: 'text-lg', sub: 'text-xs' },
    xl: { icon: 'w-16 h-16', text: 'text-2xl', sub: 'text-sm' },
  };

  const currentSize = sizeMap[size] || sizeMap.md;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Scalable Vector Emblem */}
      <div className={`relative shrink-0 ${currentSize.icon}`}>
        <svg
          viewBox="0 0 64 64"
          className="w-full h-full drop-shadow-md"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="logoBgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#1e293b" />
              <stop offset="50%" stop-color="#0f172a" />
              <stop offset="100%" stop-color="#020617" />
            </linearGradient>

            <linearGradient id="logoBorderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.9" />
              <stop offset="50%" stop-color="#3b82f6" stop-opacity="0.5" />
              <stop offset="100%" stop-color="#10b981" stop-opacity="0.8" />
            </linearGradient>

            <linearGradient id="logoAlphaGrad" x1="10%" y1="90%" x2="90%" y2="10%">
              <stop offset="0%" stop-color="#10b981" />
              <stop offset="35%" stop-color="#06b6d4" />
              <stop offset="70%" stop-color="#3b82f6" />
              <stop offset="100%" stop-color="#818cf8" />
            </linearGradient>

            <linearGradient id="logoGoldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#fef08a" />
              <stop offset="100%" stop-color="#f59e0b" />
            </linearGradient>

            <filter id="logoGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="1.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Squircle Glass Shield */}
          <rect
            x="2"
            y="2"
            width="60"
            height="60"
            rx="16"
            fill="url(#logoBgGrad)"
            stroke="url(#logoBorderGrad)"
            strokeWidth="1.5"
          />

          {/* Soft ambient backlight */}
          <circle cx="46" cy="18" r="12" fill="#3b82f6" fillOpacity="0.2" filter="blur(5px)" />
          <circle cx="18" cy="46" r="10" fill="#10b981" fillOpacity="0.2" filter="blur(5px)" />

          {/* 3 Ascending Momentum Bars (Data -> ML -> Alpha) */}
          <rect x="18" y="38" width="3.5" height="10" rx="1.5" fill="#10b981" fillOpacity="0.75" />
          <rect x="24.5" y="32" width="3.5" height="16" rx="1.5" fill="#06b6d4" fillOpacity="0.85" />
          <rect x="31" y="25" width="3.5" height="23" rx="1.5" fill="#3b82f6" fillOpacity="0.95" />

          {/* Stylized Greek Alpha (α) with breakout trajectory */}
          <path
            d="M 46 22 C 40 38 34 46 25 46 C 17 46 12 40 12 32 C 12 23 18 17 26 17 C 33 17 39 23 44 32 L 50 14"
            stroke="url(#logoAlphaGrad)"
            strokeWidth="3.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            filter="url(#logoGlow)"
          />

          {/* Arrow Head */}
          <path
            d="M 42 14 L 50 14 L 50 22"
            stroke="url(#logoAlphaGrad)"
            strokeWidth="3.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Alpha Profit Sparkle */}
          <path
            d="M 52 11 Q 52 7 50 7 Q 52 7 52 3 Q 52 7 54 7 Q 52 7 52 11 Z"
            fill="url(#logoGoldGrad)"
          />
          <circle cx="52" cy="7" r="1" fill="#ffffff" />
        </svg>
      </div>

      {/* Typography Branding */}
      {showText && (
        <div className="min-w-0">
          <div className="flex items-center gap-1.5 leading-none">
            <span className={`font-black tracking-tight text-white ${currentSize.text}`}>
              Lanka<span className="bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">Alpha</span>
            </span>
            <span className="text-[9px] font-black uppercase tracking-wider px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
              AI
            </span>
          </div>
          {subtitle && (
            <p className={`text-slate-400 font-medium tracking-wide mt-1 line-clamp-1 ${currentSize.sub}`}>
              {subtitle}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
