import axios from 'axios';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Recommendations
export function useRecommendations(signal = null) {
  return useQuery({
    queryKey: ['recommendations', signal],
    queryFn: async () => {
      const res = await api.get('/recommendations/', { params: signal ? { signal } : {} });
      return res.data;
    },
    refetchInterval: 30000,
  });
}

export function useRecommendationHistory() {
  return useQuery({
    queryKey: ['recommendations-history'],
    queryFn: async () => {
      const res = await api.get('/recommendations/history');
      return res.data;
    },
  });
}

export function useExecuteRecommendation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => api.post(`/recommendations/${id}/execute`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
    },
  });
}

// Portfolio
export function usePortfolio(status = 'all') {
  return useQuery({
    queryKey: ['portfolio', status],
    queryFn: async () => {
      const [posRes, sumRes, watchRes] = await Promise.all([
        api.get('/portfolio/positions', { params: { status } }),
        api.get('/portfolio/summary'),
        api.get('/portfolio/watchlist'),
      ]);
      return {
        positions: posRes.data,
        summary: sumRes.data,
        watchlist: watchRes.data,
      };
    },
    refetchInterval: 15000,
  });
}

export function useAddPosition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (newPos) => api.post('/portfolio/positions', newPos),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
    },
  });
}

export function useClosePosition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, exit_price }) => api.post(`/portfolio/positions/${id}/close`, null, { params: { exit_price } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
    },
  });
}

export function useRemovePosition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => api.delete(`/portfolio/positions/${id}/permanent`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
    },
  });
}

export function useAddWatchlist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (item) => api.post('/portfolio/watchlist', item),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['portfolio'] }),
  });
}

export function useRemoveWatchlist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => api.delete(`/portfolio/watchlist/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['portfolio'] }),
  });
}

// Data Pipeline & Market
export function useMarketSummary() {
  return useQuery({
    queryKey: ['market-summary'],
    queryFn: async () => {
      const res = await api.get('/data/market/summary');
      return res.data;
    },
    refetchInterval: 15000,
  });
}

export function useMarketIndices(days = 30) {
  return useQuery({
    queryKey: ['market-indices', days],
    queryFn: async () => {
      const res = await api.get('/data/market/indices', { params: { days } });
      return res.data;
    },
  });
}

export function useSecurityPrices(symbol, days = 90) {
  return useQuery({
    queryKey: ['security-prices', symbol, days],
    queryFn: async () => {
      if (!symbol) return [];
      const res = await api.get(`/data/securities/${symbol}/prices`, { params: { days } });
      return res.data;
    },
    enabled: !!symbol,
  });
}

export function usePipelineStatus() {
  return useQuery({
    queryKey: ['pipeline-status'],
    queryFn: async () => {
      const [statusRes, freshRes] = await Promise.all([
        api.get('/data/pipeline/status'),
        api.get('/data/pipeline/freshness'),
      ]);
      return {
        ...statusRes.data,
        freshness: freshRes.data,
      };
    },
    refetchInterval: 15000,
  });
}

export function useTriggerPipeline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (target = 'daily') => api.post('/data/pipeline/run', null, { params: { target } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipeline-status'] }),
  });
}

// Models & Retraining
export function useModels() {
  return useQuery({
    queryKey: ['models'],
    queryFn: async () => {
      const res = await api.get('/models/');
      return res.data;
    },
  });
}

export function useModelPerformance() {
  return useQuery({
    queryKey: ['model-performance'],
    queryFn: async () => {
      const res = await api.get('/models/performance/summary');
      return res.data;
    },
    refetchInterval: 10000,
  });
}

export function useRetrainModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ updatePredictions = true, asyncMode = false } = {}) =>
      api.post('/models/retrain', null, {
        params: { async_mode: asyncMode, update_predictions: updatePredictions },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      queryClient.invalidateQueries({ queryKey: ['model-performance'] });
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
    },
  });
}

export function useRetrainStatus(jobId) {
  return useQuery({
    queryKey: ['model-retrain-status', jobId],
    queryFn: async () => {
      const res = await api.get(`/models/retrain/status/${jobId}`);
      return res.data;
    },
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return !status || status === 'queued' || status === 'running' ? 1200 : false;
    },
  });
}

export function useGeneratePredictions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post('/models/predict'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
      queryClient.invalidateQueries({ queryKey: ['model-performance'] });
    },
  });
}

export function usePromoteModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => api.post(`/models/${id}/promote`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      queryClient.invalidateQueries({ queryKey: ['model-performance'] });
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
    },
  });
}

// Settings
export function useSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const res = await api.get('/settings/');
      return res.data;
    },
  });
}

export function useUpdateSetting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ key, value }) => api.put(`/settings/${key}`, { value }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings'] }),
  });
}

export function useTelegramSettings() {
  return useQuery({
    queryKey: ['telegram-settings'],
    queryFn: async () => {
      const res = await api.get('/settings/telegram');
      return res.data;
    },
  });
}

export function useUpdateTelegramSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (settings) => api.put('/settings/telegram', settings),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['telegram-settings'] }),
  });
}

export function useTestTelegramSettings() {
  return useMutation({
    mutationFn: (settings) => api.post('/settings/telegram/test', settings),
  });
}

// Data Download
export function useDownloadStatus() {
  return useQuery({
    queryKey: ['download-status'],
    queryFn: async () => {
      const res = await api.get('/data/download/status');
      return res.data;
    },
    refetchInterval: 3000,
  });
}

export function useTriggerDownload() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ period, run_features }) =>
      api.post('/data/download', null, { params: { period, run_features } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['download-status'] });
      queryClient.invalidateQueries({ queryKey: ['lake-stats'] });
    },
  });
}

export function useImportCsv() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (formData) =>
      api.post('/data/import/csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lake-stats'] });
      queryClient.invalidateQueries({ queryKey: ['securities'] });
    },
  });
}

export function useLakeStats() {
  return useQuery({
    queryKey: ['lake-stats'],
    queryFn: async () => {
      const res = await api.get('/data/lake/stats');
      return res.data;
    },
    refetchInterval: 15000,
  });
}

// DB Explorer
export function useDbSchemas() {
  return useQuery({
    queryKey: ['db-schemas'],
    queryFn: async () => {
      const res = await api.get('/db/schemas');
      return res.data;
    },
  });
}

export function useDbTableData(schema, table, page, pageSize, search, sortCol, sortDir) {
  return useQuery({
    queryKey: ['db-table', schema, table, page, pageSize, search, sortCol, sortDir],
    queryFn: async () => {
      if (!schema || !table) return null;
      const res = await api.get(`/db/table/${schema}/${table}`, {
        params: { page, page_size: pageSize, search: search || undefined, sort_col: sortCol || undefined, sort_dir: sortDir },
      });
      return res.data;
    },
    enabled: !!schema && !!table,
    placeholderData: keepPreviousData,
  });
}

export default api;
