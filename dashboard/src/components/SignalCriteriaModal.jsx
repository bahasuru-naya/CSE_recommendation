import React, { useState } from 'react';
import {
  Brain,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  Eye,
  Scale,
  DollarSign,
  Activity,
  Filter,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  X,
  ArrowRight,
  Info,
} from 'lucide-react';
import InfoTooltip from './InfoTooltip';

export default function SignalCriteriaModal({ isOpen, onClose }) {
  const [activeSignal, setActiveSignal] = useState('BUY');

  if (!isOpen) return null;

  const criteriaData = {
    BUY: {
      title: 'BUY (Good Opportunity)',
      subtitle: 'High probability of price appreciation beating broker fees & the CSE market.',
      badgeColor: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
      icon: TrendingUp,
      iconColor: 'text-emerald-400',
      summary:
        'The AI generates a BUY signal only when a stock clears all three safety gates: strong liquidity, bullish macro regime, and high model confidence.',
      gates: [
        {
          name: 'Gate 1: High Model Confidence Score',
          requirement: 'Confidence ≥ 65%',
          explanation:
            'The LightGBM machine learning model projects a 65%+ probability that this stock will beat the ASPI index net of round-trip costs over the next 10 trading days.',
          status: 'Must Be Met',
          statusColor: 'emerald',
        },
        {
          name: 'Gate 2: Cost-Hurdle Clearance',
          requirement: 'Expected Upside > 2.68% Fees',
          explanation:
            'Projected upside must comfortably exceed the official 2.68% CSE round-trip costs (broker commissions, SEC levies, CDS charges, and taxes). Trades that barely make 1-2% are filtered out.',
          status: 'Must Be Met',
          statusColor: 'emerald',
        },
        {
          name: 'Gate 3: Market Regime Filter',
          requirement: 'ASPI Index > 100-Day SMA (allow_buy = True)',
          explanation:
            'The overall Colombo Stock Exchange index must be in a healthy macro trend. When the market is in severe bear territory, BUY signals are paused to protect your capital.',
          status: 'Must Be Met',
          statusColor: 'emerald',
        },
        {
          name: 'Gate 4: Minimum Share Liquidity',
          requirement: 'Daily Turnover ≥ LKR 200,000 & Volume ≥ 500 Shares',
          explanation:
            'The stock must have enough active buyers and sellers so you can enter and exit without delays or unfair price slippage.',
          status: 'Must Be Met',
          statusColor: 'emerald',
        },
      ],
      execution: [
        { label: 'Recommended Entry Range', value: 'Current Price ± 1% (never chase high spikes)' },
        { label: 'Safety Stop-Loss', value: '2 × ATR below entry price (limits losses to ~3-5%)' },
        { label: 'Profit Target', value: '3 × ATR above entry price (aims for 1.5:1+ reward-to-risk)' },
        { label: 'Position Sizing', value: 'Max 2% risk of total portfolio capital per trade' },
      ],
      userAction: 'Click "Record Buy" to open a tracked holding in Portfolio with entry price, stop-loss, and profit target.',
    },
    SELL: {
      title: 'SELL (Take Profit / Avoid)',
      subtitle: 'Time to lock in gains or step aside before prices decline further.',
      badgeColor: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
      icon: TrendingDown,
      iconColor: 'text-rose-400',
      summary:
        'The AI triggers a SELL signal when statistical momentum turns sharply negative or when previous profit targets or stop-loss boundaries are breached.',
      gates: [
        {
          name: 'Gate 1: Weak Model Confidence Score',
          requirement: 'Confidence ≤ 35%',
          explanation:
            'The model calculates a 65%+ probability of underperforming or dropping. Statistical buyers have dried up, and sellers are dominating order books.',
          status: 'Trigger Condition',
          statusColor: 'rose',
        },
        {
          name: 'Gate 2: Target Price or Stop Loss Hit',
          requirement: 'Price reaches Target OR drops below Stop-Loss',
          explanation:
            'If the stock reaches its profit goal, sell to lock in real cash. If it breaches the stop-loss level, sell immediately to avoid a minor 3% dip turning into a 30% loss.',
          status: 'Trigger Condition',
          statusColor: 'rose',
        },
        {
          name: 'Gate 3: Severe Overbought or Negative Divergence',
          requirement: 'RSI > 75 with declining buyer volume',
          explanation:
            'When prices spike too fast on thinning volume, institutional smart money is often quietly unloading shares onto retail buyers.',
          status: 'Caution Trigger',
          statusColor: 'rose',
        },
      ],
      execution: [
        { label: 'Action for Existing Holders', value: 'Sell shares through your CSE broker to lock in cash profits' },
        { label: 'Action for Non-Holders', value: 'Do not buy. Wait for price to find a healthy bottom floor' },
        { label: 'Fee Impact', value: 'Factor in 1.12% sell-side CSE transaction fees' },
      ],
      userAction: 'Click "Record Sell" to close the position in Portfolio and calculate your final net profit/loss.',
    },
    HOLD: {
      title: 'HOLD (Wait & Hold Existing Shares)',
      subtitle: 'Neutral territory. Maintain current positions without adding fresh money.',
      badgeColor: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
      icon: Scale,
      iconColor: 'text-blue-400',
      summary:
        'The stock is liquid and stable, but expected gains are not yet high enough to justify paying fresh 2.68% round-trip brokerage fees.',
      gates: [
        {
          name: 'Gate 1: Neutral Model Confidence',
          requirement: '36% < Confidence < 64%',
          explanation:
            'The AI sees neither a strong bull surge nor a bear breakdown. Expected return is around market average.',
          status: 'Neutral Range',
          statusColor: 'blue',
        },
        {
          name: 'Gate 2: Insufficient Alpha Over 2.68% Fee Hurdle',
          requirement: 'Expected 10-day return < 2.68% net fee hurdle',
          explanation:
            'Buying today would likely leave you flat after broker fees. It is smarter to let existing shares ride rather than paying fresh transaction fees.',
          status: 'Fee Barrier',
          statusColor: 'blue',
        },
        {
          name: 'Gate 3: Holding Above Stop-Loss',
          requirement: 'Price is comfortably above safety stop floor',
          explanation:
            'There is no reason to panic sell because the stock is consolidating in a normal, healthy price band.',
          status: 'Safe Zone',
          statusColor: 'blue',
        },
      ],
      execution: [
        { label: 'Action for Existing Holders', value: 'Keep your shares recorded in Portfolio; leave stops active' },
        { label: 'Action for Non-Holders', value: 'Do not buy new shares yet; wait for a confirmed BUY breakout' },
      ],
      userAction: 'Keeps the stock tracked in your portfolio or watchlist without modifying share counts.',
    },
    WATCH: {
      title: 'WATCH (Wait & Monitor Liquidity)',
      subtitle: 'Thinly traded stock or consolidating pattern. Wait for volume to pick up.',
      badgeColor: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
      icon: Eye,
      iconColor: 'text-amber-400',
      summary:
        'Even if a stock looks cheap or has positive momentum, the AI marks it WATCH if it fails the liquidity safety check.',
      gates: [
        {
          name: 'Gate 1: Liquidity Safety Filter Failed',
          requirement: 'Turnover < LKR 200,000 / day OR Volume < 500 shares',
          explanation:
            'Thinly traded stocks on the Colombo Stock Exchange have wide bid-ask spreads. If you buy, you might get trapped and unable to sell when you want.',
          status: 'Safety Quarantine',
          statusColor: 'amber',
        },
        {
          name: 'Gate 2: Waiting for Volume Breakout',
          requirement: 'Volume surge > 1.2x needed for confirmation',
          explanation:
            'A true sustainable rally requires institutional buyer volume. Until trading activity surges, the AI keeps it on the watchlist.',
          status: 'Pending Volume',
          statusColor: 'amber',
        },
      ],
      execution: [
        { label: 'Action for Investors', value: 'Add to Watchlist; monitor for volume spikes and breakout alerts' },
        { label: 'Risk Protection', value: 'Prevents getting locked into illiquid penny stocks' },
      ],
      userAction: 'Click "Add to Watchlist" to track price movements and alerts without risking real money.',
    },
  };

  const current = criteriaData[activeSignal];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-850/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-600/20 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white">How the AI Determines Stock Signals</h2>
                <span className="text-[10px] font-bold uppercase bg-blue-500/15 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full">
                  Decision Rules &amp; Safety Gates
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Exact statistical thresholds and quantitative checks applied to all 290+ CSE listed stocks.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Signal Switcher Tabs */}
        <div className="grid grid-cols-4 border-b border-slate-800 bg-slate-950/50">
          {['BUY', 'SELL', 'HOLD', 'WATCH'].map((sig) => {
            const isSelected = activeSignal === sig;
            const data = criteriaData[sig];
            const Icon = data.icon;

            return (
              <button
                key={sig}
                onClick={() => setActiveSignal(sig)}
                className={`py-3 px-2 text-center transition flex flex-col sm:flex-row items-center justify-center gap-1.5 border-b-2 ${
                  isSelected
                    ? sig === 'BUY'
                      ? 'border-emerald-500 text-emerald-400 bg-emerald-500/10 font-bold'
                      : sig === 'SELL'
                      ? 'border-rose-500 text-rose-400 bg-rose-500/10 font-bold'
                      : sig === 'HOLD'
                      ? 'border-blue-500 text-blue-400 bg-blue-500/10 font-bold'
                      : 'border-amber-500 text-amber-400 bg-amber-500/10 font-bold'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="text-xs">{sig} Signal</span>
              </button>
            );
          })}
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          {/* Active Signal Banner */}
          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${current.badgeColor}`}>
                {current.title}
              </span>
              <span className="text-[11px] text-slate-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                <span>Automated AI Rule</span>
              </span>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed">{current.subtitle}</p>
            <p className="text-[11px] text-slate-400">{current.summary}</p>
          </div>

          {/* Decision Gates Checklist */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Filter className="w-4 h-4 text-purple-400" />
              <span>Required Safety Gates &amp; Conditions</span>
            </h3>

            <div className="space-y-2.5">
              {current.gates.map((gate, i) => (
                <div
                  key={i}
                  className="bg-slate-850 p-3.5 rounded-xl border border-slate-800 space-y-1.5 hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-white text-xs flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                      <span>{gate.name}</span>
                    </span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-blue-300 border border-slate-700">
                      {gate.requirement}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{gate.explanation}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Execution & Risk Bounds */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Execution Guidelines &amp; Risk Rules</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {current.execution.map((item, idx) => (
                <div key={idx} className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-medium">
                    {item.label}
                  </span>
                  <span className="text-xs text-slate-200 font-semibold block mt-1">
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* What to do in UI */}
          <div className="bg-gradient-to-r from-blue-950/40 to-indigo-950/40 p-4 rounded-xl border border-blue-500/20 flex items-start gap-3">
            <Sparkles className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-white text-xs block">Action Button in Dashboard:</span>
              <p className="text-xs text-blue-200/90 mt-0.5 leading-relaxed">{current.userAction}</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-850/60 flex items-center justify-between text-xs">
          <span className="text-slate-400">
            All signals are audited against historical price data and CSE brokerage costs.
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg transition"
          >
            Got It
          </button>
        </div>
      </div>
    </div>
  );
}
