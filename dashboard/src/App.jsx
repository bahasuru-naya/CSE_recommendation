import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Recommendations from './pages/Recommendations';
import Portfolio from './pages/Portfolio';
import DataPipeline from './pages/DataPipeline';
import Models from './pages/Models';
import Settings from './pages/Settings';
import DataDownload from './pages/DataDownload';
import DatabaseExplorer from './pages/DatabaseExplorer';

import StockMarketGuide from './pages/StockMarketGuide';
import { BeginnerModeProvider } from './components/BeginnerModeContext';

export default function App() {
  return (
    <BeginnerModeProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/guide" element={<StockMarketGuide />} />
          <Route path="/data" element={<DataPipeline />} />
          <Route path="/models" element={<Models />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/data-download" element={<DataDownload />} />
          <Route path="/db-explorer" element={<DatabaseExplorer />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BeginnerModeProvider>
  );
}
