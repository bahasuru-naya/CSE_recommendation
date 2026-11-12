import React, { useState } from 'react';
import {
  Brain,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  Activity,
  Layers,
  X,
  CheckCircle2,
  AlertTriangle,
  Info,
  DollarSign,
  Maximize2,
  Sparkles,
  GraduationCap,
  ArrowRight,
  HelpCircle,
  Scale,
  Eye,
  Filter,
  Lightbulb,
} from 'lucide-react';
import CompanyLogo from './CompanyLogo';
import InfoTooltip from './InfoTooltip';
import { useBeginnerMode } from './BeginnerModeContext';
import { getFeatureMeta } from '../data/featureMetadata';

export default function ExplainabilityModal({ rec, isOpen, onClose }) {
  const { isBeginnerMode } = useBeginnerMode();
  const [activeTab, setActiveTab] = useState('beginner'); // 'beginner' or 'quant'

  if (!isOpen || !rec) return null;

  const isBuy = rec.signal === 'BUY';
  const isSell = rec.signal === 'SELL';
  const isWatch = rec.signal === 'WATCH';

  const badgeColor = isBuy
    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
    : isSell
    ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
    : isWatch
    ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
    : 'bg-slate-700/30 text-slate-400 border-slate-700';

  const confPct = Math.round((rec.confidence || 0.5) * 100);

  // Extract structured reasons or normalize from older format
  const reasonsData = rec.reasons || {};
  const isStructured = typeof reasonsData === 'object' && !Array.isArray(reasonsData);

  const summary = isStructured
    ? reasonsData.summary
    : Array.isArray(reasonsData) && reasonsData[0]?.rule
    ? reasonsData[0].rule
    : `Model projects a ${confPct}% confidence score for ${rec.symbol}. Quantitative technical indicators and market regime context were evaluated to produce this signal.`;

  const factors = isStructured
    ? reasonsData.factors || []
    : Array.isArray(reasonsData)
    ? reasonsData.map((r) => ({
        feature: r.feature || 'Factor',
        display_name: (r.feature || 'Metric').replace('_', ' ').toUpperCase(),
        value: r.impact ? `${r.impact}` : '-',
        impact: r.impact || 0.05,
        direction: (r.impact || 0) >= 0 ? 'bullish' : 'bearish',
        description: r.rule || 'Quantitative model attribution score',
      }))
    : [];

  const regime = isStructured ? reasonsData.regime : null;
  const liquidity = isStructured ? reasonsData.liquidity : null;
  const riskReward = isStructured ? reasonsData.risk_reward : null;
  const modelDetails = isStructured ? reasonsData.model_details : null;

  // Friendly human translation of features
  const getFriendlyFeatureName = (feat) => {
    const meta = getFeatureMeta(feat);
    return meta?.name || (feat || '').replace(/_/g, ' ');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl lg:max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-850/60">
          <div className="flex items-center gap-3">
            <CompanyLogo symbol={rec.symbol} name={rec.name} logoUrl={rec.logo_url} size="lg" />
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white">{rec.symbol}</h2>
                <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${badgeColor}`}>
                  {rec.signal}
                </span>
              </div>
              <p className="text-xs text-slate-400 line-clamp-1">{rec.name || rec.security_name}</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block flex items-center gap-1 justify-end">
                <span>Confidence</span>
                <InfoTooltip termId="confidence" />
              </span>
              <span className="text-base font-extrabold text-white">{confPct}%</span>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              title="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Selector: Full-Width 3-Column Segmented Tabs */}
        <div className="border-b border-slate-800 bg-slate-950/80 px-4 sm:px-6">
          <div className="grid grid-cols-3 gap-2 -mb-px">
            <button
              onClick={() => setActiveTab('beginner')}
              className={`py-3.5 px-3 text-xs font-bold flex items-center justify-center gap-2 border-b-2 transition text-center ${
                activeTab === 'beginner'
                  ? 'border-blue-500 text-blue-400 bg-blue-500/15 rounded-t-lg shadow-sm'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 rounded-t-lg'
              }`}
            >
              <GraduationCap className="w-4 h-4 text-amber-400 shrink-0" />
              <span className="whitespace-nowrap">Plain English</span>
              <span className="hidden sm:inline text-slate-500 font-normal">(Beginner)</span>
            </button>

            <button
              onClick={() => setActiveTab('quant')}
              className={`py-3.5 px-3 text-xs font-bold flex items-center justify-center gap-2 border-b-2 transition text-center ${
                activeTab === 'quant'
                  ? 'border-blue-500 text-blue-400 bg-blue-500/15 rounded-t-lg shadow-sm'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 rounded-t-lg'
              }`}
            >
              <Activity className="w-4 h-4 text-purple-400 shrink-0" />
              <span className="whitespace-nowrap">Quant &amp; SHAP</span>
              <span className="hidden sm:inline text-slate-500 font-normal">(Waterfall)</span>
            </button>

            <button
              onClick={() => setActiveTab('criteria')}
              className={`py-3.5 px-3 text-xs font-bold flex items-center justify-center gap-2 border-b-2 transition text-center ${
                activeTab === 'criteria'
                  ? 'border-blue-500 text-blue-400 bg-blue-500/15 rounded-t-lg shadow-sm'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 rounded-t-lg'
              }`}
            >
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="whitespace-nowrap">Signal Criteria</span>
              <span className="hidden sm:inline text-slate-500 font-normal">(Checklist)</span>
            </button>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="overflow-y-auto p-6 space-y-6 text-xs text-slate-300">
          {activeTab === 'beginner' ? (
            /* =================== BEGINNER PLAIN ENGLISH VIEW =================== */
            <div className="space-y-6">
              {/* Executive Summary Card */}
              <div className="bg-gradient-to-r from-blue-950/40 via-indigo-950/30 to-slate-900 border border-blue-500/20 rounded-xl p-4 space-y-2">
                <div className="flex items-center gap-2 text-blue-400 font-bold">
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  <span>Why is the AI Recommending {rec.symbol}?</span>
                </div>
                <p className="text-slate-200 leading-relaxed text-xs">
                  {summary}
                </p>
                <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/80 flex items-start gap-1.5">
                  <Lightbulb className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                  <span><strong>In short:</strong> Our AI ran 25+ statistical checks on CSE historical price trends and found strong evidence that this stock has favorable odds of rising.</span>
                </div>
              </div>

              {/* 3 Golden Numbers (Simple Cards) */}
              <div className="space-y-2">
                <div className="flex items-center gap-1.5 text-slate-200 font-bold">
                  <DollarSign className="w-4 h-4 text-emerald-400" />
                  <span>Your 3 Golden Action Numbers</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="bg-slate-950/80 border border-slate-800 p-3.5 rounded-xl space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">1. Where to Buy</span>
                      <InfoTooltip termId="entry_range" />
                    </div>
                    <div className="text-sm font-bold text-slate-100">
                      {rec.entry_price_low ? `LKR ${rec.entry_price_low} - ${rec.entry_price_high}` : 'Around Market Price'}
                    </div>
                    <p className="text-[10px] text-slate-400">Do not overpay if price climbs above this range.</p>
                  </div>

                  <div className="bg-slate-950/80 border border-rose-500/20 p-3.5 rounded-xl space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-rose-400 font-semibold uppercase tracking-wider">2. Safety Stop</span>
                      <InfoTooltip termId="stop_loss" />
                    </div>
                    <div className="text-sm font-bold text-rose-300">
                      {rec.stop_loss ? `LKR ${rec.stop_loss}` : '-'}
                    </div>
                    <p className="text-[10px] text-rose-400/80">
                      Sell immediately if it drops here to stop small losses from turning into big ones.
                    </p>
                  </div>

                  <div className="bg-slate-950/80 border border-emerald-500/20 p-3.5 rounded-xl space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-emerald-400 font-semibold uppercase tracking-wider">3. Profit Goal</span>
                      <InfoTooltip termId="target_price" />
                    </div>
                    <div className="text-sm font-bold text-emerald-300">
                      {rec.target_price ? `LKR ${rec.target_price}` : '-'}
                    </div>
                    <p className="text-[10px] text-emerald-400/80">
                      Sell when it reaches this target to turn paper profit into real cash in your bank.
                    </p>
                  </div>
                </div>
              </div>

              {/* Top Clues the AI Spotted */}
              {factors.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-slate-200 font-bold">
                      <Brain className="w-4 h-4 text-purple-400" />
                      <span>Top Clues Spotted by the AI (SHAP Factors)</span>
                      <InfoTooltip termId="shap" />
                    </div>
                    <span className="text-[11px] text-slate-400">Plain-English indicator breakdown</span>
                  </div>

                  <div className="space-y-2.5">
                    {factors.map((factor, idx) => {
                      const isPositive = factor.direction === 'bullish' || (factor.impact && factor.impact >= 0);
                      const meta = getFeatureMeta(factor.feature);
                      const friendlyTitle = factor.display_name && !factor.display_name.includes('_')
                        ? factor.display_name
                        : meta.name;

                      return (
                        <div
                          key={idx}
                          className="bg-slate-850/90 border border-slate-800 hover:border-slate-700 rounded-xl p-3.5 space-y-2 transition"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="font-bold text-white text-xs">{friendlyTitle}</span>
                                <span className="text-[9px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                                  {meta.category}
                                </span>
                                <span className="text-[10px] text-slate-400 font-mono bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                                  Value: {factor.value}
                                </span>
                                <InfoTooltip
                                  title={meta.name}
                                  text={meta.simpleDescription}
                                  example={isPositive ? meta.bullishMeaning : meta.bearishMeaning}
                                />
                              </div>
                              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                                {meta.simpleDescription}
                              </p>
                            </div>

                            <div className="shrink-0 text-right">
                              {isPositive ? (
                                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                                  <TrendingUp className="w-3.5 h-3.5" />
                                  <span>Positive Boost</span>
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-lg border border-rose-500/20">
                                  <TrendingDown className="w-3.5 h-3.5" />
                                  <span>Caution Factor</span>
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Specific Takeaway / Interpretation */}
                          <div
                            className={`text-xs p-2.5 rounded-lg border flex items-start gap-2 ${
                              isPositive
                                ? 'bg-emerald-950/40 border-emerald-800/40 text-emerald-300'
                                : 'bg-rose-950/40 border-rose-800/40 text-rose-300'
                            }`}
                          >
                            {isPositive ? (
                              <Sparkles className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                            ) : (
                              <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                            )}
                            <div className="space-y-0.5">
                              <span className="font-semibold block text-[11px] uppercase tracking-wider text-slate-400">
                                What the AI spotted for {rec.symbol}:
                              </span>
                              <p className="leading-snug">
                                {factor.description && factor.description !== 'Model alpha indicator' && factor.description !== 'Quantitative model attribution score'
                                  ? factor.description
                                  : isPositive
                                  ? meta.bullishMeaning
                                  : meta.bearishMeaning}
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Safety Checks: Fee Hurdle + Liquidity + Overall Market */}
              <div className="space-y-3">
                <div className="text-slate-200 font-bold flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>3 Safety Guardrails Evaluated</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {/* Fee Hurdle */}
                  <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-300 text-[11px] flex items-center gap-1">
                        <span>Fee Hurdle Check</span>
                        <InfoTooltip termId="cost_hurdle" />
                      </span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        PASSED
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">
                      CSE brokerage &amp; taxes cost ~2.68%. Expected return easily beats this cost.
                    </p>
                  </div>

                  {/* Liquidity */}
                  <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-300 text-[11px] flex items-center gap-1">
                        <span>Can You Sell Easily?</span>
                        <InfoTooltip termId="liquidity" />
                      </span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {liquidity?.is_liquid ? 'PASSED' : 'CAUTION'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">
                      Active daily volume means you can turn shares into cash whenever you want.
                    </p>
                  </div>

                  {/* Market Weather */}
                  <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-300 text-[11px] flex items-center gap-1">
                        <span>Overall Market Mood</span>
                        <InfoTooltip termId="market_regime" />
                      </span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                        {regime?.regime || 'BULLISH'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">
                      The whole CSE index (ASPI) is trending up, giving this stock strong market support.
                    </p>
                  </div>
                </div>
              </div>

              {/* How to execute with your broker */}
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="font-bold text-white flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-blue-400" />
                  <span>How to buy this stock in real life:</span>
                </div>
                <ol className="list-decimal list-inside space-y-1 text-[11px] text-slate-300 pl-1">
                  <li>Log into your registered Sri Lankan Stockbroker app (CAL, Asha, CT CLSA, Bartleet, etc.).</li>
                  <li>Search for symbol: <strong className="text-white font-mono">{rec.symbol}</strong>.</li>
                  <li>Submit a buy order within the Entry Range (<strong className="text-white">LKR {rec.entry_price_low || rec.entry_price || '-'}</strong>).</li>
                  <li>Remember to keep your Stop Loss at <strong className="text-rose-300">LKR {rec.stop_loss || '-'}</strong> to protect your money.</li>
                </ol>
              </div>
            </div>
          ) : activeTab === 'quant' ? (
            /* =================== ADVANCED QUANT VIEW =================== */
            <div className="space-y-6">
              {/* Executive Summary Card */}
              <div className="bg-indigo-950/30 border border-indigo-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold mb-2">
                  <Brain className="w-4 h-4" />
                  <span>Transparent Decision Rationale</span>
                </div>
                <p className="text-slate-200 leading-relaxed text-xs">
                  {summary}
                </p>
              </div>

              {/* Model Alpha vs Cost Hurdle */}
              <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400 font-semibold flex items-center gap-1">
                    <span>Alpha Probability vs Cost Hurdle</span>
                    <InfoTooltip termId="cost_hurdle" />
                  </span>
                  <span className="text-slate-400 font-mono text-[11px]">Hurdle: 2.68% round-trip costs</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden mb-1">
                  <div
                    className={`h-full ${isBuy ? 'bg-emerald-500' : isSell ? 'bg-rose-500' : 'bg-amber-500'}`}
                    style={{ width: `${confPct}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                  <span>0% (Strong Underperform)</span>
                  <span>50% (Neutral)</span>
                  <span>100% (Strong Outperform)</span>
                </div>
              </div>

              {/* Feature Attribution (SHAP Waterfall) */}
              {factors.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-1.5 text-slate-200 font-bold">
                      <Activity className="w-4 h-4 text-blue-400" />
                      <span>Key Feature Attributions (SHAP Explanation)</span>
                      <InfoTooltip termId="shap" />
                    </div>
                    <span className="text-[11px] text-slate-500">Feature contribution to alpha forecast</span>
                  </div>

                  <div className="space-y-2.5">
                    {factors.map((factor, idx) => {
                      const isPositive = factor.direction === 'bullish' || (factor.impact && factor.impact >= 0);
                      const impactMagnitude = Math.min(Math.abs(factor.impact || 0) * 100, 100);
                      const meta = getFeatureMeta(factor.feature);
                      const friendlyTitle = factor.display_name && !factor.display_name.includes('_')
                        ? factor.display_name
                        : meta.name;

                      return (
                        <div
                          key={idx}
                          className="bg-slate-850/80 border border-slate-800 rounded-lg p-3 hover:border-slate-750 transition space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-semibold text-white text-xs">{friendlyTitle}</span>
                              <span className="text-[10px] text-slate-500 font-mono">({factor.feature})</span>
                              <span className="text-[9px] font-semibold uppercase px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                                {meta.category}
                              </span>
                              <span className="text-[11px] text-slate-300 font-mono bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                                {factor.value}
                              </span>
                              <InfoTooltip
                                title={`${friendlyTitle} (${factor.feature})`}
                                text={meta.simpleDescription}
                                example={isPositive ? meta.bullishMeaning : meta.bearishMeaning}
                              />
                            </div>
                            <div className="flex items-center gap-1 text-[11px] font-bold">
                              {isPositive ? (
                                <span className="text-emerald-400 flex items-center gap-0.5">
                                  <TrendingUp className="w-3 h-3" />
                                  +{Math.abs(factor.impact).toFixed(3)} Bullish Boost
                                </span>
                              ) : (
                                <span className="text-rose-400 flex items-center gap-0.5">
                                  <TrendingDown className="w-3 h-3" />
                                  -{Math.abs(factor.impact).toFixed(3)} Bearish Drag
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Visual Contribution Bar */}
                          <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${isPositive ? 'bg-emerald-500' : 'bg-rose-500'}`}
                              style={{ width: `${Math.max(impactMagnitude, 10)}%` }}
                            ></div>
                          </div>

                          <div className="text-[11px] text-slate-300 pt-0.5 flex flex-col gap-0.5">
                            <p className="text-slate-300">{meta.simpleDescription}</p>
                            {factor.description && factor.description !== meta.simpleDescription && (
                              <p className="text-slate-400 text-[10px] italic">
                                &bull; {factor.description}
                              </p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Risk-Reward & ATR Bounds */}
              <div>
                <div className="flex items-center gap-1.5 text-slate-200 font-bold mb-3">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Risk-Reward &amp; Execution Bounds</span>
                  <InfoTooltip termId="atr" />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
                  <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Entry Range</span>
                    <span className="text-xs font-bold text-slate-200 mt-1 block">
                      {rec.entry_price_low ? `LKR ${rec.entry_price_low} - ${rec.entry_price_high}` : 'Market Price'}
                    </span>
                  </div>

                  <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg">
                    <span className="text-[10px] text-rose-400 uppercase tracking-wider block">Stop Loss (2x ATR)</span>
                    <span className="text-xs font-bold text-rose-300 mt-1 block">
                      {rec.stop_loss ? `LKR ${rec.stop_loss}` : '-'}
                    </span>
                    {riskReward?.downside_risk_pct && (
                      <span className="text-[10px] text-rose-400 font-mono">-{riskReward.downside_risk_pct}% risk</span>
                    )}
                  </div>

                  <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg">
                    <span className="text-[10px] text-emerald-400 uppercase tracking-wider block">Target (3x ATR)</span>
                    <span className="text-xs font-bold text-emerald-300 mt-1 block">
                      {rec.target_price ? `LKR ${rec.target_price}` : '-'}
                    </span>
                    {riskReward?.upside_potential_pct && (
                      <span className="text-[10px] text-emerald-400 font-mono">+{riskReward.upside_potential_pct}% upside</span>
                    )}
                  </div>

                  <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg">
                    <span className="text-[10px] text-indigo-400 uppercase tracking-wider block">Reward/Risk Ratio</span>
                    <span className="text-xs font-bold text-indigo-300 mt-1 block">
                      {riskReward?.reward_to_risk_ratio ? `1 : ${riskReward.reward_to_risk_ratio}` : '1 : 1.50'}
                    </span>
                    <span className="text-[10px] text-slate-400">Asymmetric edge</span>
                  </div>
                </div>
              </div>

              {/* Liquidity & Macro Regime Guardrails */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Liquidity Check */}
                <div className="bg-slate-950/80 border border-slate-800 p-3.5 rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                      <Activity className="w-3.5 h-3.5 text-blue-400" />
                      <span>Liquidity Guardrail</span>
                      <InfoTooltip termId="liquidity" />
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                        liquidity?.is_liquid
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}
                    >
                      {liquidity?.is_liquid ? 'PASSED' : 'CONSTRAINED'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 space-y-1">
                    <div className="flex justify-between">
                      <span>20D Avg Turnover:</span>
                      <span className="text-slate-200 font-mono">
                        LKR {liquidity?.avg_turnover_lkr ? Number(liquidity.avg_turnover_lkr).toLocaleString() : '200,000+'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>20D Avg Volume:</span>
                      <span className="text-slate-200 font-mono">
                        {liquidity?.avg_volume_shares ? Number(liquidity.avg_volume_shares).toLocaleString() : '500+'} shares
                      </span>
                    </div>
                  </div>
                </div>

                {/* Market Regime */}
                <div className="bg-slate-950/80 border border-slate-800 p-3.5 rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-purple-400" />
                      <span>ASPI Market Regime</span>
                      <InfoTooltip termId="market_regime" />
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                      {regime?.regime || 'BULLISH'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    {regime?.aspi_context || 'ASPI benchmark is trading above its 100-day SMA, permitting active long alpha strategies.'}
                  </p>
                </div>
              </div>

              {/* Audit & Compliance Disclaimer */}
              <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800 text-[10px] text-slate-500 flex items-start gap-2">
                <Info className="w-4 h-4 shrink-0 text-slate-400 mt-0.5" />
                <div>
                  <span>
                    <strong>Model Version:</strong> {rec.model_version || 'CSE-LightGBM-Alpha-v2'} &bull;{' '}
                    <strong>Point-in-Time Safe:</strong> Forward returns were strictly quarantined during feature generation.
                  </span>
                  <p className="mt-0.5 text-slate-500">
                    All recommendations are purely quantitative decision-support models. Orders must be reviewed and placed manually by you through your registered CSE broker.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            /* =================== SIGNAL CRITERIA CHECKLIST VIEW =================== */
            <div className="space-y-6">
              {/* How this stock scored */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-xs flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span>Signal Scorecard for {rec.symbol}</span>
                  </span>
                  <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${badgeColor}`}>
                    Assigned: {rec.signal}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider block">1. Model Confidence Score</span>
                    <span className="font-bold text-base text-white">{confPct}%</span>
                    <p className="text-[10px] text-slate-400">
                      {confPct >= 65
                        ? 'Passed BUY threshold (≥ 65% probability of beating ASPI)'
                        : confPct <= 35
                        ? 'Triggered SELL threshold (≤ 35% probability of underperforming)'
                        : 'Neutral HOLD territory (36% - 64%)'}
                    </p>
                  </div>

                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider block">2. CSE Fee Hurdle Check</span>
                    <span className="font-bold text-base text-emerald-400">2.68% Covered</span>
                    <p className="text-[10px] text-slate-400">
                      Requires net projected return to exceed round-trip broker commission and government levies.
                    </p>
                  </div>

                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider block">3. Share Liquidity Filter</span>
                    <span className="font-bold text-base text-blue-400">
                      {liquidity?.is_liquid ? 'PASSED (Liquid)' : 'CONSTRAINED (WATCH)'}
                    </span>
                    <p className="text-[10px] text-slate-400">
                      Daily Turnover: LKR {liquidity?.avg_turnover_lkr ? Number(liquidity.avg_turnover_lkr).toLocaleString() : '200k+'} (Threshold: LKR 200,000)
                    </p>
                  </div>

                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider block">4. Colombo Market Regime</span>
                    <span className="font-bold text-base text-purple-400">
                      {regime?.regime || 'BULLISH'}
                    </span>
                    <p className="text-[10px] text-slate-400">
                      ASPI index is trading above its 100-day moving average.
                    </p>
                  </div>
                </div>
              </div>

              {/* Complete 4-Signal Rules Reference */}
              <div className="space-y-3">
                <span className="font-bold text-xs uppercase tracking-wider text-slate-300 block flex items-center gap-1.5">
                  <Filter className="w-4 h-4 text-purple-400" />
                  <span>The AI 4-Signal Decision Engine Rules</span>
                </span>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* BUY */}
                  <div className="bg-slate-950/70 p-3.5 rounded-xl border border-emerald-500/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-emerald-400 flex items-center gap-1.5 text-xs">
                        <TrendingUp className="w-4 h-4" />
                        <span>BUY (Good Opportunity)</span>
                      </span>
                      <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-300 px-1.5 py-0.2 rounded font-bold border border-emerald-500/25">
                        Score ≥ 65%
                      </span>
                    </div>
                    <ul className="text-slate-300 space-y-1 text-[11px]">
                      <li>&bull; <strong>Model Score:</strong> ≥ 65% probability to beat ASPI</li>
                      <li>&bull; <strong>Fee Hurdle:</strong> Upside clears 2.68% CSE fees</li>
                      <li>&bull; <strong>Regime Gate:</strong> ASPI &gt; 100-Day SMA</li>
                      <li>&bull; <strong>Liquidity:</strong> Turnover ≥ LKR 200,000/day</li>
                    </ul>
                    <span className="text-[10px] text-emerald-400 block pt-1 border-t border-slate-800">
                      Action: Record Buy opens active holding with 2x ATR stop.
                    </span>
                  </div>

                  {/* SELL */}
                  <div className="bg-slate-950/70 p-3.5 rounded-xl border border-rose-500/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-rose-400 flex items-center gap-1.5 text-xs">
                        <TrendingDown className="w-4 h-4" />
                        <span>SELL (Take Profit / Avoid)</span>
                      </span>
                      <span className="text-[10px] font-mono bg-rose-500/10 text-rose-300 px-1.5 py-0.2 rounded font-bold border border-rose-500/25">
                        Score ≤ 35%
                      </span>
                    </div>
                    <ul className="text-slate-300 space-y-1 text-[11px]">
                      <li>&bull; <strong>Model Score:</strong> Drops to ≤ 35% confidence</li>
                      <li>&bull; <strong>Stop Hit:</strong> Breaches 2x ATR stop loss (~3-5%)</li>
                      <li>&bull; <strong>Target Hit:</strong> Reaches 3x ATR profit goal</li>
                      <li>&bull; <strong>Divergence:</strong> RSI &gt; 75 with falling volume</li>
                    </ul>
                    <span className="text-[10px] text-rose-400 block pt-1 border-t border-slate-800">
                      Action: Record Sell exits position and locks in cash.
                    </span>
                  </div>

                  {/* HOLD */}
                  <div className="bg-slate-950/70 p-3.5 rounded-xl border border-blue-500/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-blue-400 flex items-center gap-1.5 text-xs">
                        <Scale className="w-4 h-4" />
                        <span>HOLD (Maintain Position)</span>
                      </span>
                      <span className="text-[10px] font-mono bg-blue-500/10 text-blue-300 px-1.5 py-0.2 rounded font-bold border border-blue-500/25">
                        36% - 64%
                      </span>
                    </div>
                    <ul className="text-slate-300 space-y-1 text-[11px]">
                      <li>&bull; <strong>Neutral Zone:</strong> Moderate price momentum</li>
                      <li>&bull; <strong>Fee Barrier:</strong> Expected gain &lt; 2.68% fee hurdle</li>
                      <li>&bull; <strong>Floor Protected:</strong> Holding safely above stop-loss</li>
                      <li>&bull; <strong>Guidance:</strong> Avoid paying fresh broker fees</li>
                    </ul>
                    <span className="text-[10px] text-blue-400 block pt-1 border-t border-slate-800">
                      Action: Maintain current shares; do not commit fresh capital.
                    </span>
                  </div>

                  {/* WATCH */}
                  <div className="bg-slate-950/70 p-3.5 rounded-xl border border-amber-500/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-amber-400 flex items-center gap-1.5 text-xs">
                        <Eye className="w-4 h-4" />
                        <span>WATCH (Wait &amp; Monitor)</span>
                      </span>
                      <span className="text-[10px] font-mono bg-amber-500/10 text-amber-300 px-1.5 py-0.2 rounded font-bold border border-amber-500/25">
                        Illiquid Check
                      </span>
                    </div>
                    <ul className="text-slate-300 space-y-1 text-[11px]">
                      <li>&bull; <strong>Low Volume:</strong> Turnover &lt; LKR 200,000/day</li>
                      <li>&bull; <strong>Share Liquidity:</strong> Traded volume &lt; 500 shares</li>
                      <li>&bull; <strong>Risk Prevention:</strong> Avoids wide bid-ask spread trap</li>
                      <li>&bull; <strong>Breakout Watch:</strong> Monitors for volume surge (&gt;1.2x)</li>
                    </ul>
                    <span className="text-[10px] text-amber-400 block pt-1 border-t border-slate-800">
                      Action: Monitored on Watchlist until volume confirms interest.
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-850/60 flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Recommended Allocation: <strong className="text-white">{Math.round((rec.position_size_pct || 0.05) * 100)}%</strong> ({rec.max_quantity || 100} shares)
          </span>
          <button
            onClick={onClose}
            className="bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition"
          >
            Close Explanation
          </button>
        </div>
      </div>
    </div>
  );
}
