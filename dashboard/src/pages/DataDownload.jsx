import React, { useState, useRef } from 'react';
import {
  RefreshCw,
  Download,
  Upload,
  FileText,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Info,
  Database,
  FileSpreadsheet,
  X,
} from 'lucide-react';
import {
  useDownloadStatus,
  useTriggerDownload,
  useLakeStats,
  useImportCsv,
} from '../api/client';

const PERIODS = [
  { value: '5', label: 'Period 5 — 1 Year (~245 trading days) [Maximum Official CSE API History]' },
  { value: '4', label: 'Period 4 — 3 Months (~60 trading days)' },
  { value: '3', label: 'Period 3 — 1 Month (~22 trading days)' },
  { value: '2', label: 'Period 2 — 1 Week (5 trading days)' },
  { value: '1', label: 'Period 1 — 1 Day (Intraday Ticks)' },
];

const SCHEMA_COLORS = {
  raw: 'bg-slate-700 text-slate-200',
  staging: 'bg-orange-900/60 text-orange-300',
  core: 'bg-blue-900/60 text-blue-300',
  features: 'bg-purple-900/60 text-purple-300',
  ml: 'bg-emerald-900/60 text-emerald-300',
  app: 'bg-cyan-900/60 text-cyan-300',
};

const SCHEMA_HEADER_COLORS = {
  raw: 'text-slate-400 border-slate-700',
  staging: 'text-orange-400 border-orange-800',
  core: 'text-blue-400 border-blue-800',
  features: 'text-purple-400 border-purple-800',
  ml: 'text-emerald-400 border-emerald-800',
  app: 'text-cyan-400 border-cyan-800',
};

