import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, TrendingDown, Eye, CheckCircle2, XCircle, ShieldAlert, Brain, Sparkles, HelpCircle, Loader2, Bookmark } from 'lucide-react';
import { useExecuteRecommendation } from '../api/client';
import CompanyLogo from './CompanyLogo';
import ExplainabilityModal from './ExplainabilityModal';
import PriceChartModal from './PriceChartModal';
import InfoTooltip from './InfoTooltip';
import { useBeginnerMode } from './BeginnerModeContext';
import { getFeatureMeta } from '../data/featureMetadata';

export default function RecommendationCard({ rec, onSelectSymbol }) {
  const executeMutation = useExecuteRecommendation();
  const [showExplain, setShowExplain] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const [recorded, setRecorded] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const { isBeginnerMode } = useBeginnerMode();

  const isBuy = rec.signal === 'BUY';
  const isSell = rec.signal === 'SELL';
  const isWatch = rec.signal === 'WATCH';
  const isHold = rec.signal === 'HOLD';

  // If user actively holds open shares for this stock in Portfolio, mark it as tracked
  const isAlreadyTracked = Boolean(isBuy && rec.has_open_position);
  const isActionDone = recorded || isAlreadyTracked;

  const handleOpenChart = () => {
    if (onSelectSymbol) {
      onSelectSymbol(rec.symbol);
    } else {
      setShowChart(true);
    }
  };

  const handleRecordTrade = () => {
    executeMutation.mutate(rec.id, {
      onSuccess: (res) => {
        setRecorded(true);
        const msg = res?.data?.action || res?.data?.message || 'Trade recorded in Portfolio!';
        setFeedback({ type: 'success', message: msg });
        setTimeout(() => setFeedback(null), 6000);
      },
      onError: (err) => {
        const errMsg = err?.response?.data?.detail || err.message || 'Failed to record trade. Please try again.';
        setFeedback({ type: 'error', message: errMsg });
        setTimeout(() => setFeedback(null), 5000);
      },
    });
  };

  const badgeColor = isBuy
    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
    : isSell
    ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
    : isWatch
    ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
    : isHold
    ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
    : 'bg-slate-700/30 text-slate-400 border-slate-700';

  const signalLabel = isBuy
    ? 'BUY (Good Opportunity)'
    : isSell
    ? 'SELL (Take Profit / Avoid)'
    : isWatch
    ? 'WATCH (Wait & Monitor)'
    : isHold
    ? 'HOLD'
    : rec.signal;

  const progressBarColor = isBuy
    ? 'bg-emerald-500'
    : isSell
    ? 'bg-rose-500'
    : isWatch
    ? 'bg-amber-500'
    : isHold
    ? 'bg-blue-500'
    : 'bg-slate-500';

  const confPct = Math.round((rec.confidence || 0.5) * 100);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition shadow-lg flex flex-col justify-between">
      <div>
        {/* Top Header */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <CompanyLogo symbol={rec.symbol} name={rec.name} logoUrl={rec.logo_url} size="md" />
            <div className="min-w-0">
              <span
                onClick={handleOpenChart}
                className="font-bold text-lg text-white hover:text-blue-400 cursor-pointer transition block truncate"
                title="Click to view price chart pop-up"
              >
                {rec.symbol}
              </span>
              <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{rec.name || rec.security_name || rec.symbol}</p>
            </div>
          </div>

          <div className="text-right shrink-0 pl-2">
            <div className="flex items-center justify-end gap-1 text-xs font-medium text-slate-400">
              <span>Model Conf.</span>
              <InfoTooltip termId="confidence" />
            </div>
            <div className="text-sm font-bold text-slate-200">{confPct}%</div>
          </div>
        </div>

        {/* Signal Badge: Right of new line before progress bar */}
        <div className="flex items-center justify-end mb-2">
          <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${badgeColor}`}>
            {signalLabel}
          </span>
        </div>

        {/* Confidence Progress Bar */}
        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mb-4">
          <div
            className={`h-full ${progressBarColor}`}
            style={{ width: `${confPct}%` }}
          ></div>
        </div>

        {/* Key Trade Parameters with Tooltips */}
        <div className="grid grid-cols-3 gap-2 bg-slate-850 p-3 rounded-lg border border-slate-800/80 mb-3 text-center">
          <div>
            <div className="text-[11px] text-slate-400 flex items-center justify-center gap-1">
              <span>Entry Range</span>
              <InfoTooltip termId="entry_range" />
            </div>
            <div className="text-xs font-semibold text-slate-200 mt-0.5">
              {rec.entry_price_low ? `LKR ${rec.entry_price_low}` : '-'}
            </div>
          </div>
          <div>
            <div className="text-[11px] text-rose-400 flex items-center justify-center gap-1">
              <span>Stop Loss</span>
              <InfoTooltip termId="stop_loss" />
            </div>
            <div className="text-xs font-semibold text-rose-300 mt-0.5">
              {rec.stop_loss ? `LKR ${rec.stop_loss}` : '-'}
            </div>
          </div>
          <div>
            <div className="text-[11px] text-emerald-400 flex items-center justify-center gap-1">
              <span>Target</span>
              <InfoTooltip termId="target_price" />
            </div>
            <div className="text-xs font-semibold text-emerald-300 mt-0.5">
              {rec.target_price ? `LKR ${rec.target_price}` : '-'}
            </div>
          </div>
        </div>

        {/* Allocation */}
        <div className="flex items-center justify-between text-xs text-slate-400 mb-3 px-1">
          <span className="flex items-center gap-1">
            <span>Max Shares: <strong className="text-slate-200">{rec.max_quantity || 100}</strong></span>
            <InfoTooltip termId="position_sizing" />
          </span>
          <span>Budget Sizing: <strong className="text-slate-200">{Math.round((rec.position_size_pct || 0.05) * 100)}%</strong></span>
        </div>

        {/* Beginner-friendly "In Simple Words" Advice Box */}
        {isBeginnerMode && (
          <div className="bg-blue-950/20 border border-blue-500/20 rounded-lg p-2.5 mb-3 text-[11px] text-blue-200 space-y-1">
            <div className="font-bold flex items-center gap-1 text-blue-300">
              <Sparkles className="w-3 h-3 text-amber-400" />
              <span>What should I do?</span>
            </div>
            {isBuy ? (
              <p className="text-slate-300 leading-relaxed">
                Buy between <strong className="text-white">LKR {rec.entry_price_low || rec.entry_price || '-'}</strong>. Set a safety stop at <strong className="text-rose-300">LKR {rec.stop_loss || '-'}</strong>. Aim to take profit at <strong className="text-emerald-300">LKR {rec.target_price || '-'}</strong>.
              </p>
            ) : isSell ? (
              <p className="text-slate-300 leading-relaxed">
                If you already own this stock, consider selling to lock in your money. Avoid buying new shares today.
              </p>
            ) : isHold ? (
              <p className="text-slate-300 leading-relaxed">
                Hold existing shares. No urgent action is needed today while the price consolidates.
              </p>
            ) : (
              <p className="text-slate-300 leading-relaxed">
                Keep this stock on your watchlist. Do not buy yet until the price settles into the entry range.
              </p>
            )}
          </div>
        )}

        {/* AI Summary or SHAP Factors teaser */}
        {rec.reasons && (() => {
          const isStructured = rec.reasons && !Array.isArray(rec.reasons) && rec.reasons.summary;
          const factorsList = isStructured
            ? rec.reasons.factors || []
            : Array.isArray(rec.reasons)
            ? rec.reasons
            : [];

          if (isStructured || factorsList.length > 0) {
            return (
              <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60 mb-4 space-y-2">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                  <span className="flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-purple-400" />
                    <span>AI Decision Clues</span>
                  </span>
                  <InfoTooltip termId="shap" />
                </div>

                {isStructured && rec.reasons.summary && (
                  <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                    {rec.reasons.summary}
                  </p>
                )}

                {factorsList.length > 0 && (
                  <div className="pt-1.5 border-t border-slate-800/80 space-y-1.5">
                    <span className="text-[10px] font-medium text-slate-400 block">Top Contributing Factors:</span>
                    {factorsList.slice(0, 2).map((r, i) => {
                      const meta = getFeatureMeta(r.feature);
                      const isPositive = (r.impact !== undefined && r.impact >= 0) || r.direction === 'bullish';
                      const title = r.display_name && !r.display_name.includes('_')
                        ? r.display_name
                        : meta.name;

                      return (
                        <div key={i} className="bg-slate-900/80 p-1.5 rounded border border-slate-800 flex items-center justify-between gap-2">
                          <div className="truncate">
                            <span className="text-xs font-medium text-white truncate block">
                              {title}
                            </span>
                            <span className="text-[10px] text-slate-400 truncate block">
                              {meta.simpleDescription}
                            </span>
                          </div>
                          <div className="shrink-0 text-right">
                            {r.impact !== undefined && (
                              <span className={`text-[10px] font-mono font-bold ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {isPositive ? `+${Math.abs(r.impact).toFixed(2)}` : `-${Math.abs(r.impact).toFixed(2)}`}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          }
          return null;
        })()}
      </div>

      {/* Action Buttons */}
      <div className="pt-2 border-t border-slate-800 space-y-2">
        <div className="flex items-center gap-2">
          <button
            onClick={handleRecordTrade}
            disabled={executeMutation.isPending || isActionDone}
            className={`flex-1 text-xs font-semibold py-2 px-3 rounded-lg transition flex items-center justify-center gap-1.5 ${
              isActionDone
                ? 'bg-emerald-600/20 text-emerald-300 border border-emerald-500/40 cursor-default'
                : 'bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 text-white shadow-sm'
            }`}
            title={
              isActionDone
                ? isBuy
                  ? 'Active open holding tracked in Portfolio'
                  : isSell
                  ? 'Exit trade logged in Portfolio'
                  : 'Tracked in Monitored Watchlist'
                : isWatch || isHold
                ? 'Add this stock to your Monitored Watchlist in Portfolio'
                : isSell
                ? rec.has_open_position
                  ? 'Sell / close your active open holding in Portfolio'
                  : 'Record exited sell trade in Portfolio'
                : 'Record this buy trade in your portfolio tracker (Note: Place real orders through your CSE stockbroker)'
            }
          >
            {executeMutation.isPending ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>{isWatch || isHold ? 'Saving...' : 'Recording...'}</span>
              </>
            ) : isActionDone ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>
                  {isBuy
                    ? 'Tracked in Portfolio'
                    : isSell
                    ? 'Exit Logged'
                    : 'In Watchlist'}
                </span>
              </>
            ) : isBuy ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Record Buy</span>
              </>
            ) : isSell ? (
              <>
                <TrendingDown className="w-3.5 h-3.5 text-rose-300" />
                <span>{rec.has_open_position ? 'Record Sell (Close Holding)' : 'Record Sell'}</span>
              </>
            ) : isWatch ? (
              <>
                <Bookmark className="w-3.5 h-3.5 text-amber-300" />
                <span>Add to Watchlist</span>
              </>
            ) : (
              <>
                <Bookmark className="w-3.5 h-3.5 text-blue-300" />
                <span>Track in Watchlist</span>
              </>
            )}
          </button>

          <button
            onClick={() => setShowExplain(true)}
            className="bg-violet-900/50 hover:bg-violet-800/70 text-violet-300 text-xs font-medium py-2 px-3 rounded-lg transition flex items-center justify-center gap-1 border border-violet-700/40"
            title="Explain this recommendation in plain English"
          >
            <Brain className="w-3.5 h-3.5" />
            <span>Explain</span>
          </button>

          <button
            onClick={handleOpenChart}
            className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium py-2 px-3 rounded-lg transition flex items-center justify-center gap-1"
            title="Open price chart in pop-up window"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Chart</span>
          </button>
        </div>

        {/* Feedback message */}
        {feedback && (
          <div
            className={`p-2 rounded text-[11px] flex items-center justify-between gap-2 border animate-fade-in ${
              feedback.type === 'success'
                ? 'bg-emerald-950/70 border-emerald-800 text-emerald-300'
                : 'bg-rose-950/70 border-rose-800 text-rose-300'
            }`}
          >
            <div className="flex items-center gap-1.5 min-w-0">
              {feedback.type === 'success' ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              ) : (
                <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
              )}
              <span className="truncate">{feedback.message}</span>
            </div>
            {feedback.type === 'success' && (
              <Link
                to="/portfolio"
                className="text-blue-300 hover:text-white font-semibold underline shrink-0 text-[10px] flex items-center gap-0.5"
              >
                <span>View Portfolio</span>
                <span>&rarr;</span>
              </Link>
            )}
          </div>
        )}
      </div>

      {/* Explainability Modal */}
      <ExplainabilityModal rec={rec} isOpen={showExplain} onClose={() => setShowExplain(false)} />

      {/* Price Chart Pop-up Window */}
      <PriceChartModal
        symbol={rec.symbol}
        name={rec.name || rec.security_name}
        logoUrl={rec.logo_url}
        isOpen={showChart}
        onClose={() => setShowChart(false)}
      />
    </div>
  );
}
