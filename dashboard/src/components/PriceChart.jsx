import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { Maximize2 } from 'lucide-react';
import InfoTooltip from './InfoTooltip';

export default function PriceChart({ data, title = 'Stock Price History', onExpand }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-72 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center text-slate-500 text-sm">
        No price series available.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm text-slate-200">{title}</h3>
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
            <span>Closing Price (LKR)</span>
            <InfoTooltip title="Closing Price" text="The final price per share agreed upon at market closing time (14:30 SL time)." />
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-600"></span>
            <span>Daily Volume</span>
            <InfoTooltip termId="volume" />
          </div>
          {onExpand && (
            <button
              onClick={onExpand}
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition ml-1"
              title="Open chart in pop-up window"
              aria-label="Expand chart"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => v ? String(v).substring(5) : ''}
            />
            <YAxis
              yAxisId="price"
              stroke="#64748b"
              fontSize={11}
              domain={['auto', 'auto']}
              tickLine={false}
              tickFormatter={(v) => Number(v).toFixed(0)}
            />
            <YAxis
              yAxisId="volume"
              orientation="right"
              stroke="#475569"
              fontSize={10}
              tickLine={false}
              tickFormatter={(v) => (v > 1000 ? `${(v / 1000).toFixed(0)}k` : v)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#f8fafc',
              }}
              formatter={(val, name) => [
                name === 'close' ? `LKR ${Number(val).toFixed(2)}` : Number(val).toLocaleString(),
                name === 'close' ? 'Close Price' : 'Volume',
              ]}
            />
            <Bar yAxisId="volume" dataKey="volume" fill="#334155" opacity={0.4} barSize={12} />
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="close"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
