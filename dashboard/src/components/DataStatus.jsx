import React, { useState } from 'react';
import { Database, Play, CheckCircle2, AlertTriangle, Clock, Loader2 } from 'lucide-react';
import { useTriggerPipeline } from '../api/client';

export default function DataStatus({ pipelineData }) {
  const triggerMutation = useTriggerPipeline();
  const [notice, setNotice] = useState(null);

  const isStale = pipelineData?.freshness?.is_stale;
  const recentRuns = pipelineData?.ingestion_runs || [];

  const handleTrigger = () => {
    triggerMutation.mutate('daily', {
      onSuccess: () => {
        setNotice('EOD pipeline queued!');
        setTimeout(() => setNotice(null), 4000);
      },
      onError: (err) => {
        setNotice('Pipeline trigger failed');
        setTimeout(() => setNotice(null), 4000);
      },
    });
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-blue-400" />
          <h3 className="font-semibold text-sm text-slate-200">Lakehouse Status</h3>
          {notice && (
            <span className="text-[11px] text-emerald-400 font-medium bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded">
              {notice}
            </span>
          )}
        </div>

        <button
          onClick={handleTrigger}
          disabled={triggerMutation.isPending}
          className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-700 text-slate-200 transition disabled:opacity-50"
        >
          {triggerMutation.isPending ? (
            <Loader2 className="w-3 h-3 animate-spin text-emerald-400" />
          ) : (
            <Play className="w-3 h-3 text-emerald-400 fill-emerald-400" />
          )}
          <span>{triggerMutation.isPending ? 'Queued...' : 'Run EOD Ingestion'}</span>
        </button>
      </div>

      {/* Staleness Banner */}
      <div
        className={`p-3 rounded-lg border mb-4 flex items-center justify-between text-xs ${
          isStale
            ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
            : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
        }`}
      >
        <div className="flex items-center gap-2">
          {isStale ? <AlertTriangle className="w-4 h-4 text-amber-400" /> : <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
          <span>Data Freshness: <strong>{isStale ? 'Awaiting EOD Update (Safety Pause)' : 'UP TO DATE'}</strong></span>
        </div>
        <span className="text-[11px] opacity-80">Checked {new Date().toLocaleTimeString()}</span>
      </div>

      {/* Recent Ingestion Runs */}
      <div className="space-y-2">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
          Recent Ingestions
        </div>
        {recentRuns.length === 0 ? (
          <p className="text-xs text-slate-500">No ingestion runs recorded yet.</p>
        ) : (
          recentRuns.slice(0, 3).map((r, i) => (
            <div
              key={i}
              className="flex items-center justify-between text-xs bg-slate-850/60 p-2.5 rounded border border-slate-800/80"
            >
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                <span className="font-mono text-slate-300">{r.endpoint}</span>
              </div>
              <div className="flex items-center gap-3 text-slate-400 text-[11px]">
                <span>{r.records_landed || 0} landed</span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                    r.status === 'success'
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-amber-500/20 text-amber-400'
                  }`}
                >
                  {r.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