function StatusBadge({ status }) {
  const configs = {
    queued: { cls: 'bg-yellow-900/60 text-yellow-300 border border-yellow-700', icon: Clock, label: 'Queued' },
    running: { cls: 'bg-blue-900/60 text-blue-300 border border-blue-700', icon: Loader2, label: 'Running', spin: true },
    completed: { cls: 'bg-emerald-900/60 text-emerald-300 border border-emerald-700', icon: CheckCircle, label: 'Completed' },
    failed: { cls: 'bg-rose-900/60 text-rose-300 border border-rose-700', icon: XCircle, label: 'Failed' },
  };
  const cfg = configs[status] || configs.queued;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.cls}`}>
      <Icon className={`w-3 h-3 ${cfg.spin ? 'animate-spin' : ''}`} />
      {cfg.label}
    </span>
  );
}

function JobCard({ job }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-mono text-slate-500 mb-1">Job ID</p>
          <p className="text-sm font-medium text-slate-200 font-mono">{job.job_id}</p>
        </div>
        <StatusBadge status={job.status} />
      </div>
      {job.message && (
        <p className="text-sm text-slate-400">{job.message}</p>
      )}
      <div className="flex flex-wrap gap-4 text-xs text-slate-500 pt-1 border-t border-slate-700">
        {job.started_at && (
          <span>Started: <span className="text-slate-300">{new Date(job.started_at).toLocaleString()}</span></span>
        )}
        {job.finished_at && (
          <span>Finished: <span className="text-slate-300">{new Date(job.finished_at).toLocaleString()}</span></span>
        )}
      </div>
    </div>
  );
}

function LakeStatsCard() {
  const { data, isLoading, refetch, isFetching } = useLakeStats();

  const grouped = React.useMemo(() => {
    if (!data) return {};
    const statsObj = data?.lake_stats || (typeof data === 'object' && !Array.isArray(data) ? data : {});
    const result = {};

    if (Array.isArray(data)) {
      data.forEach((item) => {
        const schema = item.schema || item.table_schema || 'unknown';
        if (!result[schema]) result[schema] = [];
        result[schema].push(item);
      });
      return result;
    }

    for (const [key, count] of Object.entries(statsObj)) {
      const parts = key.split('.');
      const schema = parts.length > 1 ? parts[0] : 'core';
      const table = parts.length > 1 ? parts[1] : key;
      if (!result[schema]) result[schema] = [];
      result[schema].push({ table, count });
    }
    return result;
  }, [data]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-400" />
          Medallion Lake Statistics
        </h2>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
        </div>
      ) : Object.keys(grouped).length === 0 ? (
        <p className="text-sm text-slate-500 text-center py-6">No lake stats available</p>
      ) : (
        <div className="space-y-4">
          {Object.entries(grouped).map(([schema, tables]) => {
            const headerCls = SCHEMA_HEADER_COLORS[schema] || 'text-slate-400 border-slate-700';
            const badgeCls = SCHEMA_COLORS[schema] || 'bg-slate-700 text-slate-200';
            return (
              <div key={schema}>
                <h3 className={`text-xs font-semibold uppercase tracking-wider pb-2 mb-2 border-b ${headerCls}`}>
                  {schema}
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                  {tables.map((item) => {
                    const tableName = item.table || item.table_name || item.name || '';
                    const count = item.row_count ?? item.count ?? item.rows ?? 0;
                    return (
                      <div key={tableName} className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                        <p className="text-xs text-slate-400 truncate mb-1" title={tableName}>{tableName}</p>
                        <p className="text-lg font-bold text-slate-100">{Number(count).toLocaleString()}</p>
                        <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${badgeCls}`}>{schema}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function DataDownload() {
  const [period, setPeriod] = useState('5');
  const [runFeatures, setRunFeatures] = useState(true);
  const [downloadMsg, setDownloadMsg] = useState(null);

  // CSV Import State
  const [csvFile, setCsvFile] = useState(null);
  const [defaultSymbol, setDefaultSymbol] = useState('');
  const [recomputeCsvFeatures, setRecomputeCsvFeatures] = useState(true);
  const [csvMsg, setCsvMsg] = useState(null);
  const fileInputRef = useRef(null);

  const { data: jobs, isLoading: jobsLoading } = useDownloadStatus();
  const triggerDownload = useTriggerDownload();
  const importCsv = useImportCsv();

  const handleStart = () => {
    setDownloadMsg(null);
    triggerDownload.mutate(
      { period, run_features: runFeatures },
      {
        onSuccess: (res) => {
          setDownloadMsg({ type: 'success', text: res?.data?.message || 'Download & sync job queued successfully!' });
          setTimeout(() => setDownloadMsg(null), 6000);
        },
        onError: (err) => {
          setDownloadMsg({ type: 'error', text: err?.response?.data?.detail || err.message || 'Failed to trigger download job.' });
          setTimeout(() => setDownloadMsg(null), 6000);
        },
      }
    );
  };

  const handleCsvUpload = (e) => {
    e.preventDefault();
    if (!csvFile) {
      setCsvMsg({ type: 'error', text: 'Please select a CSV file to upload.' });
      return;
    }
    setCsvMsg(null);
    const formData = new FormData();
    formData.append('file', csvFile);
    if (defaultSymbol.trim()) {
      formData.append('default_symbol', defaultSymbol.trim().toUpperCase());
    }
    formData.append('recompute_features', recomputeCsvFeatures);

    importCsv.mutate(formData, {
      onSuccess: (res) => {
        setCsvMsg({
          type: 'success',
          text: res?.data?.message || `Successfully imported ${res?.data?.rows_imported} historical price records!`,
          details: res?.data,
        });
        setCsvFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
      },
      onError: (err) => {
        setCsvMsg({
          type: 'error',
          text: err?.response?.data?.detail || err.message || 'Failed to import CSV file.',
        });
      },
    });
  };

  const activeJobs = Array.isArray(jobs) ? jobs : (jobs ? [jobs] : []);

  return (
    <div className="min-h-screen bg-slate-950 p-6 space-y-6">
      {/* Notifications */}
      {downloadMsg && (
        <div
          className={`px-4 py-3 rounded-xl border text-xs flex items-center justify-between shadow-lg ${
            downloadMsg.type === 'success'
              ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-300'
              : 'bg-rose-950/80 border-rose-500/50 text-rose-300'
          }`}
        >
          <span>{downloadMsg.text}</span>
          <button onClick={() => setDownloadMsg(null)} className="p-1 hover:bg-white/10 rounded transition text-slate-300 hover:text-white" title="Dismiss">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {csvMsg && (
        <div
          className={`px-4 py-3 rounded-xl border text-xs flex items-center justify-between shadow-lg ${
            csvMsg.type === 'success'
              ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-300'
              : 'bg-rose-950/80 border-rose-500/50 text-rose-300'
          }`}
        >
          <div>
            <p className="font-semibold">{csvMsg.text}</p>
            {csvMsg.details && (
              <p className="mt-1 text-[11px] opacity-90">
                Range: {csvMsg.details.date_range?.min} to {csvMsg.details.date_range?.max} • Symbols: {csvMsg.details.unique_symbols?.join(', ')} • Features Computed: {csvMsg.details.features_computed}
              </p>
            )}
          </div>
          <button onClick={() => setCsvMsg(null)} className="p-1 hover:bg-white/10 rounded transition text-slate-300 hover:text-white" title="Dismiss">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Data Management &amp; Historical Sync</h1>
        <p className="text-slate-400 mt-1 text-sm">Download official CSE price history or import multi-year archives into the Medallion Lakehouse</p>
      </div>

      {/* 5-Year Data Capability Info Callout */}
      <div className="bg-slate-900/90 border border-blue-500/30 rounded-xl p-5 shadow-lg space-y-3">
        <div className="flex items-center gap-2 text-blue-400 font-semibold text-sm">
          <Info className="w-5 h-5 shrink-0" />
          <span>Understanding CSE Historical Data &amp; 5-Year Storage</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300 leading-relaxed">
          <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800">
            <span className="font-semibold text-blue-300 block mb-1">Official CSE Public API Limitation:</span>
            The Colombo Stock Exchange public charts endpoint (<code>companyChartDataByStock</code>) provides up to <strong>1 Year (Period 5)</strong> of daily history (~245 trading days). The CSE web server hard-caps online requests at 1 year.
          </div>
          <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800">
            <span className="font-semibold text-emerald-300 block mb-1">How 5+ Years History is Supported:</span>
            <strong>1. Continuous Lakehouse Accumulation:</strong> The automated EOD pipeline saves daily closing prices into <code>core.fact_price_daily</code> without expiring old data.<br/>
            <strong>2. Historical CSV Import:</strong> You can upload 5 to 10+ years of daily OHLCV CSV data below from CSE Data Library, broker statements, or historical archives.
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left Column: API Download & CSV Upload */}
        <div className="xl:col-span-1 space-y-6">
          {/* Official API Download Form */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h2 className="text-base font-semibold text-slate-200 mb-4 flex items-center gap-2">
              <Download className="w-4 h-4 text-blue-400" />
              Download from CSE API
            </h2>

            {/* Period Selector */}
            <div className="mb-5">
              <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">
                Historical Period
              </label>
              <div className="space-y-2">
                {PERIODS.map((p) => (
                  <label
                    key={p.value}
                    className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      period === p.value
                        ? 'border-blue-600 bg-blue-600/10 text-slate-200'
                        : 'border-slate-700 hover:border-slate-600 text-slate-400'
                    }`}
                  >
                    <input
                      type="radio"
                      name="period"
                      value={p.value}
                      checked={period === p.value}
                      onChange={(e) => setPeriod(e.target.value)}
                      className="accent-blue-600"
                    />
                    <span className="text-xs sm:text-sm">{p.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Feature Generation Toggle */}
            <div className="mb-5">
              <label className="flex items-center justify-between p-3 rounded-lg border border-slate-700 hover:border-slate-600 cursor-pointer transition-colors">
                <div>
                  <p className="text-sm font-medium text-slate-200">Include feature generation</p>
                  <p className="text-xs text-slate-500 mt-0.5">Run ML feature pipeline after download</p>
                </div>
                <div className="relative">
                  <input
                    type="checkbox"
                    className="sr-only"
                    checked={runFeatures}
                    onChange={(e) => setRunFeatures(e.target.checked)}
                  />
                  <div
                    onClick={() => setRunFeatures(!runFeatures)}
                    className={`w-11 h-6 rounded-full transition-colors ${runFeatures ? 'bg-blue-600' : 'bg-slate-700'}`}
                  >
                    <div className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${runFeatures ? 'translate-x-5' : 'translate-x-0'}`} />
                  </div>
                </div>
              </label>
            </div>

            {/* Submit */}
            <button
              onClick={handleStart}
              disabled={triggerDownload.isPending}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition-colors text-sm"
            >
              {triggerDownload.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Starting…
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  Start CSE API Download
                </>
              )}
            </button>
          </div>

          {/* Multi-Year Historical CSV Import Component */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
              <Upload className="w-4 h-4 text-emerald-400" />
              Import Multi-Year Historical CSV
            </h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Upload historical daily OHLCV CSV archives (5+ years) directly into <code>core.fact_price_daily</code>.
            </p>

            <form onSubmit={handleCsvUpload} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
                  Select CSV File
                </label>
                <div className="flex items-center gap-3">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    onChange={(e) => setCsvFile(e.target.files[0] || null)}
                    className="block w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700 cursor-pointer"
                  />
                </div>
                {csvFile && (
                  <p className="mt-1.5 text-xs text-emerald-400 flex items-center gap-1">
                    <FileSpreadsheet className="w-3.5 h-3.5" />
                    {csvFile.name} ({(csvFile.size / 1024).toFixed(1)} KB)
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
                  Default Stock Symbol <span className="text-slate-600 font-normal lowercase">(optional if CSV has a symbol column)</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. COMB.N0000 or JKH.N0000"
                  value={defaultSymbol}
                  onChange={(e) => setDefaultSymbol(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <label className="flex items-center justify-between p-2.5 rounded-lg border border-slate-700/80 hover:border-slate-600 cursor-pointer transition-colors">
                <div>
                  <p className="text-xs font-medium text-slate-300">Compute Technical &amp; ML Features</p>
                  <p className="text-[11px] text-slate-500">Calculate indicators after import</p>
                </div>
                <input
                  type="checkbox"
                  checked={recomputeCsvFeatures}
                  onChange={(e) => setRecomputeCsvFeatures(e.target.checked)}
                  className="w-4 h-4 rounded text-blue-600 bg-slate-800 border-slate-600 focus:ring-0"
                />
              </label>

              <button
                type="submit"
                disabled={!csvFile || importCsv.isPending}
                className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2.5 px-4 rounded-lg transition-colors text-xs"
              >
                {importCsv.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Importing Historical Records…
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Upload &amp; Populate Lakehouse
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Active Jobs */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-slate-200">Active Jobs</h2>
              {jobsLoading && <Loader2 className="w-4 h-4 animate-spin text-slate-500" />}
            </div>

            {activeJobs.length === 0 ? (
              <div className="text-center py-6">
                <Clock className="w-7 h-7 text-slate-700 mx-auto mb-2" />
                <p className="text-xs text-slate-500">No active background jobs</p>
              </div>
            ) : (
              <div className="space-y-3">
                {activeJobs.map((job, i) => (
                  <JobCard key={job.job_id || i} job={job} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Lake Stats */}
        <div className="xl:col-span-2 space-y-6">
          <LakeStatsCard />
        </div>
      </div>
    </div>
  );
}
