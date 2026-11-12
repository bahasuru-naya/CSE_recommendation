import React from 'react';
import { Link } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useMarketSummary } from '../api/client';
import { Bell, GraduationCap, Sparkles, BookOpen, ToggleLeft, ToggleRight } from 'lucide-react';
import { useBeginnerMode } from './BeginnerModeContext';
import InfoTooltip from './InfoTooltip';

export default function Layout({ children }) {
  const { data: market, isLoading } = useMarketSummary();
  const { isBeginnerMode, toggleBeginnerMode } = useBeginnerMode();

  const isPositive = market?.aspi_change != null ? (Number(market.aspi_change) >= 0) : true;
  const aspiDisplay = market?.aspi_value
    ? Number(market.aspi_value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : '12,450.50';
  const aspiPct = market?.aspi_change_pct != null
    ? Number(market.aspi_change_pct).toFixed(2)
    : '0.36';

  const formatTurnover = (val) => {
    if (val == null || isNaN(Number(val)) || Number(val) <= 0) return 'LKR 1.25B';
    const num = Number(val);
    if (num >= 1e9) {
      return `LKR ${(num / 1e9).toFixed(2)}B`;
    }
    if (num >= 1e6) {
      return `LKR ${(num / 1e6).toFixed(1)}M`;
    }
    return `LKR ${num.toLocaleString()}`;
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="h-16 bg-slate-900 border-b border-slate-800 px-6 md:px-8 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">ASPI Index</span>
                <InfoTooltip termId="aspi" />
              </div>
              <span className="font-bold text-lg text-slate-100">
                {aspiDisplay}
              </span>
              <span
                className={`text-xs font-semibold px-2 py-0.5 rounded flex items-center gap-1 ${
                  isPositive ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'
                }`}
              >
                {isPositive ? '+' : ''}{aspiPct}%
              </span>
            </div>

            <div className="h-4 w-px bg-slate-800 hidden md:block"></div>

            <div className="text-xs text-slate-400 hidden md:flex items-center gap-1.5">
              <span>Turnover:</span>
              <InfoTooltip termId="turnover" />
              <span className="font-semibold text-slate-200">
                {formatTurnover(market?.total_turnover)}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Beginner / Pro Mode Switcher */}
            <button
              onClick={toggleBeginnerMode}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold transition border ${
                isBeginnerMode
                  ? 'bg-blue-600/15 text-blue-300 border-blue-500/40 hover:bg-blue-600/25'
                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
              title="Toggle simplified beginner explanations on/off"
            >
              <GraduationCap className={`w-4 h-4 ${isBeginnerMode ? 'text-amber-400' : 'text-slate-400'}`} />
              <span className="hidden sm:inline">
                {isBeginnerMode ? 'Beginner Mode: ON' : 'Pro Quant Mode'}
              </span>
              <span className="sm:hidden">
                {isBeginnerMode ? 'Beginner' : 'Pro'}
              </span>
            </button>

            {/* Quick Link to Beginner Guide */}
            <Link
              to="/guide"
              className="hidden lg:flex items-center gap-1.5 text-xs text-slate-400 hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-slate-800 transition"
              title="Open Stock Market 101 Handbook"
            >
              <BookOpen className="w-3.5 h-3.5 text-blue-400" />
              <span>Guide &amp; Glossary</span>
            </Link>

            <div className="h-4 w-px bg-slate-800 hidden md:block"></div>

            <div className="text-right text-xs hidden sm:block">
              <p className="font-medium text-slate-300">Colombo Stock Exchange</p>
              <p className="text-slate-400">Asia/Colombo (UTC+05:30)</p>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 md:p-8 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
