import React, { useState } from 'react';
import {
  GraduationCap,
  Search,
  BookOpen,
  ShieldCheck,
  TrendingUp,
  DollarSign,
  Brain,
  Lightbulb,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  HelpCircle,
  Sparkles,
} from 'lucide-react';
import { GLOSSARY_TERMS } from '../data/glossary';

export default function StockMarketGuide() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const categories = [
    { id: 'all', label: 'All Terms' },
    { id: 'basics', label: 'Basics & CSE' },
    { id: 'signals', label: 'Signals & Buying' },
    { id: 'risk', label: 'Safety & Risk (Stops)' },
    { id: 'market', label: 'Market Moods' },
    { id: 'portfolio', label: 'Portfolio & P&L' },
    { id: 'ai_models', label: 'AI & Indicators' },
  ];

  const filteredTerms = GLOSSARY_TERMS.filter((item) => {
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory;
    const matchesSearch =
      item.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.simple.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.details.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Hero Welcome Banner */}
      <div className="bg-gradient-to-r from-blue-900/60 via-indigo-900/40 to-slate-900 border border-blue-500/30 rounded-2xl p-6 md:p-8 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-semibold border border-blue-500/30">
              <GraduationCap className="w-4 h-4 text-blue-400" />
              <span>Stock Market 101 &bull; Beginner Friendly</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Stock Market Made Simple
            </h1>
            <p className="text-slate-300 text-sm leading-relaxed">
              You do not need a finance degree to grow your wealth on the <strong>Colombo Stock Exchange (CSE)</strong>.
              This system does the heavy mathematical work for you. Here is everything you need to know in plain, everyday language.
            </p>
          </div>

          <div className="bg-slate-900/80 border border-slate-700/80 p-4 rounded-xl shrink-0 space-y-2 text-xs">
            <div className="text-amber-400 font-bold flex items-center gap-1.5">
              <Lightbulb className="w-4 h-4" />
              <span>Quick Golden Rule:</span>
            </div>
            <p className="text-slate-300 max-w-xs">
              Never invest money you need for daily living or urgent bills in the next 6-12 months. Treat stock investing as building a long-term future.
            </p>
          </div>
        </div>
      </div>

      {/* 3-Step Simple Guide to Using This System */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-bold text-white">How to Use This System in 3 Easy Steps</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Step 1 */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition space-y-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 font-bold flex items-center justify-center text-sm border border-blue-500/30">
              1
            </div>
            <h3 className="font-bold text-white text-sm">Check Today's Market Mood</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Look at the <strong>Market Regime</strong> on your Overview screen:
            </p>
            <div className="space-y-1.5 text-xs">
              <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                <span><strong>BULLISH:</strong> Market is healthy and rising. Great time to buy.</span>
              </div>
              <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
                <span><strong>BEARISH:</strong> Market is falling. Keep cash ready and be cautious.</span>
              </div>
            </div>
          </div>

          {/* Step 2 */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition space-y-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-600/20 text-emerald-400 font-bold flex items-center justify-center text-sm border border-emerald-500/30">
              2
            </div>
            <h3 className="font-bold text-white text-sm">Pick a High-Confidence BUY Stock</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Open the <strong>Signals &amp; Recommendations</strong> page:
            </p>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-start gap-2">
                <span className="text-blue-400 font-bold">&bull;</span>
                <span>Look for a green <strong>BUY</strong> signal.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400 font-bold">&bull;</span>
                <span>Check that <strong>Model Confidence</strong> is high (75% or higher).</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400 font-bold">&bull;</span>
                <span>Click the purple <strong>"Explain"</strong> button to see why the AI picked this company in plain words.</span>
              </li>
            </ul>
          </div>

          {/* Step 3 */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition space-y-3">
            <div className="w-8 h-8 rounded-lg bg-purple-600/20 text-purple-400 font-bold flex items-center justify-center text-sm border border-purple-500/30">
              3
            </div>
            <h3 className="font-bold text-white text-sm">Follow the 3 Golden Numbers</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every recommendation card gives you 3 specific numbers to place with your broker:
            </p>
            <div className="space-y-1.5 text-xs text-slate-300">
              <div className="p-2 rounded bg-slate-850 border border-slate-800">
                <span className="text-blue-400 font-semibold block">1. Entry Range:</span>
                <span className="text-slate-400 text-[11px]">The safe price to buy. Don't overpay if it jumps!</span>
              </div>
              <div className="p-2 rounded bg-slate-850 border border-slate-800">
                <span className="text-rose-400 font-semibold block">2. Stop Loss (Safety Net):</span>
                <span className="text-slate-400 text-[11px]">Sell if it drops here to stop small losses from becoming big.</span>
              </div>
              <div className="p-2 rounded bg-slate-850 border border-slate-800">
                <span className="text-emerald-400 font-semibold block">3. Target (Profit Goal):</span>
                <span className="text-slate-400 text-[11px]">Sell when price reaches this level to lock in your profits.</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* How CSE Trading Works in Real Life */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-bold text-white">How Does Actual Stock Trading Work in Sri Lanka?</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-300 leading-relaxed">
          <div className="space-y-3">
            <h3 className="font-bold text-slate-100 text-sm">How to Buy Real Shares (CDS Account)</h3>
            <p>
              In Sri Lanka, stock transactions are legally registered under your name at the <strong>Central Depository System (CDS)</strong>.
              To buy or sell shares:
            </p>
            <ol className="list-decimal list-inside space-y-1.5 text-slate-400 pl-1">
              <li>Open a free account with any licensed CSE Stockbroker (e.g., CAL, Asha Securities, CT CLSA, Bartleet, SC Securities, Lanka Securities).</li>
              <li>Deposit funds into your brokerage account via online bank transfer.</li>
              <li>Use the broker's mobile or web app to place your order using the numbers recommended in this dashboard.</li>
            </ol>
            <p className="text-slate-400 flex items-start gap-1.5">
              <Lightbulb className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <span><em>Note: This system is your AI research assistant and decision support tool. It does not touch your bank account directly. You remain in 100% control of your money.</em></span>
            </p>
          </div>

          <div className="space-y-3">
            <h3 className="font-bold text-slate-100 text-sm">The 2.68% Fee Rule (Cost Hurdle)</h3>
            <p>
              Every time you buy and sell shares on the CSE, official fees are deducted (broker commissions, SEC regulatory levies, and government share transaction levy):
            </p>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
              <div className="flex justify-between text-slate-400">
                <span>Buying cost:</span>
                <span className="font-mono text-slate-200">~1.12%</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Selling cost:</span>
                <span className="font-mono text-slate-200">~1.12%</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>CDS &amp; SEC transaction levy:</span>
                <span className="font-mono text-slate-200">~0.44%</span>
              </div>
              <div className="pt-1.5 border-t border-slate-800 flex justify-between font-bold text-amber-400">
                <span>Total Round-Trip Hurdle:</span>
                <span className="font-mono">~2.68%</span>
              </div>
            </div>
            <p className="text-slate-400">
              <strong>Why this matters to you:</strong> A stock must grow by more than 2.68% for you to make a true profit.
              Our AI automatically filters out weak stocks and only signals trades with upside potential well above 2.68%.
            </p>
          </div>
        </div>
      </div>

      {/* Jargon Buster & Interactive Dictionary */}
      <div className="space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Brain className="w-5 h-5 text-indigo-400" />
              <span>Stock Market Jargon Buster (A to Z Dictionary)</span>
            </h2>
            <p className="text-xs text-slate-400">
              Every technical word used in this application explained in plain English with Sri Lankan Rupee examples.
            </p>
          </div>

          {/* Search Box */}
          <div className="relative w-full md:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search any word (e.g., Stop Loss, RSI)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Category Filter Pills */}
        <div className="flex flex-wrap items-center gap-2">
          {categories.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedCategory(c.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                selectedCategory === c.id
                  ? 'bg-blue-600 text-white shadow'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* Grid of Terms */}
        {filteredTerms.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-sm">
            No terms match "{searchTerm}". Try another word!
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredTerms.map((item) => (
              <div
                key={item.id}
                className="bg-slate-900 border border-slate-800 hover:border-blue-500/40 rounded-xl p-5 transition space-y-3 flex flex-col justify-between shadow-lg"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="font-bold text-white text-sm">{item.term}</h3>
                    <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                      {item.category}
                    </span>
                  </div>

                  {/* 1-sentence simple definition */}
                  <div className="p-2.5 rounded-lg bg-blue-950/30 border border-blue-500/20 text-xs font-medium text-blue-200">
                    {item.simple}
                  </div>

                  {/* Detailed explanation */}
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {item.details}
                  </p>
                </div>

                {/* Practical Example */}
                {item.example && (
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs">
                    <span className="text-amber-400 font-semibold text-[11px] flex items-center gap-1 mb-0.5">
                      <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                      <span>Real Example:</span>
                    </span>
                    <span className="text-slate-300">{item.example}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 4 Golden Rules for Beginners */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <span>4 Golden Rules Every Stock Investor Must Follow</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <h4 className="font-bold text-emerald-400">1. Always Honor Your Stop Loss</h4>
            <p className="text-slate-300 leading-relaxed">
              If a stock hits the Stop Loss price, exit immediately. Hoping and praying a falling stock will bounce back is how beginners lose their savings. Small losses are normal; big losses ruin portfolios.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <h4 className="font-bold text-blue-400">2. Diversify (Spread Your Risk)</h4>
            <p className="text-slate-300 leading-relaxed">
              Never put 100% of your money into one company. Spread your investment across 4 to 8 different companies across sectors (Banking, Manufacturing, Tourism, Energy).
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <h4 className="font-bold text-amber-400">3. Stick to the Entry Range</h4>
            <p className="text-slate-300 leading-relaxed">
              If a stock has already jumped way past the Entry Range, let it go! Do not suffer from "FOMO" (Fear Of Missing Out). The market always presents new opportunities tomorrow.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <h4 className="font-bold text-purple-400">4. Keep a Long-Term Perspective</h4>
            <p className="text-slate-300 leading-relaxed">
              Stock prices fluctuate day-to-day. Great companies in Sri Lanka compound value over months and years. Let the AI signals guide your entries and exits calmly without panic.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
