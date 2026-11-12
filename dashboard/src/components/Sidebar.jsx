import React from 'react';
import { NavLink } from 'react-router-dom';
import Logo from './Logo';
import {
  LayoutDashboard,
  TrendingUp,
  Briefcase,
  Database,
  Brain,
  Settings,
  Activity,
  Download,
  Table2,
  GraduationCap,
  Sparkles,
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Overview', sub: 'Market pulse & top picks', icon: LayoutDashboard },
  { to: '/recommendations', label: 'Signals & Recommendations', sub: 'AI Buy & Sell suggestions', icon: TrendingUp },
  { to: '/portfolio', label: 'Portfolio & Watchlist', sub: 'My investments tracker', icon: Briefcase },
  { to: '/guide', label: "Beginner's Guide", sub: 'Stock dictionary & tutorials', icon: GraduationCap, badge: 'Start Here' },
  { to: '/models', label: 'AI Models & Backtests', sub: 'How the AI decides', icon: Brain },
  { to: '/data', label: 'Data Lakehouse', sub: 'Market price records', icon: Database },
  { to: '/data-download', label: 'Data Download', sub: 'Export CSV / Parquet', icon: Download },
  { to: '/db-explorer', label: 'DB Explorer', sub: 'Raw database tables', icon: Table2 },
  { to: '/settings', label: 'Settings', sub: 'App configuration', icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-72 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center px-4 border-b border-slate-800">
          <Logo size="md" showText={true} subtitle="Colombo Stock Exchange AI" />
        </div>

        {/* Navigation Items */}
        <nav className="p-3.5 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-start gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      className={`w-4 h-4 mt-0.5 shrink-0 transition ${
                        isActive ? 'text-white' : 'text-slate-400 group-hover:text-blue-400'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span
                          className={`text-xs sm:text-sm leading-snug ${
                            isActive ? 'text-white font-bold' : 'text-slate-100 font-semibold group-hover:text-white'
                          }`}
                        >
                          {item.label}
                        </span>
                        {item.badge && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gradient-to-r from-amber-400 to-amber-500 text-slate-950 font-black text-[10px] rounded-full uppercase tracking-wider shrink-0 shadow-sm leading-none whitespace-nowrap">
                            <Sparkles className="w-2.5 h-2.5" />
                            <span>{item.badge}</span>
                          </span>
                        )}
                      </div>
                      {item.sub && (
                        <span
                          className={`block text-[11px] mt-0.5 leading-snug transition ${
                            isActive
                              ? 'text-blue-100 font-medium'
                              : 'text-slate-400/90 group-hover:text-slate-300'
                          }`}
                        >
                          {item.sub}
                        </span>
                      )}
                    </div>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
