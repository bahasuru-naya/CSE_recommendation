import React, { useState, useEffect } from 'react';
import {
  X,
  TrendingUp,
  TrendingDown,
  Calendar,
  BarChart3,
  Sparkles,
  Maximize2,
  Info,
  DollarSign,
  Activity,
} from 'lucide-react';
import { useSecurityPrices } from '../api/client';
import PriceChart from './PriceChart';
import CompanyLogo from './CompanyLogo';
import InfoTooltip from './InfoTooltip';

const TIMEFRAMES = [
  { label: '30 Days', days: 30 },
  { label: '60 Days', days: 60 },
  { label: '90 Days', days: 90 },
  { label: '180 Days', days: 180 },
  { label: '1 Year', days: 365 },
];

export default function PriceChartModal({
  symbol,
  name,
  logoUrl,
  isOpen,
  onClose,
  initialData,
}) {
  const [selectedDays, setSelectedDays] = useState(90);

  // Fetch price series for the selected symbol and timeframe
  const isCustomSeries = Array.isArray(initialData) && symbol === 'ASPI';
  const { data: fetchedData, isLoading } = useSecurityPrices(
    isCustomSeries ? null : symbol,
    selectedDays
  );

  const priceData = isCustomSeries ? initialData : fetchedData || [];

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose && onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'auto';
    };
  }, [isOpen, onClose]);

  if (!isOpen || !symbol) return null;

  // Calculate quick summary metrics from the price data
  const closes = priceData.map((d) => Number(d.close || 0)).filter((v) => v > 0);
  const volumes = priceData.map((d) => Number(d.volume || 0)).filter((v) => v > 0);

  const highestPrice = closes.length > 0 ? Math.max(...closes) : null;
  const lowestPrice = closes.length > 0 ? Math.min(...closes) : null;
  const latestPrice = closes.length > 0 ? closes[closes.length - 1] : null;
  const firstPrice = closes.length > 0 ? closes[0] : null;

  const priceChange = latestPrice && firstPrice ? latestPrice - firstPrice : 0;
  const priceChangePct = firstPrice && firstPrice > 0 ? (priceChange / firstPrice) * 100 : 0;
  const isPositive = priceChange >= 0;

  const avgDailyVolume =
    volumes.length > 0
      ? Math.round(volumes.reduce((a, b) => a + b, 0) / volumes.length)
      : null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-850/60">
          <div className="flex items-center gap-3.5">
            <CompanyLogo symbol={symbol} name={name} logoUrl={logoUrl} size="lg" />
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white">{symbol}</h2>
                {latestPrice && (
                  <span className="text-base font-extrabold text-blue-400 font-mono">
                    LKR {latestPrice.toFixed(2)}
                  </span>
                )}
                {priceChangePct !== 0 && (
                  <span
                    className={`inline-flex items-center gap-0.5 text-xs font-bold px-2 py-0.5 rounded-full border ${
                      isPositive
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                    }`}
                  >
                    {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                    <span>{isPositive ? '+' : ''}{priceChangePct.toFixed(2)}%</span>
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">{name || 'Colombo Stock Exchange'}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Timeframe selector pills */}
            {!isCustomSeries && (
              <div className="hidden sm:flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
                {TIMEFRAMES.map((tf) => (
                  <button
                    key={tf.days}
                    onClick={() => setSelectedDays(tf.days)}
                    className={`px-2.5 py-1 rounded-md font-medium transition ${
                      selectedDays === tf.days
                        ? 'bg-blue-600 text-white shadow'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {tf.label}
                  </button>
                ))}
              </div>
            )}

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              title="Close window (Esc)"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="overflow-y-auto p-6 space-y-5">
          {/* Mobile Timeframe Selector */}
          {!isCustomSeries && (
            <div className="flex sm:hidden justify-center bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
              {TIMEFRAMES.map((tf) => (
                <button
                  key={tf.days}
                  onClick={() => setSelectedDays(tf.days)}
                  className={`flex-1 py-1 rounded-md font-medium transition text-center ${
                    selectedDays === tf.days
                      ? 'bg-blue-600 text-white shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {tf.label.replace(' Days', 'D').replace('1 Year', '1Y')}
                </button>
              ))}
            </div>
          )}

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">
                Period High
              </span>
              <span className="text-sm font-bold text-slate-100 mt-0.5 block">
                {highestPrice ? `LKR ${highestPrice.toFixed(2)}` : '—'}
              </span>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">
                Period Low
              </span>
              <span className="text-sm font-bold text-slate-100 mt-0.5 block">
                {lowestPrice ? `LKR ${lowestPrice.toFixed(2)}` : '—'}
              </span>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">
                Avg Daily Volume
              </span>
              <span className="text-sm font-bold text-slate-100 mt-0.5 block">
                {avgDailyVolume ? `${avgDailyVolume.toLocaleString()} shares` : '—'}
              </span>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">
                Period Net Change
              </span>
              <span
                className={`text-sm font-bold mt-0.5 block ${
                  isPositive ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {priceChange !== 0 ? `${isPositive ? '+' : ''}LKR ${priceChange.toFixed(2)}` : '—'}
              </span>
            </div>
          </div>

          {/* Chart Display */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
            {isLoading ? (
              <div className="h-72 flex items-center justify-center text-slate-500 text-sm">
                Loading price history...
              </div>
            ) : priceData.length === 0 ? (
              <div className="h-72 flex items-center justify-center text-slate-500 text-sm">
                No historical price records found for this period.
              </div>
            ) : (
              <PriceChart
                data={priceData}
                title={`${symbol} Price & Volume (${selectedDays} Days)`}
              />
            )}
          </div>

          {/* In Plain English Educational Callout */}
          <div className="bg-blue-950/30 border border-blue-500/20 rounded-xl p-3.5 flex items-start gap-3 text-xs text-slate-300">
            <Sparkles className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-white block">
                How to read this chart (Beginner Guide):
              </span>
              <p className="text-slate-300 leading-relaxed text-[11px]">
                The <strong>blue line</strong> tracks the official closing price at 14:30 each trading day in Colombo.
                The <strong>grey vertical bars</strong> at the bottom show trading volume (how many shares people bought and sold).
                When a price rises with tall volume bars, it means lots of buyers are actively pushing the price up.
              </p>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-850/60 flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Official EOD prices from Colombo Stock Exchange (Asia/Colombo)
          </span>
          <button
            onClick={onClose}
            className="bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition"
          >
            Close Window
          </button>
        </div>
      </div>
    </div>
  );
}
