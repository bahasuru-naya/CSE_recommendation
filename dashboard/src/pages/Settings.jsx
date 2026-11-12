import React, { useState, useEffect } from 'react';
import { useSettings, useUpdateSetting } from '../api/client';
import { Settings as SettingsIcon, Save, Shield, Percent, Clock, AlertTriangle } from 'lucide-react';

export default function Settings() {
  const { data: settingsData, isLoading } = useSettings();
  const updateMutation = useUpdateSetting();

  // Local state for forms
  const [costs, setCosts] = useState({ commission_pct: 0.0115, sec_levy_pct: 0.0015, cse_levy_pct: 0.0004 });
  const [liquidity, setLiquidity] = useState({ min_avg_daily_turnover_20d: 500000, min_avg_daily_volume_20d: 1000 });
  const [risk, setRisk] = useState({ max_position_pct: 0.10, max_positions: 10, max_volume_pct: 0.05 });
  const [savedNotice, setSavedNotice] = useState('');

  useEffect(() => {
    if (settingsData) {
      if (settingsData.trading_costs?.value) setCosts(settingsData.trading_costs.value);
      if (settingsData.liquidity_filter?.value) setLiquidity(settingsData.liquidity_filter.value);
      if (settingsData.risk_limits?.value) setRisk(settingsData.risk_limits.value);
    }
  }, [settingsData]);

  const saveCosts = (e) => {
    e.preventDefault();
    updateMutation.mutate(
      { key: 'trading_costs', value: costs },
      {
        onSuccess: () => {
          setSavedNotice('Trading costs saved.');
          setTimeout(() => setSavedNotice(''), 3000);
        },
      }
    );
  };

  const saveLiquidity = (e) => {
    e.preventDefault();
    updateMutation.mutate(
      { key: 'liquidity_filter', value: liquidity },
      {
        onSuccess: () => {
          setSavedNotice('Liquidity settings saved.');
          setTimeout(() => setSavedNotice(''), 3000);
        },
      }
    );
  };

  const saveRisk = (e) => {
    e.preventDefault();
    updateMutation.mutate(
      { key: 'risk_limits', value: risk },
      {
        onSuccess: () => {
          setSavedNotice('Risk limits saved.');
          setTimeout(() => setSavedNotice(''), 3000);
        },
      }
    );
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">System Settings &amp; Constraints</h1>
          <p className="text-xs text-slate-400">
            Tune execution parameters, brokerage fees, risk constraints, and data freshness thresholds.
          </p>
        </div>
        {savedNotice && (
          <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded-lg animate-fade-in font-medium">
            {savedNotice}
          </span>
        )}
      </div>

      {/* 1. Trading Costs */}
      <form onSubmit={saveCosts} className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Percent className="w-4 h-4 text-blue-400" />
            <h2 className="font-bold text-sm text-white">Colombo Stock Exchange (CSE) Cost Assumptions</h2>
          </div>
          <button
            type="submit"
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Costs</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="block text-slate-400 mb-1">Broker Commission (e.g. 0.0115 = 1.15%)</label>
            <input
              type="number"
              step="0.0001"
              value={costs.commission_pct}
              onChange={(e) => setCosts({ ...costs, commission_pct: parseFloat(e.target.value) })}
              className="w-full bg-slate-850 border border-slate-700 rounded-lg p-2 text-white"
            />
          </div>
          <div>
            <label className="block text-slate-400 mb-1">SEC Levy (0.0015 = 0.15%)</label>
            <input
              type="number"
              step="0.0001"
              value={costs.sec_levy_pct}
              onChange={(e) => setCosts({ ...costs, sec_levy_pct: parseFloat(e.target.value) })}
              className="w-full bg-slate-850 border border-slate-700 rounded-lg p-2 text-white"
            />
          </div>
          <div>
            <label className="block text-slate-400 mb-1">CSE / Share Transfer Levy (0.0004)</label>
            <input
              type="number"
              step="0.0001"
              value={costs.cse_levy_pct}
              onChange={(e) => setCosts({ ...costs, cse_levy_pct: parseFloat(e.target.value) })}
              className="w-full bg-slate-850 border border-slate-700 rounded-lg p-2 text-white"
            />
          </div>
        </div>
        <p className="text-[11px] text-slate-500 mt-2">
          Total round-trip hurdle rate = ~2.68%. Models only recommend when alpha exceeds this fee barrier.
        </p>
      </form>

      {/* 2. Liquidity Filter */}
      <form onSubmit={saveLiquidity} className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-400" />
            <h2 className="font-bold text-sm text-white">Liquidity &amp; Tradability Gate</h2>
          </div>
          <button
            type="submit"
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Liquidity</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block text-slate-400 mb-1">Min 20-Day Average Daily Turnover (LKR)</label>
            <input
              type="number"
              step="50000"
              value={liquidity.min_avg_daily_turnover_20d}
              onChange={(e) =>
                setLiquidity({ ...liquidity, min_avg_daily_turnover_20d: parseFloat(e.target.value) })
              }
              className="w-full bg-slate-850 border border-slate-700 rounded-lg p-2 text-white"
            />
          </div>
          <div>
            <label className="block text-slate-400 mb-1">Min 20-Day Average Daily Volume (Shares)</label>
            <input
              type="number"
              step="100"
              value={liquidity.min_avg_daily_volume_20d}
              onChange={(e) =>
                setLiquidity({ ...liquidity, min_avg_daily_volume_20d: parseInt(e.target.value, 10) })
              }
              className="w-full bg-slate-850 border border-slate-700 rounded-lg p-2 text-white"
            />
          </div>
        </div>
      </form>

      {/* 3. Risk & Sizing Limits */}
      <form onSubmit={saveRisk} className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h2 className="font-bold text-sm text-white">Position Risk &amp; Sizing Caps</h2>
          </div>
          <button
            type="submit"
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Risk Limits</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="block text-slate-400 mb-1">Max Position Size % of Portfolio</label>
            <input
              type="number"
              step="0.01"
              value={risk.max_position_pct}
              onChange={(e) => setRisk({ ...risk, max_position_pct: parseFloat(e.target.value) })}
              className="w-full bg-slate-850 border border-slate-700 rounded-lg p-2 text-white"
            />
          </div>
          <div>
            <label className="block text-slate-400 mb-1">Max Concurrent Positions</label>
            <input
              type="number"
              value={risk.max_positions}
              onChange={(e) => setRisk({ ...risk, max_positions: parseInt(e.target.value, 10) })}
              className="w-full bg-slate-850 border border-slate-700 rounded-lg p-2 text-white"
            />
          </div>
          <div>
            <label className="block text-slate-400 mb-1">Max % of Average Daily Volume</label>
            <input
              type="number"
              step="0.01"
              value={risk.max_volume_pct}
              onChange={(e) => setRisk({ ...risk, max_volume_pct: parseFloat(e.target.value) })}
              className="w-full bg-slate-850 border border-slate-700 rounded-lg p-2 text-white"
            />
          </div>
        </div>
      </form>
    </div>
  );
}
