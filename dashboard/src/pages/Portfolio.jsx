import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { usePortfolio, useAddPosition, useAddWatchlist, useRemoveWatchlist } from '../api/client';
import PortfolioTable from '../components/PortfolioTable';
import CompanyLogo from '../components/CompanyLogo';
import InfoTooltip from '../components/InfoTooltip';
import PriceChartModal from '../components/PriceChartModal';
import { useBeginnerMode } from '../components/BeginnerModeContext';
import { PlusCircle, Bookmark, DollarSign, Wallet, TrendingUp, Trash2, Eye, HelpCircle, Sparkles, Info, ArrowRight, X, CheckCircle2 } from 'lucide-react';

export default function Portfolio() {
  const { data: portData, isLoading } = usePortfolio();
  const addPositionMutation = useAddPosition();
  const addWatchlistMutation = useAddWatchlist();
  const removeWatchlistMutation = useRemoveWatchlist();
  const { isBeginnerMode } = useBeginnerMode();

  const [positionFilter, setPositionFilter] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showWatchModal, setShowWatchModal] = useState(false);
  const [chartModalSymbol, setChartModalSymbol] = useState(null);
  const [posError, setPosError] = useState(null);
  const [watchError, setWatchError] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);
  const [watchForm, setWatchForm] = useState({ symbol: '', reason: '', alert_price_above: '', alert_price_below: '' });
  const [formData, setFormData] = useState({
    symbol: '',
    entry_price: '',
    quantity: '',
    stop_loss: '',
    target_price: '',
    notes: '',
  });

  const handleWatchSubmit = (e) => {
    e.preventDefault();
    setWatchError(null);
    const sym = (watchForm.symbol || '').trim().toUpperCase();
    if (!sym) {
      setWatchError('Please enter a valid stock symbol.');
      return;
    }

    addWatchlistMutation.mutate(
      {
        symbol: sym,
        reason: watchForm.reason || 'Technical observation',
        alert_price_above: watchForm.alert_price_above ? parseFloat(watchForm.alert_price_above) : null,
        alert_price_below: watchForm.alert_price_below ? parseFloat(watchForm.alert_price_below) : null,
      },
      {
        onSuccess: (res) => {
          setShowWatchModal(false);
          setWatchForm({ symbol: '', reason: '', alert_price_above: '', alert_price_below: '' });
          setWatchError(null);
          setToastMessage(`Added ${sym} to your monitored watchlist!`);
          setTimeout(() => setToastMessage(null), 4000);
        },
        onError: (err) => {
          setWatchError(err?.response?.data?.detail || err.message || 'Failed to add to watchlist.');
        },
      }
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setPosError(null);
    const sym = (formData.symbol || '').trim().toUpperCase();
    const price = parseFloat(formData.entry_price);
    const qty = parseInt(formData.quantity, 10);

    if (!sym) {
      setPosError('Please enter a stock symbol.');
      return;
    }
    if (isNaN(price) || price <= 0) {
      setPosError('Bought price per share must be greater than zero.');
      return;
    }
    if (isNaN(qty) || qty <= 0) {
      setPosError('Number of shares must be at least 1.');
      return;
    }

    addPositionMutation.mutate(
      {
        symbol: sym,
        entry_price: price,
        quantity: qty,
        stop_loss: formData.stop_loss ? parseFloat(formData.stop_loss) : null,
        target_price: formData.target_price ? parseFloat(formData.target_price) : null,
        notes: formData.notes,
      },
      {
        onSuccess: () => {
          setShowAddModal(false);
          setFormData({ symbol: '', entry_price: '', quantity: '', stop_loss: '', target_price: '', notes: '' });
          setPosError(null);
          setPositionFilter('open');
          setToastMessage(`Recorded ${qty.toLocaleString()} shares of ${sym} into your active holdings!`);
          setTimeout(() => setToastMessage(null), 4000);
        },
        onError: (err) => {
          setPosError(err?.response?.data?.detail || err.message || 'Failed to record trade. Please check values.');
        },
      }
    );
  };

  const positions = portData?.positions || [];
  const summary = portData?.summary;
  const watchlist = portData?.watchlist || [];

  const openPositions = positions.filter((p) => p.status === 'open');
  const closedPositions = positions.filter((p) => p.status === 'closed');
  const filteredPositions =
    positionFilter === 'open'
      ? openPositions
      : positionFilter === 'closed'
      ? closedPositions
      : positions;

  return (
    <div className="space-y-6">
      {/* Toast Notification Banner */}
      {toastMessage && (
        <div className="bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 px-4 py-2.5 rounded-xl text-xs flex items-center justify-between shadow-lg animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="font-medium">{toastMessage}</span>
          </div>
          <button onClick={() => setToastMessage(null)} className="text-emerald-400 hover:text-white p-1 rounded transition" title="Dismiss">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <span>Portfolio &amp; Risk Monitor</span>
            <InfoTooltip termId="portfolio_valuation" />
          </h1>
          <p className="text-xs text-slate-400">
            {isBeginnerMode
              ? 'Track your stock investments, paper gains, safety stop losses, and watchlist in one place.'
              : 'Track actual executed positions, unrealized P&L, stops, and watchlist targets.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setWatchError(null);
              setShowWatchModal(true);
            }}
            className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-200 text-xs font-semibold px-3.5 py-2 rounded-lg transition"
          >
            <Bookmark className="w-4 h-4 text-amber-400" />
            <span>Add Watchlist</span>
          </button>

          <button
            onClick={() => {
              setPosError(null);
              setShowAddModal(true);
            }}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3.5 py-2 rounded-lg transition shadow-md shadow-blue-600/20"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Record Trade</span>
          </button>
        </div>
      </div>

      {/* Beginner Note */}
      {isBeginnerMode && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 text-xs text-slate-300 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-white">Note for Beginners:</strong> This portfolio tracks your positions on paper.
            To buy or sell actual company shares with real money, place your orders through your registered Sri Lankan stockbroker (e.g. CAL, Asha, CT CLSA).
          </div>
        </div>
      )}

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1">
            <span>Portfolio Valuation</span>
            <InfoTooltip termId="portfolio_valuation" />
          </div>
          <div className="text-2xl font-bold text-white">
            LKR {Number(summary?.portfolio_value ?? 1000000).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Cash: LKR {Number(summary?.cash_balance ?? 1000000).toLocaleString('en-US', { minimumFractionDigits: 2 })} • Holdings: LKR {Number(summary?.holdings_value || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1">
            <span>{openPositions.length > 0 ? 'Total Profit & Loss' : 'Realized Gain / Loss'}</span>
            <InfoTooltip termId="unrealized_pnl" />
          </div>
          <div
            className={`text-2xl font-bold ${
              ((summary?.total_pnl ?? summary?.realized_pnl ?? summary?.unrealized_pnl) || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {((summary?.total_pnl ?? summary?.realized_pnl ?? summary?.unrealized_pnl) || 0) >= 0 ? '+' : ''}
            LKR {Number((summary?.total_pnl ?? summary?.realized_pnl ?? summary?.unrealized_pnl) || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {openPositions.length > 0
              ? `Paper: ${Number(summary?.unrealized_pnl || 0) >= 0 ? '+' : ''}LKR ${Number(summary?.unrealized_pnl || 0).toFixed(2)} • Realized: ${Number(summary?.realized_pnl || 0) >= 0 ? '+' : ''}LKR ${Number(summary?.realized_pnl || 0).toFixed(2)}`
              : `${Number(summary?.realized_pnl || 0) >= 0 ? '+' : ''}${Number(summary?.realized_pnl_pct || 0).toFixed(2)}% locked profit from ${closedPositions.length} closed trades`}
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1">
            <span>Active Positions</span>
            <InfoTooltip termId="position_sizing" />
          </div>
          <div className="text-2xl font-bold text-white">{openPositions.length}</div>
          <p className="text-xs text-slate-400 mt-1">{closedPositions.length} closed / exited trades logged</p>
        </div>
      </div>

      {/* Positions Table with Active / Closed / All Filter */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-white">Holdings &amp; Trade Records</h2>
            <span className="text-xs text-slate-400 font-medium">({filteredPositions.length})</span>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1 bg-slate-850 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setPositionFilter('all')}
              className={`px-3 py-1 rounded-md font-medium transition ${
                positionFilter === 'all'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All Records ({positions.length})
            </button>
            <button
              onClick={() => setPositionFilter('open')}
              className={`px-3 py-1 rounded-md font-medium transition ${
                positionFilter === 'open'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Active Holdings ({openPositions.length})
            </button>
            <button
              onClick={() => setPositionFilter('closed')}
              className={`px-3 py-1 rounded-md font-medium transition ${
                positionFilter === 'closed'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Closed / Exited ({closedPositions.length})
            </button>
          </div>
        </div>

        {positionFilter === 'open' && openPositions.length === 0 && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center space-y-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center mx-auto">
              <PlusCircle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">No Active Open Holdings</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
                You currently have no open stock positions. When you buy shares, record them here to track live profit/loss and safety stop-loss levels.
              </p>
            </div>
            <div className="flex items-center justify-center gap-3 pt-1">
              <button
                onClick={() => {
                  setPosError(null);
                  setShowAddModal(true);
                }}
                className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow flex items-center gap-1.5"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>+ Record Trade Manually</span>
              </button>
              <Link
                to="/recommendations"
                className="bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-semibold px-4 py-2 rounded-lg transition border border-slate-700 flex items-center gap-1.5"
              >
                <span>View BUY Opportunities</span>
                <ArrowRight className="w-3.5 h-3.5 text-blue-400" />
              </Link>
            </div>
          </div>
        )}

        <PortfolioTable positions={filteredPositions} />
      </div>

      {/* Watchlist Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Bookmark className="w-4 h-4 text-amber-400" />
            <span>Monitored Watchlist ({watchlist.length})</span>
          </h2>
          <button
            onClick={() => setShowWatchModal(true)}
            className="text-xs text-amber-400 hover:text-amber-300 font-medium"
          >
            + Add Stock
          </button>
        </div>
        {watchlist.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-500 text-xs">
            Watchlist is empty. Click &quot;Add Watchlist&quot; to monitor specific securities.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {watchlist.map((w) => (
              <div key={w.id} className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between hover:border-slate-750 transition group">
                <div className="flex items-center gap-3">
                  <CompanyLogo symbol={w.symbol} logoUrl={w.logo_url} size="md" />
                  <div>
                    <button
                      onClick={() => setChartModalSymbol(w.symbol)}
                      className="font-bold text-sm text-white hover:text-blue-400 cursor-pointer text-left transition"
                      title="Open price chart pop-up"
                    >
                      {w.symbol}
                    </button>
                    <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{w.reason || 'Technical breakout alert'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-xs font-semibold text-slate-200">
                      {w.current_price ? `LKR ${Number(w.current_price).toFixed(2)}` : '—'}
                    </div>
                    {w.change_pct != null && (
                      <div className={`text-[10px] font-mono ${Number(w.change_pct) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {Number(w.change_pct) >= 0 ? '+' : ''}{Number(w.change_pct).toFixed(2)}%
                      </div>
                    )}
                    {w.alert_price_above && (
                      <div className="text-[10px] text-amber-400 font-mono">Alert &gt; {w.alert_price_above}</div>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => setChartModalSymbol(w.symbol)}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-blue-400 border border-slate-700/70 transition shadow-sm"
                      title="Open price chart pop-up"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => {
                        if (window.confirm(`Permanently remove ${w.symbol} from your monitored watchlist?`)) {
                          removeWatchlistMutation.mutate(w.id);
                        }
                      }}
                      disabled={removeWatchlistMutation.isPending}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/50 text-slate-400 hover:text-rose-400 border border-slate-700/70 hover:border-rose-800/60 transition shadow-sm"
                      title="Remove from Watchlist"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Price Chart Pop-up Modal */}
      <PriceChartModal
        symbol={chartModalSymbol}
        isOpen={!!chartModalSymbol}
        onClose={() => setChartModalSymbol(null)}
      />

      {/* Add Watchlist Modal */}
      {showWatchModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-sm w-full p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white mb-2">Add Stock to Watchlist</h3>
            {watchError && (
              <div className="mb-3 p-2.5 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
                {watchError}
              </div>
            )}
            <form onSubmit={handleWatchSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Symbol (e.g. LOLC.N0000)</label>
                <input
                  type="text"
                  required
                  value={watchForm.symbol}
                  onChange={(e) => setWatchForm({ ...watchForm, symbol: e.target.value })}
                  placeholder="JKH.N0000"
                  className="w-full bg-slate-850 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 uppercase"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Reason / Thesis</label>
                <input
                  type="text"
                  value={watchForm.reason}
                  onChange={(e) => setWatchForm({ ...watchForm, reason: e.target.value })}
                  placeholder="Volume breakout watch"
                  className="w-full bg-slate-850 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Alert Price Above</label>
                  <input
                    type="number"
                    step="0.05"
                    value={watchForm.alert_price_above}
                    onChange={(e) => setWatchForm({ ...watchForm, alert_price_above: e.target.value })}
                    className="w-full bg-slate-850 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Alert Price Below</label>
                  <input
                    type="number"
                    step="0.05"
                    value={watchForm.alert_price_below}
                    onChange={(e) => setWatchForm({ ...watchForm, alert_price_below: e.target.value })}
                    className="w-full bg-slate-850 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowWatchModal(false)}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addWatchlistMutation.isPending}
                  className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold"
                >
                  {addWatchlistMutation.isPending ? 'Saving...' : 'Add to Watchlist'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Position Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white mb-1">Record New Position</h3>
            <p className="text-xs text-slate-400 mb-3">
              Log a trade to track its profit/loss and performance against CSE market prices.
            </p>
            {posError && (
              <div className="mb-3 p-2.5 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
                {posError}
              </div>
            )}
            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Stock Symbol</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. COMB.N0000 or JKH.N0000"
                  value={formData.symbol}
                  onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                  className="w-full bg-slate-850 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 uppercase font-mono"
                />
                <span className="text-[10px] text-slate-500 mt-0.5 block">Official CSE stock ticker</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Bought Price (LKR)</label>
                  <input
                    type="number"
                    step="0.05"
                    required
                    placeholder="e.g. 95.50"
                    value={formData.entry_price}
                    onChange={(e) => setFormData({ ...formData, entry_price: e.target.value })}
                    className="w-full bg-slate-850 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5 block">Purchase price per share</span>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Number of Shares</label>
                  <input
                    type="number"
                    required
                    placeholder="e.g. 200"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    className="w-full bg-slate-850 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5 block">Quantity bought</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-rose-300 font-semibold mb-1">Stop Loss (LKR)</label>
                  <input
                    type="number"
                    step="0.05"
                    placeholder="e.g. 90.00"
                    value={formData.stop_loss}
                    onChange={(e) => setFormData({ ...formData, stop_loss: e.target.value })}
                    className="w-full bg-slate-850 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5 block">Safety exit if price drops</span>
                </div>
                <div>
                  <label className="block text-emerald-300 font-semibold mb-1">Target Price (LKR)</label>
                  <input
                    type="number"
                    step="0.05"
                    placeholder="e.g. 110.00"
                    value={formData.target_price}
                    onChange={(e) => setFormData({ ...formData, target_price: e.target.value })}
                    className="w-full bg-slate-850 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5 block">Profit goal to sell at</span>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addPositionMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold"
                >
                  {addPositionMutation.isPending ? 'Saving...' : 'Record Position'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
