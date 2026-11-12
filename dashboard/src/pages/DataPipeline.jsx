import React, { useState } from 'react';
import { usePipelineStatus, useTriggerPipeline } from '../api/client';
import { Database, Play, CheckCircle2, AlertOctagon, RefreshCw, Layers, Loader2, X } from 'lucide-react';

export default function DataPipeline() {
  const { data: pipelineData, refetch, isFetching } = usePipelineStatus();
  const triggerMutation = useTriggerPipeline();
  const [notice, setNotice] = useState(null);

  const freshness = pipelineData?.freshness?.tables || {};
  const isStale = pipelineData?.freshness?.is_stale;
  const recentRuns = pipelineData?.ingestion_runs || [];
  const jobRuns = pipelineData?.job_runs || [];

  const handleFetchData = () => {
    triggerMutation.mutate('daily', {
      onSuccess: () => {
        setNotice('Pipeline execution queued in background!');
        setTimeout(() => setNotice(null), 4000);
      },
      onError: () => {
        setNotice('Failed to queue pipeline run.');
        setTimeout(() => setNotice(null), 4000);
      },
    });
  };

  return (
    <div className="space-y-6">
      {notice && (
        <div className="bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 px-4 py-2 rounded-xl text-xs flex items-center justify-between">
          <span>{notice}</span>
          <button onClick={() => setNotice(null)} className="p-1 text-emerald-400 hover:text-emerald-200 transition" title="Dismiss">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white">Market Data Pipeline &amp; Lakehouse</h1>
          <p className="text-xs text-slate-400">
            The automated engine that downloads CSE prices, cleans the numbers, and prepares data for the AI.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs px-3 py-2 rounded-lg"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleFetchData}
            disabled={triggerMutation.isPending}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3.5 py-2 rounded-lg shadow-md shadow-blue-600/20 disabled:opacity-60"
            title="Download the latest end-of-day stock prices from the CSE"
          >
            {triggerMutation.isPending ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-white" />
            )}
            <span>{triggerMutation.isPending ? 'Queued...' : 'Fetch Latest CSE Data'}</span>
          </button>
        </div>
      </div>

      {/* Medallion Architecture Visual Banner */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        {[
          { name: 'Raw', desc: 'JSON payloads + hashes', count: 'raw.api_payloads' },
          { name: 'Staging', desc: 'Typed & deduplicated', count: 'staging.trade_summary' },
          { name: 'Core', desc: 'Dim & Hypertables', count: 'core.fact_price_daily' },
          { name: 'Features', desc: 'Point-in-time tech/fund', count: 'features.feature_daily' },
          { name: 'ML', desc: 'Model registry & backtests', count: 'ml.model_registry' },
          { name: 'App', desc: 'Signals & settings', count: 'app.recommendations' },
        ].map((layer, i) => (
          <div key={i} className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-center">
            <span className="text-[10px] font-mono text-blue-400 uppercase tracking-wider">Layer 0{i + 1}</span>
            <div className="font-bold text-sm text-white mt-0.5">{layer.name}</div>
            <p className="text-[11px] text-slate-400 mt-1 line-clamp-1">{layer.desc}</p>
            <div className="text-[10px] text-slate-500 font-mono mt-2 bg-slate-850 py-0.5 rounded">
              {layer.count}
            </div>
          </div>
        ))}
      </div>

      {/* Data Freshness Status */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <h2 className="font-bold text-sm text-white mb-3 flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-400" />
          <span>Layer Freshness &amp; Point-in-Time Integrity</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(freshness).map(([table, meta]) => (
            <div key={table} className="bg-slate-850 p-3.5 rounded-lg border border-slate-800 flex items-center justify-between text-xs">
              <div>
                <span className="font-semibold text-slate-200">{table}</span>
                <p className="text-slate-400 text-[11px] mt-0.5">
                  Latest trading date: <strong className="text-slate-300">{meta.latest_date || 'N/A'}</strong>
                </p>
              </div>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
          ))}
        </div>
      </div>

      {/* Execution History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Raw Ingestion Logs */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <h3 className="font-bold text-sm text-white mb-3">Raw Endpoint Ingestions</h3>
          <div className="space-y-2">
            {recentRuns.length === 0 ? (
              <p className="text-xs text-slate-500">No recent raw API ingestions recorded.</p>
            ) : (
              recentRuns.slice(0, 5).map((r, i) => (
                <div key={i} className="flex items-center justify-between p-2.5 rounded bg-slate-850 border border-slate-800 text-xs">
                  <div>
                    <span className="font-mono font-medium text-slate-200">{r.endpoint}</span>
                    <p className="text-[11px] text-slate-400">{r.started_at ? new Date(r.started_at).toLocaleString() : ''}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-semibold text-slate-300">{r.records_landed || 0} landed</span>
                    <span className="block text-[10px] uppercase font-bold text-emerald-400">{r.status}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Scheduled Job Runs */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <h3 className="font-bold text-sm text-white mb-3">Scheduled Background Pipeline Runs</h3>
          <div className="space-y-2">
            {jobRuns.length === 0 ? (
              <p className="text-xs text-slate-500">No scheduled job runs recorded.</p>
            ) : (
              jobRuns.slice(0, 5).map((j, i) => (
                <div key={i} className="flex items-center justify-between p-2.5 rounded bg-slate-850 border border-slate-800 text-xs">
                  <div>
                    <span className="font-semibold text-slate-200">{j.job_id}</span>
                    <p className="text-[11px] text-slate-400">{j.started_at ? new Date(j.started_at).toLocaleString() : ''}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-mono text-slate-300">{j.duration_seconds ? `${j.duration_seconds}s` : '-'}</span>
                    <span className="block text-[10px] uppercase font-bold text-emerald-400">{j.status}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
