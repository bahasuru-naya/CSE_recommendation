import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  useRecommendations,
  usePortfolio,
  useMarketIndices,
  usePipelineStatus,
  useSecurityPrices,
} from '../api/client';
import RecommendationCard from '../components/RecommendationCard';
import PriceChart from '../components/PriceChart';
import PriceChartModal from '../components/PriceChartModal';
import SignalCriteriaModal from '../components/SignalCriteriaModal';
import DataStatus from '../components/DataStatus';
import InfoTooltip from '../components/InfoTooltip';
import { useBeginnerMode } from '../components/BeginnerModeContext';
import {
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Wallet,
  Activity,
  ShieldCheck,
  GraduationCap,
  Sparkles,
  BookOpen,
  ArrowRight,
  Info,
  Brain,
} from 'lucide-react';

export default function Dashboard() {
  const [chartModalSymbol, setChartModalSymbol] = useState(null);
  const [showCriteriaModal, setShowCriteriaModal] = useState(false);
  const { isBeginnerMode } = useBeginnerMode();

  const { data: recData, isLoading: recLoading } = useRecommendations();
  const { data: portData } = usePortfolio();
  const { data: indicesData } = useMarketIndices(30);
  const { data: pipelineData } = usePipelineStatus();

  const recsRaw = recData?.data || [];
  const seenDashSymbols = new Set();
  const recs = recsRaw.filter((r) => {
    const sym = (r.symbol || '').trim().toUpperCase();
    if (!sym || seenDashSymbols.has(sym)) return false;
    seenDashSymbols.add(sym);
    return true;
  });
  const buyCount = recs.filter((r) => r.signal === 'BUY').length;
  const sellCount = recs.filter((r) => r.signal === 'SELL').length;
  const portSummary = portData?.summary;
  const regimeInfo = recs[0]?.reasons?.regime;
  const isMarketBullish = regimeInfo?.regime !== 'BEARISH';

  // Format index chart data
  const aspiSeries = (indicesData || [])
    .filter((d) => d.index_name === 'ASPI')
    .map((d) => ({ date: d.date, close: d.close }));

  return (
    <div className="space-y-6">
      {/* Beginner Welcome Banner */}
      {isBeginnerMode && (
        <div className="bg-gradient-to-r from-blue-950/60 via-slate-900 to-indigo-950/40 border border-blue-500/30 rounded-2xl p-5 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-[11px] font-semibold flex items-center gap-1 border border-blue-500/30">
                <Sparkles className="w-3 h-3 text-amber-400" />
                <span>Beginner Overview</span>
              </span>
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <span>Today's Market Status:</span>
                <span className={`inline-flex items-center gap-1.5 font-semibold ${isMarketBullish ? 'text-emerald-400' : 'text-rose-400'}`}>
                  <span className={`w-2 h-2 rounded-full ${isMarketBullish ? 'bg-emerald-400 ring-2 ring-emerald-400/30' : 'bg-rose-400 ring-2 ring-rose-400/30'}`} />
                  <span>{isMarketBullish ? 'Bullish (Growing)' : 'Bearish (Caution)'}</span>
                </span>
              </div>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed">
              Welcome! The AI has scanned all 290+ CSE stocks today. Currently, there are <strong className="text-emerald-300">{buyCount} BUY opportunities</strong> meeting strict risk and fee thresholds. Click on any card below to see the recommended buy price, safety stop, and target profit.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Link
              to="/guide"
              className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-md shadow-blue-600/20"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Stock Market 101 Guide</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Signals */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="flex items-center gap-1">
              <span>Signals Available</span>
              <InfoTooltip termId="signal_buy" />
            </span>
            <TrendingUp className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white mb-2">{recs.length}</div>
          <div className="flex items-center gap-3 text-xs">
            <span className="text-emerald-400 font-medium">{buyCount} BUY</span>
            <span className="text-rose-400 font-medium">{sellCount} SELL</span>
            <span className="text-slate-400 font-medium">{recs.length - buyCount - sellCount} NEUTRAL</span>
          </div>
        </div>

        {/* Portfolio Value */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="flex items-center gap-1">
              <span>Portfolio Valuation</span>
              <InfoTooltip termId="portfolio_valuation" />
            </span>
            <Wallet className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white mb-2">
            LKR {Number(portSummary?.portfolio_value ?? 1000000).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Open: <span className="font-semibold text-slate-200">{portSummary?.open_positions || 0}</span></span>
            <span>•</span>
            <span>Closed: <span className="font-semibold text-slate-200">{portSummary?.closed_positions || 0}</span></span>
          </div>
        </div>

        {/* Profit & Loss */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="flex items-center gap-1">
              <span>{portSummary?.open_positions > 0 ? 'Total Profit & Loss' : 'Realized Gain / Loss'}</span>
              <InfoTooltip termId="unrealized_pnl" />
            </span>
            {((portSummary?.total_pnl ?? portSummary?.realized_pnl ?? portSummary?.unrealized_pnl) || 0) >= 0 ? (
              <ArrowUpRight className="w-4 h-4 text-emerald-400" />
            ) : (
              <ArrowDownRight className="w-4 h-4 text-rose-400" />
            )}
          </div>
          <div
            className={`text-2xl font-bold mb-2 ${
              ((portSummary?.total_pnl ?? portSummary?.realized_pnl ?? portSummary?.unrealized_pnl) || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {((portSummary?.total_pnl ?? portSummary?.realized_pnl ?? portSummary?.unrealized_pnl) || 0) >= 0 ? '+' : ''}
            LKR {Number((portSummary?.total_pnl ?? portSummary?.realized_pnl ?? portSummary?.unrealized_pnl) || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-400">
            {portSummary?.open_positions > 0
              ? `Paper: ${Number(portSummary?.unrealized_pnl || 0) >= 0 ? '+' : ''}LKR ${Number(portSummary?.unrealized_pnl || 0).toFixed(2)} • Realized: ${Number(portSummary?.realized_pnl || 0) >= 0 ? '+' : ''}LKR ${Number(portSummary?.realized_pnl || 0).toFixed(2)}`
              : `${Number(portSummary?.realized_pnl || 0) >= 0 ? '+' : ''}${Number(portSummary?.realized_pnl_pct || 0).toFixed(2)}% locked profit from ${portSummary?.closed_positions || 0} closed trades`}
          </div>
        </div>

        {/* System Risk Regime */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="flex items-center gap-1">
              <span>Market Regime</span>
              <InfoTooltip termId="market_regime" />
            </span>
            <ShieldCheck className="w-4 h-4 text-purple-400" />
          </div>
          <div className={`text-2xl font-bold mb-2 ${regimeInfo?.regime === 'BEARISH' ? 'text-rose-400' : 'text-emerald-400'}`}>
            {regimeInfo?.regime || 'BULLISH'}
          </div>
          <div className="text-xs text-slate-400">
            {regimeInfo?.aspi_context || 'ASPI trending above 100-day SMA'}
          </div>
        </div>
      </div>

      {/* Main Grid: Charts & Lakehouse Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* ASPI Index Trend */}
          <PriceChart
            data={aspiSeries}
            title="ASPI Benchmark Index (Last 30 Days)"
            onExpand={() => setChartModalSymbol('ASPI')}
          />
        </div>

        <div className="space-y-6">
          {/* Lakehouse Data Status */}
          <DataStatus pipelineData={pipelineData} />

          {/* Quick CSE Market Info */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <h3 className="font-semibold text-sm text-slate-200 mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Trading Rhythm (Colombo Time)</span>
            </h3>
            <ul className="space-y-2 text-xs text-slate-400">
              <li className="flex items-center justify-between py-1 border-b border-slate-800">
                <span>Intraday Snapshot</span>
                <span className="font-mono text-slate-300">Every 5 mins</span>
              </li>
              <li className="flex items-center justify-between py-1 border-b border-slate-800">
                <span>EOD Data Landing</span>
                <span className="font-mono text-slate-300">14:45</span>
              </li>
              <li className="flex items-center justify-between py-1 border-b border-slate-800">
                <span>Features &amp; Scoring</span>
                <span className="font-mono text-slate-300">15:00</span>
              </li>
              <li className="flex items-center justify-between py-1">
                <span>Weekly Retrain &amp; Audit</span>
                <span className="font-mono text-slate-300">Saturday</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Top Actionable Recommendations */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span>Top Stock Recommendations</span>
              <InfoTooltip termId="signal_buy" />
            </h2>
            <p className="text-xs text-slate-400">
              {isBeginnerMode
                ? 'High-confidence stocks analyzed by AI. Each card gives you a recommended buy price, safety stop, and target profit.'
                : 'Calibrated alpha predictions beat round-trip costs net of CSE brokerage fees.'}
            </p>
          </div>
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              onClick={() => setShowCriteriaModal(true)}
              className="text-xs text-purple-300 hover:text-purple-200 bg-purple-500/15 hover:bg-purple-500/25 px-2.5 py-1.5 rounded-lg border border-purple-500/30 font-semibold flex items-center gap-1.5 transition"
              title="See exact criteria for BUY, SELL, HOLD, and WATCH"
            >
              <Brain className="w-3.5 h-3.5 text-purple-400" />
              <span>How Signals Work</span>
            </button>
            <Link
              to="/recommendations"
              className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 bg-slate-900 hover:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-800 transition"
            >
              <span>View All ({recs.length}) Signals</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {recLoading ? (
          <div className="h-40 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center text-slate-500 text-sm">
            Evaluating quantitative models...
          </div>
        ) : recs.length === 0 ? (
          <div className="h-40 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center text-slate-500 text-sm">
            No active signals today. Market regime or liquidity filter triggered "No Edge".
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {recs.slice(0, 6).map((rec) => (
              <RecommendationCard
                key={rec.id}
                rec={rec}
                onSelectSymbol={(sym) => setChartModalSymbol(sym)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Price Chart Pop-up Window */}
      <PriceChartModal
        symbol={chartModalSymbol}
        name={chartModalSymbol === 'ASPI' ? 'All Share Price Index (Colombo)' : undefined}
        isOpen={!!chartModalSymbol}
        onClose={() => setChartModalSymbol(null)}
        initialData={chartModalSymbol === 'ASPI' ? aspiSeries : undefined}
      />

      {/* Signal Determination Criteria Modal */}
      <SignalCriteriaModal
        isOpen={showCriteriaModal}
        onClose={() => setShowCriteriaModal(false)}
      />
    </div>
  );
}
