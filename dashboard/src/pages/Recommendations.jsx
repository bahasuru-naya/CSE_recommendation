import React, { useState } from 'react';
import { useRecommendations } from '../api/client';
import RecommendationCard from '../components/RecommendationCard';
import PriceChartModal from '../components/PriceChartModal';
import SignalCriteriaModal from '../components/SignalCriteriaModal';
import InfoTooltip from '../components/InfoTooltip';
import { useBeginnerMode } from '../components/BeginnerModeContext';
import { Filter, Search, Sparkles, HelpCircle, CheckCircle2, Brain, ChevronDown, ChevronUp, Scale, TrendingUp, TrendingDown, Eye } from 'lucide-react';

export default function Recommendations() {
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [inspectedSymbol, setInspectedSymbol] = useState(null);
  const [showCriteriaModal, setShowCriteriaModal] = useState(false);
  const [showCriteriaBanner, setShowCriteriaBanner] = useState(false);
  const { isBeginnerMode } = useBeginnerMode();

  const signalParam = filter === 'ALL' ? null : filter;
  const { data: recData, isLoading } = useRecommendations(signalParam);

  const recsRaw = recData?.data || [];
  const seenSymbols = new Set();
  const recs = recsRaw.filter((r) => {
    const sym = (r.symbol || '').trim().toUpperCase();
    if (!sym || seenSymbols.has(sym)) {
      return false;
    }
    seenSymbols.add(sym);

    if (!search) return true;
    return (
      r.symbol.toLowerCase().includes(search.toLowerCase()) ||
      (r.name && r.name.toLowerCase().includes(search.toLowerCase())) ||
      (r.security_name && r.security_name.toLowerCase().includes(search.toLowerCase()))
    );
  });

  return (
    <div className="space-y-6">
      {/* Title & Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <span>Stock Signals &amp; Recommendations</span>
            <InfoTooltip termId="signal_buy" />
          </h1>
          <p className="text-xs text-slate-400">
            {isBeginnerMode
              ? 'AI-checked stock recommendations for Sri Lankan companies. Place your final buy/sell orders through your registered CSE broker.'
              : 'Rule-checked and SHAP-explained long recommendations. All orders placed by you through your broker.'}
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search symbol (e.g. COMB)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 w-48"
            />
          </div>

          <div className="bg-slate-900 p-1 rounded-lg border border-slate-800 flex items-center text-xs">
            {['ALL', 'BUY', 'SELL', 'HOLD', 'WATCH'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded-md font-medium transition ${
                  filter === f ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Signal Determination Overview Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-4">
            <span className="text-slate-300 font-semibold flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>How AI Determines Signals:</span>
            </span>
            <span className="inline-flex items-center gap-1.5 text-emerald-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <strong>BUY:</strong> Confidence ≥65% + Liquid + Market Bullish
            </span>
            <span className="inline-flex items-center gap-1.5 text-rose-300">
              <span className="w-2 h-2 rounded-full bg-rose-400"></span>
              <strong>SELL:</strong> Confidence ≤35% or Stop-Loss / Target Hit
            </span>
            <span className="inline-flex items-center gap-1.5 text-blue-300">
              <span className="w-2 h-2 rounded-full bg-blue-400"></span>
              <strong>HOLD:</strong> 36-64% Neutral Zone (Upside &lt; 2.68% fee hurdle)
            </span>
            <span className="inline-flex items-center gap-1.5 text-amber-300">
              <span className="w-2 h-2 rounded-full bg-amber-400"></span>
              <strong>WATCH:</strong> Thin volume (&lt;LKR 200k turnover/day)
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowCriteriaBanner(!showCriteriaBanner)}
              className="text-[11px] text-blue-400 hover:text-blue-300 flex items-center gap-1 font-semibold transition"
            >
              <span>{showCriteriaBanner ? 'Hide Details' : 'Expand Criteria'}</span>
              {showCriteriaBanner ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={() => setShowCriteriaModal(true)}
              className="text-[11px] text-purple-300 hover:text-purple-200 bg-purple-500/15 px-2.5 py-1 rounded border border-purple-500/30 flex items-center gap-1 font-semibold transition"
            >
              <span>Full Guide</span>
            </button>
          </div>
        </div>

        {/* Expandable 4-Signal Criteria Cards */}
        {showCriteriaBanner && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 pt-3 border-t border-slate-800 text-xs">
            {/* BUY */}
            <div className="bg-slate-950/70 p-3 rounded-lg border border-emerald-500/20 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-emerald-400 flex items-center gap-1">
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>BUY Criteria</span>
                </span>
                <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-300 px-1.5 py-0.2 rounded border border-emerald-500/30">
                  ≥ 65% Score
                </span>
              </div>
              <ul className="text-slate-300 space-y-1 text-[11px]">
                <li>&bull; Model confidence ≥ 65% alpha over ASPI</li>
                <li>&bull; Expected upside clears 2.68% CSE fees</li>
                <li>&bull; ASPI index &gt; 100-day trendline (Regime Safe)</li>
                <li>&bull; Daily turnover ≥ LKR 200,000 &amp; volume ≥ 500</li>
              </ul>
              <span className="text-[10px] text-emerald-400 block pt-1 border-t border-slate-800">
                Action: Open holding within Entry Range with 2x ATR stop.
              </span>
            </div>

            {/* SELL */}
            <div className="bg-slate-950/70 p-3 rounded-lg border border-rose-500/20 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-rose-400 flex items-center gap-1">
                  <TrendingDown className="w-3.5 h-3.5" />
                  <span>SELL Criteria</span>
                </span>
                <span className="text-[10px] font-mono bg-rose-500/10 text-rose-300 px-1.5 py-0.2 rounded border border-rose-500/30">
                  ≤ 35% Score
                </span>
              </div>
              <ul className="text-slate-300 space-y-1 text-[11px]">
                <li>&bull; Model confidence drops to ≤ 35%</li>
                <li>&bull; Stop-loss breached (cuts loss at ~3-5%)</li>
                <li>&bull; Profit target achieved (locks in cash gain)</li>
                <li>&bull; Extreme overbought RSI &gt; 75 with divergence</li>
              </ul>
              <span className="text-[10px] text-rose-400 block pt-1 border-t border-slate-800">
                Action: Sell position through CSE broker to protect capital.
              </span>
            </div>

            {/* HOLD */}
            <div className="bg-slate-950/70 p-3 rounded-lg border border-blue-500/20 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-blue-400 flex items-center gap-1">
                  <Scale className="w-3.5 h-3.5" />
                  <span>HOLD Criteria</span>
                </span>
                <span className="text-[10px] font-mono bg-blue-500/10 text-blue-300 px-1.5 py-0.2 rounded border border-blue-500/30">
                  36% - 64% Score
                </span>
              </div>
              <ul className="text-slate-300 space-y-1 text-[11px]">
                <li>&bull; Liquid stock in neutral momentum zone</li>
                <li>&bull; Projected return &lt; 2.68% fee hurdle</li>
                <li>&bull; Price safely above stop-loss floor</li>
                <li>&bull; Consolidating without clear direction</li>
              </ul>
              <span className="text-[10px] text-blue-400 block pt-1 border-t border-slate-800">
                Action: Keep current shares; avoid paying fresh broker fees.
              </span>
            </div>

            {/* WATCH */}
            <div className="bg-slate-950/70 p-3 rounded-lg border border-amber-500/20 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-amber-400 flex items-center gap-1">
                  <Eye className="w-3.5 h-3.5" />
                  <span>WATCH Criteria</span>
                </span>
                <span className="text-[10px] font-mono bg-amber-500/10 text-amber-300 px-1.5 py-0.2 rounded border border-amber-500/30">
                  Illiquid Check
                </span>
              </div>
              <ul className="text-slate-300 space-y-1 text-[11px]">
                <li>&bull; Daily turnover &lt; LKR 200,000</li>
                <li>&bull; Average volume &lt; 500 shares per day</li>
                <li>&bull; Wide bid-ask spread risks slippage</li>
                <li>&bull; Promising pattern waiting for volume surge</li>
              </ul>
              <span className="text-[10px] text-amber-400 block pt-1 border-t border-slate-800">
                Action: Add to Watchlist; wait for buyer volume to confirm.
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Signal Criteria Full Modal */}
      <SignalCriteriaModal
        isOpen={showCriteriaModal}
        onClose={() => setShowCriteriaModal(false)}
      />

      {/* Inspected Stock Chart Pop-up Window */}
      <PriceChartModal
        symbol={inspectedSymbol}
        isOpen={!!inspectedSymbol}
        onClose={() => setInspectedSymbol(null)}
      />

      {/* Grid of Recommendation Cards */}
      {isLoading ? (
        <div className="h-60 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center text-slate-500 text-sm">
          Loading recommendations...
        </div>
      ) : recs.length === 0 ? (
        <div className="h-60 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center text-slate-500 text-sm">
          No recommendations match filter "{filter}".
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {recs.map((rec) => (
            <RecommendationCard
              key={rec.id}
              rec={rec}
              onSelectSymbol={(sym) => setInspectedSymbol(sym)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
