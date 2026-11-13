import React, { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  useModels,
  usePromoteModel,
  useRetrainModel,
  useRetrainStatus,
  useGeneratePredictions,
  useModelPerformance,
} from '../api/client';
import {
  Brain,
  CheckCircle,
  BarChart3,
  RefreshCw,
  Zap,
  Play,
  TrendingUp,
  AlertCircle,
  Loader2,
  Sliders,
  Database,
  ArrowRight,
  Sparkles,
  HelpCircle,
  GraduationCap,
  TrendingDown,
  Scale,
  Eye,
  ShieldCheck,
  X,
} from 'lucide-react';
import InfoTooltip from '../components/InfoTooltip';
import { useBeginnerMode } from '../components/BeginnerModeContext';
import { getFeatureMeta } from '../data/featureMetadata';

export default function Models() {
  const { isBeginnerMode } = useBeginnerMode();
  const { data: models = [], isLoading: modelsLoading, refetch: refetchModels } = useModels();
  const { data: perfSummary, refetch: refetchPerf } = useModelPerformance();
  const promoteMutation = usePromoteModel();
  const retrainMutation = useRetrainModel();
  const queryClient = useQueryClient();
  const [retrainJobId, setRetrainJobId] = useState(null);
  const { data: retrainStatus, error: retrainStatusError } = useRetrainStatus(retrainJobId);
  const predictMutation = useGeneratePredictions();

  const [notification, setNotification] = useState(null);

  const activeModel = models.find((m) => m.is_active);
  const activeMetrics = activeModel?.metrics || {};

  const sharpe = activeMetrics.sharpe_ratio;
  const winRate = activeMetrics.win_rate;
  const excessRet = activeMetrics.excess_return;
  const accuracy = activeMetrics.accuracy;
  const valAuc = activeMetrics.val_auc;
  const trainSamples = activeMetrics.train_samples;
  const bestIter = activeMetrics.best_iteration;
  const noHoldoutTrades = Number(activeMetrics.total_trades) === 0;
  const formatMetric = (value, digits = 2) => {
    const numeric = Number(value);
    return value == null || !Number.isFinite(numeric) ? '—' : numeric.toFixed(digits);
  };
  const hasGateMetrics = [activeMetrics.val_auc, activeMetrics.sharpe_ratio, activeMetrics.excess_return, activeMetrics.total_trades]
    .every((value) => value != null && Number.isFinite(Number(value)));
  const safetyGatePassed =
    hasGateMetrics &&
    Number(activeMetrics.val_auc) > 0.5 &&
    Number(activeMetrics.sharpe_ratio) >= 1 &&
    Number(activeMetrics.excess_return) > 0 &&
    Number(activeMetrics.total_trades) > 0;

  // Features list enriched with beginner-friendly metadata
  const featuresList =
    activeMetrics.top_features && activeMetrics.top_features.length > 0
      ? activeMetrics.top_features.map((f) => {
          const meta = getFeatureMeta(f.feature);
          return {
            feat: f.feature,
            name: meta.name,
            score: f.importance,
            meta,
          };
        })
      : [];

  useEffect(() => {
    if (retrainStatusError && retrainJobId && !retrainStatus) {
      if (retrainStatusError.response?.status === 404) {
        setNotification({
          type: 'error',
          title: 'Training Status Lost',
          message: 'The API no longer has this training job. It may have restarted; start a new training run to continue.',
        });
        setRetrainJobId(null);
        return;
      }
      setNotification({
        type: 'info',
        message: `Training continues, but progress could not be refreshed: ${retrainStatusError.message}`,
      });
      return;
    }
    if (!retrainStatus) return;
    if (retrainStatus.status === 'completed') {
      const result = retrainStatus.result;
      const predictionUpdate = result?.prediction_update;
      const predictionsFailed = predictionUpdate?.status === 'failed';
      setNotification({
        type: predictionsFailed ? 'error' : 'success',
        title: predictionsFailed ? 'Model Active; Predictions Not Updated' : 'Model Retraining Completed',
        message: result?.message || retrainStatus.message,
        stats: result?.metrics,
      });
      setRetrainJobId(null);
      refetchModels();
      refetchPerf();
      void Promise.all([
        queryClient.invalidateQueries({ queryKey: ['recommendations'] }),
        queryClient.invalidateQueries({ queryKey: ['recommendations-history'] }),
      ]);
    } else if (retrainStatus.status === 'failed') {
      const error = retrainStatus.error;
      setNotification({
        type: 'error',
        title: 'Retraining Failed',
        message: `${error?.type ? `${error.type}: ` : ''}${error?.message || retrainStatus.message || 'An error occurred during model retraining.'}`,
      });
      setRetrainJobId(null);
    } else if (retrainJobId) {
      setNotification({
        type: 'info',
        message: retrainStatus.message || 'Model training is running.',
      });
    }
  }, [retrainStatus, retrainStatusError, retrainJobId, refetchModels, refetchPerf, queryClient]);

  const handleRetrain = async () => {
    try {
      setNotification({ type: 'info', message: 'Queuing model training using existing stored data...' });
      const res = await retrainMutation.mutateAsync({ updatePredictions: true, asyncMode: true });
      if (res.data?.job_id) {
        setRetrainJobId(res.data.job_id);
        setNotification({ type: 'info', message: res.data.message || 'Training job queued.' });
        return;
      }
      setNotification({
        type: 'success',
        title: 'Model Retraining Completed',
        message: `${res.data?.message || 'Model training completed.'} Generated ${res.data?.recommendations_updated ?? 0} fresh stock recommendations.`,
        stats: res.data?.metrics,
      });
      refetchModels();
      refetchPerf();
    } catch (err) {
      setNotification({
        type: 'error',
        title: 'Retraining Failed',
        message: err?.response?.data?.detail || err.message || 'An error occurred during model retraining.',
      });
    }
  };

  const handlePredictOnly = async () => {
    try {
      setNotification({ type: 'info', message: 'Generating fresh stock recommendations from active model...' });
      const res = await predictMutation.mutateAsync();
      setNotification({
        type: 'success',
        title: 'Predictions Updated!',
        message: `${res.data?.message || 'Updated.'} Generated ${res.data?.recommendations_count || 0} recommendations with active model.`,
      });
      refetchModels();
      refetchPerf();
    } catch (err) {
      setNotification({
        type: 'error',
        title: 'Prediction Update Failed',
        message: err?.response?.data?.detail || err.message || 'An error occurred while generating predictions.',
      });
    }
  };

  const isBusy = retrainMutation.isPending || predictMutation.isPending || Boolean(retrainJobId);

  return (
    <div className="space-y-6">
      {/* Top Header & Action Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Brain className="w-6 h-6 text-purple-400" />
            Machine Learning Models &amp; Walk-Forward Audits
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            LightGBM calibrated binary classifier predicting 10-day alpha over ASPI benchmark net of transaction costs.
          </p>
          <p className="text-[11px] text-slate-500 mt-1">
            Retraining reads existing database history; it does not fetch data from the internet.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handlePredictOnly}
            disabled={isBusy}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-750 text-slate-200 hover:text-white border border-slate-700 px-4 py-2.5 rounded-xl font-medium text-xs transition disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            title="Generate fresh predictions and update recommendations table without retraining"
          >
            {predictMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
            ) : (
              <Zap className="w-4 h-4 text-amber-400" />
            )}
            <span>Run Predictions Only</span>
          </button>

          <button
            onClick={handleRetrain}
            disabled={isBusy}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold px-5 py-2.5 rounded-xl text-xs transition shadow-lg shadow-blue-600/20 disabled:opacity-60 disabled:cursor-not-allowed"
            title="Train from stored features, monitor progress, evaluate the holdout, and update recommendations"
          >
            {isBusy && retrainJobId ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Training {retrainStatus?.progress ?? 0}%</span>
              </>
            ) : retrainMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Retraining &amp; Updating...</span>
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                <span>Retrain Model &amp; Update Predictions</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Notification Banner */}
      {notification && (
        <div
          className={`p-4 rounded-xl border flex items-start justify-between gap-3 ${
            notification.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
              : notification.type === 'error'
              ? 'bg-rose-950/40 border-rose-800/60 text-rose-300'
              : 'bg-blue-950/40 border-blue-800/60 text-blue-300'
          }`}
        >
          <div className="space-y-1">
            {notification.title && <p className="font-bold text-sm text-white">{notification.title}</p>}
            <p className="text-xs leading-relaxed">{notification.message}</p>
            {retrainJobId && retrainStatus && (
              <div className="pt-2 space-y-1.5">
                <div className="flex justify-between text-[11px] text-slate-300">
                  <span>{retrainStatus.stage?.replaceAll('_', ' ') || 'starting'}</span>
                  <span>{retrainStatus.progress ?? 0}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded bg-slate-800">
                  <div
                    className="h-full rounded bg-blue-500 transition-all"
                    style={{ width: `${Math.min(100, Math.max(0, retrainStatus.progress ?? 0))}%` }}
                  />
                </div>
                {retrainStatus.message && (
                  <p className="text-[11px] leading-relaxed text-slate-400">{retrainStatus.message}</p>
                )}
              </div>
            )}
            {notification.stats && (
              <div className="flex flex-wrap gap-3 pt-2 text-[11px]">
                <span className="bg-slate-900/60 px-2.5 py-0.5 rounded border border-slate-700 text-slate-300">
                  Train Samples: <strong>{notification.stats.train_samples}</strong>
                </span>
                <span className="bg-slate-900/60 px-2.5 py-0.5 rounded border border-slate-700 text-slate-300">
                  Val AUC: <strong>{notification.stats.val_auc ?? '—'}</strong>
                </span>
                <span className="bg-slate-900/60 px-2.5 py-0.5 rounded border border-slate-700 text-slate-300">
                  Accuracy: <strong>{notification.stats.accuracy != null ? `${notification.stats.accuracy}%` : '—'}</strong>
                </span>
                <span className="bg-slate-900/60 px-2.5 py-0.5 rounded border border-slate-700 text-slate-300">
                  Best Iteration: <strong>{notification.stats.best_iteration ?? '—'}</strong>
                </span>
              </div>
            )}
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Beginner Explanation Card */}
      {isBeginnerMode && (
        <div className="bg-gradient-to-r from-purple-950/40 via-slate-900 to-indigo-950/30 border border-purple-500/30 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-purple-300 font-bold text-sm">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>How Does This AI Predict Stocks in Plain English?</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-300">
            <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800 space-y-1">
              <strong className="text-white block">1. Historical Pattern Search</strong>
              <p className="text-slate-400">
                The AI studies daily price movements and trading volumes of 290+ Sri Lankan companies over past months and years.
              </p>
            </div>
            <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800 space-y-1">
              <strong className="text-white block">2. 25+ Clues Tested</strong>
              <p className="text-slate-400">
                It checks momentum, moving averages, and buyer surges to find which indicators reliably forecast profit.
              </p>
            </div>
            <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800 space-y-1">
              <strong className="text-white block">3. Beating the 2.68% Fee Hurdle</strong>
              <p className="text-slate-400">
                It only recommends a stock if the expected gain is comfortably higher than official CSE broker commissions and government taxes.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Active Model Spotlight */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-purple-600/20 border border-purple-500/30 flex items-center justify-center text-purple-400 shadow-inner">
              <Brain className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="font-bold text-lg text-white">
                  {activeModel ? `${activeModel.model_name} (v${activeModel.version})` : 'CSE LightGBM Alpha'}
                </h2>
                <span className={`text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full ${
                  activeModel
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}>
                  {activeModel ? 'Active in Production' : 'No Active Model'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-1.5 flex-wrap">
                <span>Target: Beat ASPI Benchmark + 2.68% round-trip costs</span>
                <InfoTooltip termId="cost_hurdle" />
                <span>&bull; Trained with <strong className="text-slate-200">
                  {trainSamples != null ? Number(trainSamples).toLocaleString() : '—'} samples
                </strong></span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Safety Gate:</span>
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-lg border flex items-center gap-1.5 ${
              !hasGateMetrics
                ? 'bg-slate-800 text-slate-400 border-slate-700'
                : safetyGatePassed
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/25'
            }`}>
              {hasGateMetrics && safetyGatePassed && <CheckCircle className="w-3.5 h-3.5" />}
              <span>
                {!hasGateMetrics ? 'Not Evaluated' : safetyGatePassed ? 'Passed (Holdout Gates)' : 'Not Passed'}
              </span>
            </span>
          </div>
        </div>

        {/* Performance Metrics Grid with Tooltips */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-slate-850 p-4 rounded-xl border border-slate-800">
          <div>
            <div className="text-xs text-slate-400 flex items-center gap-1">
              <span>Sharpe Ratio</span>
              <InfoTooltip termId="sharpe_ratio" />
            </div>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              {formatMetric(sharpe)}
            </div>
            <span className="text-[11px] text-emerald-400 font-medium">
              {noHoldoutTrades ? 'Cash-return convention; no holdout trades' : 'Risk-adjusted return rating'}
            </span>
          </div>
          <div>
            <div className="text-xs text-slate-400 flex items-center gap-1">
              <span>Win Rate (Profits)</span>
              <InfoTooltip termId="win_rate" />
            </div>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              {winRate == null ? '—' : `${formatMetric(winRate, 1)}%`}
            </div>
            <span className="text-[11px] text-slate-400">
              {noHoldoutTrades ? 'No closed holdout trades' : '% of profitable trades'}
            </span>
          </div>
          <div>
            <div className="text-xs text-slate-400 flex items-center gap-1">
              <span>Validation Accuracy</span>
              <InfoTooltip title="Validation Accuracy" text="How accurately the model projected prices on unseen historical CSE test data." />
            </div>
            <div className="text-2xl font-bold text-blue-400 mt-1">
              {accuracy == null ? '—' : `${formatMetric(accuracy, 1)}%`}
            </div>
            <span className="text-[11px] text-slate-400">AUC Score: {formatMetric(valAuc)}</span>
          </div>
          <div>
            <div className="text-xs text-slate-400 flex items-center gap-1">
              <span>Excess Return Net</span>
              <InfoTooltip termId="cost_hurdle" />
            </div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {excessRet == null
                ? '—'
                : `${Number(excessRet) >= 0 ? '+' : ''}${formatMetric(excessRet, 1)}%`}
            </div>
            <span className="text-[11px] text-slate-400">
              {noHoldoutTrades ? 'Uninvested cash vs ASPI' : 'Net excess return versus ASPI'}
            </span>
          </div>
        </div>
      </div>

      {/* Decision Engine Rules & Signal Criteria */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Decision Engine: How the AI Assigns BUY, SELL, HOLD &amp; WATCH</span>
              <InfoTooltip title="Signal Criteria" text="The quantitative safety gates and statistical thresholds used to convert model probabilities into actionable investor signals." />
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Raw model probabilities must clear strict liquidity, market regime, and fee gates before any signal is generated.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          {/* BUY Card */}
          <div className="bg-slate-950/70 p-4 rounded-xl border border-emerald-500/30 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-emerald-400 flex items-center gap-1.5 text-xs">
                <TrendingUp className="w-4 h-4" />
                <span>BUY (Opportunity)</span>
              </span>
              <span className="text-[10px] font-mono bg-emerald-500/15 text-emerald-300 px-2 py-0.5 rounded font-bold border border-emerald-500/30">
                Score ≥ 65%
              </span>
            </div>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              Issued when all 3 gates pass: Model confidence ≥65%, CSE daily turnover ≥LKR 200k, and ASPI index is trending above 100-day SMA.
            </p>
            <div className="pt-2 border-t border-slate-800 text-[10px] text-emerald-400/90 space-y-0.5">
              <div>&bull; <strong>Entry Range:</strong> Current Price ±1%</div>
              <div>&bull; <strong>Stop-Loss:</strong> 2x ATR (~3-5% down)</div>
              <div>&bull; <strong>Target Profit:</strong> 3x ATR (1.5:1+ R:R)</div>
            </div>
          </div>

          {/* SELL Card */}
          <div className="bg-slate-950/70 p-4 rounded-xl border border-rose-500/30 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-rose-400 flex items-center gap-1.5 text-xs">
                <TrendingDown className="w-4 h-4" />
                <span>SELL (Take Profit)</span>
              </span>
              <span className="text-[10px] font-mono bg-rose-500/15 text-rose-300 px-2 py-0.5 rounded font-bold border border-rose-500/30">
                Score ≤ 35%
              </span>
            </div>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              Triggered when model confidence drops to ≤35%, downside stop-loss is hit, profit target is reached, or overbought divergence occurs.
            </p>
            <div className="pt-2 border-t border-slate-800 text-[10px] text-rose-400/90 space-y-0.5">
              <div>&bull; <strong>Holders:</strong> Exit &amp; lock in cash</div>
              <div>&bull; <strong>Non-Holders:</strong> Avoid buying</div>
              <div>&bull; <strong>Protects:</strong> Capital preservation</div>
            </div>
          </div>

          {/* HOLD Card */}
          <div className="bg-slate-950/70 p-4 rounded-xl border border-blue-500/30 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-blue-400 flex items-center gap-1.5 text-xs">
                <Scale className="w-4 h-4" />
                <span>HOLD (Maintain Shares)</span>
              </span>
              <span className="text-[10px] font-mono bg-blue-500/10 text-blue-300 px-2 py-0.5 rounded font-bold border border-blue-500/30">
                36% - 64%
              </span>
            </div>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              Liquid stock in neutral momentum territory. Expected return is not high enough to beat the 2.68% CSE fee hurdle, but no reason to panic sell.
            </p>
            <div className="pt-2 border-t border-slate-800 text-[10px] text-blue-300/90 space-y-0.5">
              <div>&bull; <strong>Holders:</strong> Keep existing shares</div>
              <div>&bull; <strong>Non-Holders:</strong> Wait for breakout</div>
              <div>&bull; <strong>Saves:</strong> Avoids 2.68% broker fees</div>
            </div>
          </div>

          {/* WATCH Card */}
          <div className="bg-slate-950/70 p-4 rounded-xl border border-amber-500/30 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-amber-400 flex items-center gap-1.5 text-xs">
                <Eye className="w-4 h-4" />
                <span>WATCH (Wait &amp; Monitor)</span>
              </span>
              <span className="text-[10px] font-mono bg-amber-500/10 text-amber-300 px-2 py-0.5 rounded font-bold border border-amber-500/30">
                Low Volume
              </span>
            </div>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              Assigned when daily turnover &lt;LKR 200,000 or volume &lt;500 shares. Protects you from getting stuck in illiquid shares with wide bid-ask spreads.
            </p>
            <div className="pt-2 border-t border-slate-800 text-[10px] text-amber-400/90 space-y-0.5">
              <div>&bull; <strong>Status:</strong> Added to Watchlist</div>
              <div>&bull; <strong>Trigger:</strong> Alerts on volume surge</div>
              <div>&bull; <strong>Protects:</strong> Zero liquidity trap</div>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Importance Overview */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-400" />
              <span>Top Predictive Clues (LightGBM Feature Importance)</span>
              <InfoTooltip termId="shap" />
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Which technical indicators gave the AI model the strongest edge in forecasting 10-day alpha.
            </p>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {bestIter != null ? `Early stopping at iteration #${bestIter}` : 'No evaluation run yet'}
          </span>
        </div>

        {/* Beginner Context Box */}
        <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800 text-xs text-slate-300 flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-white">How to read this:</strong> Each card below represents a market indicator tested by the AI.
            The percentage score shows how much weight the model puts on that clue. We translate raw mathematical column names into plain English descriptions so you can see exactly what the AI considers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {featuresList.length === 0 && (
            <p className="text-xs text-slate-500">Feature importance is unavailable until a model evaluation completes.</p>
          )}
          {featuresList.map((item, idx) => {
            const meta = item.meta || getFeatureMeta(item.feat);
            return (
              <div
                key={idx}
                className="bg-slate-850 p-3.5 rounded-xl border border-slate-800/80 hover:border-slate-700 flex flex-col justify-between gap-2 transition"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-bold text-white text-xs">{meta.name}</span>
                      <span className="text-[9px] font-semibold uppercase px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700/60">
                        {meta.category}
                      </span>
                      <InfoTooltip
                        title={`${meta.name} (${item.feat})`}
                        text={meta.simpleDescription}
                        example={meta.bullishMeaning}
                      />
                    </div>
                    <span className="font-bold text-blue-400 font-mono text-xs">{Number(item.score).toFixed(1)}%</span>
                  </div>

                  <p className="text-[11px] text-slate-300 leading-snug">
                    {meta.simpleDescription}
                  </p>
                  <span className="text-[10px] text-slate-500 font-mono block mt-1">
                    Column: {item.feat}
                  </span>
                </div>

                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1">
                  <div
                    className="bg-blue-500 h-full rounded-full"
                    style={{ width: `${Math.min(100, Math.max(5, item.score))}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Models Registry Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-sm text-white">Model Registry &amp; Version Audit Trail</h3>
            <p className="text-xs text-slate-500 mt-0.5">Historical model checkpoints and promotion status</p>
          </div>
          <button
            onClick={() => refetchModels()}
            className="text-xs text-slate-400 hover:text-white flex items-center gap-1.5 bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-700 transition"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Refresh</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-850/70 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                <th className="py-3 px-4">Version</th>
                <th className="py-3 px-4">Algorithm</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Train Samples</th>
                <th className="py-3 px-4">Val Metrics</th>
                <th className="py-3 px-4">Registered</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {modelsLoading ? (
                <tr>
                  <td colSpan="7" className="py-8 text-center text-slate-500">
                    <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-500" />
                    Loading models registry...
                  </td>
                </tr>
              ) : models.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-6 text-center text-slate-500">
                    No models registered yet. Click &quot;Retrain Model&quot; to build version 1.
                  </td>
                </tr>
              ) : (
                models.map((m) => {
                  const mMetrics = m.metrics || {};
                  return (
                    <tr key={m.model_id} className="hover:bg-slate-850/50 transition">
                      <td className="py-3 px-4 font-bold text-white flex items-center gap-1.5">
                        <span>v{m.version}</span>
                        {m.is_active && (
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-300 font-mono text-[11px] uppercase">
                        {m.model_type}
                      </td>
                      <td className="py-3 px-4">
                        {m.is_active ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
                            Archived
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-300 font-mono">
                        {mMetrics.train_samples ? mMetrics.train_samples.toLocaleString() : '—'}
                      </td>
                      <td className="py-3 px-4 text-slate-300 text-[11px]">
                        {mMetrics.accuracy != null ? (
                          <span>Acc: {mMetrics.accuracy}% · AUC: {mMetrics.val_auc}</span>
                        ) : mMetrics.best_iteration != null ? (
                          <span>Best Iter: #{mMetrics.best_iteration}</span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {m.created_at ? new Date(m.created_at).toLocaleDateString() : '-'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {!m.is_active && (
                          <button
                            onClick={() => promoteMutation.mutate(m.model_id)}
                            disabled={promoteMutation.isPending}
                            className="bg-slate-800 hover:bg-blue-600 text-slate-300 hover:text-white px-2.5 py-1 rounded text-[11px] font-medium transition border border-slate-700 hover:border-blue-500"
                          >
                            Promote
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
