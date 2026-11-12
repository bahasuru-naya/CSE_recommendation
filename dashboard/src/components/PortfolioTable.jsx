import React, { useState } from 'react';
import { useClosePosition, useRemovePosition } from '../api/client';
import { Trash2, Eye, LogOut, Loader2 } from 'lucide-react';
import CompanyLogo from './CompanyLogo';
import InfoTooltip from './InfoTooltip';
import PriceChartModal from './PriceChartModal';

export default function PortfolioTable({ positions }) {
  const closeMutation = useClosePosition();
  const removeMutation = useRemovePosition();
  const [chartSymbol, setChartSymbol] = useState(null);
  const [actionId, setActionId] = useState(null);

  if (!positions || positions.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-400 text-sm space-y-2">
        <p className="font-semibold text-slate-300">No portfolio records found in this view.</p>
        <p className="text-xs text-slate-500">Record a BUY recommendation or use &quot;Record Trade&quot; above to track active holdings.</p>
      </div>
    );
  }

  const handleClose = (pos) => {
    const sym = pos.symbol;
    const price = Number(pos.current_price || pos.entry_price).toFixed(2);
    if (window.confirm(`Close and exit open holding for ${sym} at market price LKR ${price}?\n\nThis will lock in your realized gain/loss and move the trade to Closed / Exited Trades.`)) {
      setActionId(pos.id);
      closeMutation.mutate(
        { id: pos.id, exit_price: pos.current_price },
        { onSettled: () => setActionId(null) }
      );
    }
  };

  const handleRemove = (pos) => {
    const sym = pos.symbol;
    const statusLabel = pos.status === 'open' ? 'active open holding' : 'closed trade record';
    if (window.confirm(`Permanently delete this ${statusLabel} for ${sym} (Record #${pos.id}) from your portfolio?\n\nThis item will be completely removed.`)) {
      setActionId(pos.id);
      removeMutation.mutate(pos.id, { onSettled: () => setActionId(null) });
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-850/70 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Symbol</th>
              <th className="py-3 px-4">Trading Date</th>
              <th className="py-3 px-4 text-right">
                <span className="inline-flex items-center gap-1">
                  <span>Shares</span>
                  <InfoTooltip title="Share Quantity" text="The number of shares in this position." />
                </span>
              </th>
              <th className="py-3 px-4 text-right">
                <span className="inline-flex items-center gap-1">
                  <span>Bought At</span>
                  <InfoTooltip title="Entry Price" text="The purchase price per share in Sri Lankan Rupees." />
                </span>
              </th>
              <th className="py-3 px-4 text-right">
                <span className="inline-flex items-center gap-1">
                  <span>Market / Exit Price</span>
                  <InfoTooltip title="Current / Exit Price" text="Current live market price for open holdings, or final exit price for closed trades." />
                </span>
              </th>
              <th className="py-3 px-4 text-right">
                <span className="inline-flex items-center gap-1">
                  <span>Position Value</span>
                  <InfoTooltip termId="portfolio_valuation" />
                </span>
              </th>
              <th className="py-3 px-4 text-right">
                <span className="inline-flex items-center gap-1">
                  <span>Gain / Loss (P&L)</span>
                  <InfoTooltip termId="unrealized_pnl" />
                </span>
              </th>
              <th className="py-3 px-4 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {positions.map((pos) => {
              const isOpen = pos.status === 'open';
              const isProfit = (pos.pnl || 0) >= 0;
              const effectivePrice = isOpen ? pos.current_price : (pos.exit_price || pos.current_price);
              const positionVal = pos.quantity * effectivePrice;

              return (
                <tr key={pos.id} className="hover:bg-slate-850/50 transition">
                  <td className="py-3 px-4">
                    {isOpen ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        OPEN
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">
                        CLOSED / EXITED
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <CompanyLogo symbol={pos.symbol} logoUrl={pos.logo_url} size="sm" />
                      <button
                        onClick={() => setChartSymbol(pos.symbol)}
                        className="font-semibold text-white hover:text-blue-400 transition cursor-pointer text-left"
                        title="Click to view price chart pop-up"
                      >
                        {pos.symbol}
                      </button>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                    {isOpen ? (
                      <span>{pos.entry_date}</span>
                    ) : (
                      <span title={`Bought: ${pos.entry_date} | Exited: ${pos.exit_date || 'Today'}`}>
                        {pos.exit_date || pos.entry_date}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right text-slate-300 font-mono">
                    {Number(pos.quantity).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right text-slate-300 font-mono">
                    LKR {Number(pos.entry_price).toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-right text-slate-200 font-semibold font-mono">
                    LKR {Number(effectivePrice).toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-right text-slate-300 font-mono">
                    LKR {Number(positionVal).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-semibold">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs ${
                        isProfit
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {isProfit ? '+' : ''}{Number(pos.pnl).toFixed(2)} ({isProfit ? '+' : ''}{Number(pos.pnl_pct).toFixed(2)}%)
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <div className="flex items-center justify-center gap-1.5">
                      {/* Price Chart Pop-up */}
                      <button
                        onClick={() => setChartSymbol(pos.symbol)}
                        className="text-slate-400 hover:text-blue-400 transition p-1.5 rounded hover:bg-slate-800"
                        title="View price chart pop-up"
                        aria-label="View chart"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>

                      {/* Exit Open Holding (Close at market price) */}
                      {isOpen && (
                        <button
                          onClick={() => handleClose(pos)}
                          disabled={actionId === pos.id && closeMutation.isPending}
                          className="text-amber-400 hover:text-amber-300 transition p-1.5 rounded hover:bg-slate-800 disabled:opacity-50"
                          title="Exit Trade: Close holding at live market price and lock in gain/loss"
                          aria-label="Exit Trade"
                        >
                          {actionId === pos.id && closeMutation.isPending ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
                          ) : (
                            <LogOut className="w-3.5 h-3.5" />
                          )}
                        </button>
                      )}

                      {/* Permanently Delete Record (Open or Closed) */}
                      <button
                        onClick={() => handleRemove(pos)}
                        disabled={actionId === pos.id && removeMutation.isPending}
                        className="text-slate-500 hover:text-rose-400 transition p-1.5 rounded hover:bg-slate-800 disabled:opacity-50"
                        title={isOpen ? 'Permanently delete this active holding' : 'Permanently remove this closed trade record'}
                        aria-label="Remove item"
                      >
                        {actionId === pos.id && removeMutation.isPending ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-400" />
                        ) : (
                          <Trash2 className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Price Chart Pop-up Modal */}
      <PriceChartModal
        symbol={chartSymbol}
        isOpen={!!chartSymbol}
        onClose={() => setChartSymbol(null)}
      />
    </div>
  );
}
