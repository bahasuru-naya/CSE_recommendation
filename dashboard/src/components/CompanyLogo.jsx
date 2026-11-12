import React, { useState } from 'react';

/**
 * Generate a consistent gradient based on symbol characters.
 */
function getSymbolGradient(symbol = '') {
  const clean = symbol.replace(/[^A-Z0-9]/gi, '');
  const colors = [
    'from-blue-600 to-indigo-800',
    'from-emerald-600 to-teal-800',
    'from-violet-600 to-purple-800',
    'from-amber-600 to-orange-800',
    'from-cyan-600 to-blue-800',
    'from-rose-600 to-pink-800',
  ];
  let hash = 0;
  for (let i = 0; i < clean.length; i++) {
    hash = clean.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % colors.length;
  return colors[index];
}

/**
 * Extract a clean ticker code (e.g. "LOLC" from "LOLC.N0000").
 */
function getTicker(symbol = '') {
  return symbol.split('.')[0] || symbol.slice(0, 4);
}

export default function CompanyLogo({ symbol = '', name = '', logoUrl = null, size = 'md', className = '' }) {
  const [imgError, setImgError] = useState(false);

  const sizeClasses = {
    sm: 'w-6 h-6 text-[10px]',
    md: 'w-9 h-9 text-xs',
    lg: 'w-12 h-12 text-sm',
    xl: 'w-14 h-14 text-base',
  };

  const ticker = getTicker(symbol);
  const initials = ticker.slice(0, 3);
  const gradient = getSymbolGradient(symbol);
  const dimension = sizeClasses[size] || sizeClasses.md;

  if (logoUrl && !imgError) {
    return (
      <div
        className={`${dimension} rounded-lg bg-white p-0.5 border border-slate-700/60 shadow-sm flex items-center justify-center shrink-0 overflow-hidden ${className}`}
        title={`${symbol} - ${name || ''}`}
      >
        <img
          src={logoUrl}
          alt={symbol}
          onError={() => setImgError(true)}
          className="w-full h-full object-contain rounded-md"
          loading="lazy"
        />
      </div>
    );
  }

  // Fallback avatar badge with distinctive gradient
  return (
    <div
      className={`${dimension} rounded-lg bg-gradient-to-br ${gradient} text-white font-bold flex items-center justify-center tracking-tight shadow-sm border border-white/10 shrink-0 select-none ${className}`}
      title={`${symbol} - ${name || ''}`}
    >
      <span>{initials}</span>
    </div>
  );
}
