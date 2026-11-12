/**
 * Plain-English Metadata and Descriptions for AI / SHAP Features
 * Designed specifically for Colombo Stock Exchange (CSE) beginner investors.
 */

export const FEATURE_METADATA = {
  // --- Price Returns & Short-Term Momentum ---
  return_1d: {
    name: '1-Day Price Change',
    category: 'Price Momentum',
    categoryColor: 'blue',
    simpleDescription: 'How much the share price gained or lost compared to yesterday’s close.',
    beginnerSummary: 'Shows immediate day-to-day market sentiment.',
    bullishMeaning: 'Price jumped higher yesterday, showing instant buyer enthusiasm.',
    bearishMeaning: 'Price dipped yesterday, indicating short-term selling pressure.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  return_5d: {
    name: '5-Day Momentum (1 Week)',
    category: 'Price Momentum',
    categoryColor: 'blue',
    simpleDescription: 'The percentage return of the stock over the last 5 trading days (one calendar week).',
    beginnerSummary: 'Tells you if the stock has had a winning or losing week.',
    bullishMeaning: 'Solid weekly gains confirm short-term upward momentum.',
    bearishMeaning: 'Stock has had a losing week and may be cooling off.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  return_10d: {
    name: '10-Day Momentum (2 Weeks)',
    category: 'Price Momentum',
    categoryColor: 'blue',
    simpleDescription: 'Price gain or loss over the past 10 trading days (two weeks).',
    beginnerSummary: 'Confirms whether buyers are sustaining the price rise or losing steam.',
    bullishMeaning: 'Two weeks of sustained buying shows real demand, not just a one-day fluke.',
    bearishMeaning: 'Sustained pullback over two weeks.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  return_20d: {
    name: '20-Day Price Trend (1 Month)',
    category: 'Price Momentum',
    categoryColor: 'blue',
    simpleDescription: 'The overall percentage price change over the past 20 trading days (one full month).',
    beginnerSummary: 'The standard monthly benchmark used to judge the stock’s main direction.',
    bullishMeaning: 'Strong monthly uptrend indicates consistent institutional interest.',
    bearishMeaning: 'Stock has been declining over the past month.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },

  // --- Moving Averages & Trendlines (Normalised Ratios) ---
  sma_5: {
    name: '5-Day Average (SMA 5)',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'The average closing price of the stock over the past 5 trading days.',
    beginnerSummary: 'Ultra-fast price trendline.',
    bullishMeaning: 'Price is above its 5-day average, signaling immediate strength.',
    bearishMeaning: 'Price has slipped below its 5-day average.',
    formatValue: (v) => `LKR ${Number(v).toFixed(2)}`,
  },
  sma_5_ratio: {
    name: '5-Day Trendline Gap',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'How far today’s price is trading above or below its 5-day moving average.',
    beginnerSummary: 'Positive percentage means the stock is trading higher than its past-week average.',
    bullishMeaning: 'Trading above 5-day average indicates quick buyer pull.',
    bearishMeaning: 'Trading below 5-day average shows short-term softness.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  sma_10: {
    name: '10-Day Average (SMA 10)',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'The average closing price over the last two weeks (10 trading days).',
    beginnerSummary: 'Smoothed 2-week baseline.',
    bullishMeaning: 'Price holding above its 10-day average confirms a healthy short-term rally.',
    bearishMeaning: 'Price dipping below 10-day average warns of a short-term correction.',
    formatValue: (v) => `LKR ${Number(v).toFixed(2)}`,
  },
  sma_10_ratio: {
    name: '10-Day Trendline Gap',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'Distance between today’s stock price and its 10-day moving average.',
    beginnerSummary: 'Measures short-term breakout speed above the 2-week average price.',
    bullishMeaning: 'Stock is outpacing its recent 2-week baseline.',
    bearishMeaning: 'Stock is lagging behind its 2-week baseline.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  sma_20: {
    name: '20-Day Monthly Trendline (SMA 20)',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'The classic 1-month average price line watched by professional fund managers.',
    beginnerSummary: 'The golden baseline: stocks above this are generally in an uptrend.',
    bullishMeaning: 'Price is comfortably above the monthly baseline, showing healthy accumulation.',
    bearishMeaning: 'Price broke below the monthly baseline, suggesting caution.',
    formatValue: (v) => `LKR ${Number(v).toFixed(2)}`,
  },
  sma_20_ratio: {
    name: '20-Day Monthly Trendline Gap',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'Percentage difference between current price and the 20-day (1-month) moving average.',
    beginnerSummary: 'A positive gap means the stock is riding a solid monthly wave.',
    bullishMeaning: 'Strong position above the 20-day average confirms the stock is in an active bull wave.',
    bearishMeaning: 'Trading below 20-day average indicates intermediate-term weakness.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  sma_50: {
    name: '50-Day Intermediate Trendline (SMA 50)',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'The 10-week (quarterly) moving average price.',
    beginnerSummary: 'Major benchmark for medium-term institutional health.',
    bullishMeaning: 'Holding above 50-day average confirms a sustained quarterly bull trend.',
    bearishMeaning: 'Falling below 50-day average warns that the multi-week rally is breaking down.',
    formatValue: (v) => `LKR ${Number(v).toFixed(2)}`,
  },
  sma_50_ratio: {
    name: '50-Day Trendline Gap',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'Percentage distance of today’s price from the 50-day quarterly trendline.',
    beginnerSummary: 'Positive values show the stock is in a solid medium-term upward trend.',
    bullishMeaning: 'Well-supported above quarterly average, signaling institutional backing.',
    bearishMeaning: 'Losing ground compared to the quarterly trend.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  sma_100: {
    name: '100-Day Major Trendline (SMA 100)',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'The 5-month long-term price average.',
    beginnerSummary: 'Acts as a major fortress floor against big market drops.',
    bullishMeaning: 'Trading well above the 100-day line confirms strong long-term health.',
    bearishMeaning: 'Breaching below 100-day line signals long-term weakness.',
    formatValue: (v) => `LKR ${Number(v).toFixed(2)}`,
  },
  sma_100_ratio: {
    name: '100-Day Major Trendline Gap',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'Percentage distance of current price above or below the 100-day (5-month) line.',
    beginnerSummary: 'Measures long-term strength. Positive means trading safely above the long-term floor.',
    bullishMeaning: 'Strong macro health, safely distanced from bear market territory.',
    bearishMeaning: 'Lagging behind the long-term trendline.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  ema_12: {
    name: '12-Day Fast Average (EMA 12)',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'An average that gives extra weight to the most recent 12 days.',
    beginnerSummary: 'Catches sudden price turns much faster than a standard average.',
    bullishMeaning: 'Rising fast average confirms fresh buying momentum.',
    bearishMeaning: 'Dropping fast average warns of quick seller arrival.',
    formatValue: (v) => `LKR ${Number(v).toFixed(2)}`,
  },
  ema_12_ratio: {
    name: '12-Day Fast Average Gap',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'Distance of current price from the rapid 12-day exponential average.',
    beginnerSummary: 'High positive values show explosive short-term moves.',
    bullishMeaning: 'Price is pulling ahead of recent averages with quick momentum.',
    bearishMeaning: 'Price is falling behind the fast average.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  ema_26: {
    name: '26-Day Slow Average (EMA 26)',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'A smoothed monthly exponential average that filters out random noise.',
    beginnerSummary: 'Used alongside EMA 12 to detect trend crossovers.',
    bullishMeaning: 'Provides steady underlying support for the stock.',
    bearishMeaning: 'Acting as an overhead ceiling holding the price back.',
    formatValue: (v) => `LKR ${Number(v).toFixed(2)}`,
  },
  ema_26_ratio: {
    name: '26-Day Slow Average Gap',
    category: 'Trendlines',
    categoryColor: 'indigo',
    simpleDescription: 'Distance between today’s price and the 26-day smoothed baseline.',
    beginnerSummary: 'Measures whether the stock is holding its ground against monthly noise.',
    bullishMeaning: 'Stock is maintaining positive separation from its monthly baseline.',
    bearishMeaning: 'Stock has fallen below its monthly smoothed baseline.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },

  // --- MACD (Moving Average Convergence Divergence) ---
  macd: {
    name: 'MACD Momentum Line',
    category: 'Momentum Signals',
    categoryColor: 'purple',
    simpleDescription: 'Measures the difference between fast (12-day) and slow (26-day) moving averages.',
    beginnerSummary: 'A green-light indicator: when positive, buyers are driving the bus.',
    bullishMeaning: 'Positive MACD confirms buyers have strong control over the trend.',
    bearishMeaning: 'Negative MACD warns sellers are dominating.',
    formatValue: (v) => Number(v).toFixed(3),
  },
  macd_ratio: {
    name: 'MACD Momentum Speed',
    category: 'Momentum Signals',
    categoryColor: 'purple',
    simpleDescription: 'MACD line normalised by stock price to measure trend speed accurately across any stock.',
    beginnerSummary: 'Measures pure momentum speed without being distorted by expensive vs cheap stocks.',
    bullishMeaning: 'Fast positive momentum velocity confirms high-confidence buying interest.',
    bearishMeaning: 'Negative momentum velocity indicates slowing demand.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(3)}%`,
  },
  macd_signal: {
    name: 'MACD Signal Baseline',
    category: 'Momentum Signals',
    categoryColor: 'purple',
    simpleDescription: 'A 9-day smoothed average of the MACD line.',
    beginnerSummary: 'When MACD crosses above this line, professional traders take it as a buy trigger.',
    bullishMeaning: 'MACD is above the signal line, confirming a confirmed buy zone.',
    bearishMeaning: 'MACD is below the signal line, indicating caution.',
    formatValue: (v) => Number(v).toFixed(3),
  },
  macd_signal_ratio: {
    name: 'MACD Signal Baseline Speed',
    category: 'Momentum Signals',
    categoryColor: 'purple',
    simpleDescription: 'Normalised MACD signal trigger line relative to price.',
    beginnerSummary: 'Baseline threshold for technical buy confirmation.',
    bullishMeaning: 'Baseline is trending upwards supporting the price rally.',
    bearishMeaning: 'Baseline is tilting downward.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(3)}%`,
  },
  macd_histogram: {
    name: 'MACD Acceleration',
    category: 'Momentum Signals',
    categoryColor: 'purple',
    simpleDescription: 'The difference between the MACD line and its Signal line.',
    beginnerSummary: 'Shows whether buyer momentum is speeding up (accelerating) or slowing down.',
    bullishMeaning: 'Expanding positive histogram shows buying frenzy is gaining speed.',
    bearishMeaning: 'Histogram shrinking or negative warns momentum is losing steam.',
    formatValue: (v) => Number(v).toFixed(3),
  },
  macd_histogram_ratio: {
    name: 'MACD Acceleration Rate',
    category: 'Momentum Signals',
    categoryColor: 'purple',
    simpleDescription: 'Price-normalised rate of momentum acceleration.',
    beginnerSummary: 'Tells you if the price rally is picking up speed right now.',
    bullishMeaning: 'Buyers are hitting the gas pedal, increasing the odds of an alpha breakout.',
    bearishMeaning: 'Momentum is decelerating.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(3)}%`,
  },

  // --- Oscillators & Valuation Gauges ---
  rsi_14: {
    name: 'RSI Price Valuation Gauge (14-Day)',
    category: 'Valuation Gauge',
    categoryColor: 'emerald',
    simpleDescription: 'A 0 to 100 speed gauge showing whether a stock is a bargain or overheated.',
    beginnerSummary: 'Below 30 = Bargain (oversold); 40-65 = Healthy Sweet Spot; Above 70 = Frothy (overbought).',
    bullishMeaning: 'RSI in the healthy 45-65 zone indicates steady buyer demand with plenty of room to run.',
    bearishMeaning: 'RSI above 70 warns the stock is overheated and due for a breather.',
    formatValue: (v) => `${Number(v).toFixed(1)} / 100`,
  },
  stochastic_k: {
    name: 'Stochastic Oscillator (%K)',
    category: 'Valuation Gauge',
    categoryColor: 'emerald',
    simpleDescription: 'Measures where today’s closing price sits inside its 14-day high-low price range.',
    beginnerSummary: '0 = Closed at lowest price in 2 weeks; 100 = Closed right at the 2-week peak.',
    bullishMeaning: 'Closing near the top of the 2-week range indicates aggressive end-of-day buying.',
    bearishMeaning: 'Closing near the bottom of the range shows selling pressure.',
    formatValue: (v) => `${Number(v).toFixed(1)}%`,
  },
  stochastic_d: {
    name: 'Stochastic Smoothed Line (%D)',
    category: 'Valuation Gauge',
    categoryColor: 'emerald',
    simpleDescription: 'A 3-day smoothed average of %K used to confirm turning points without false alarms.',
    beginnerSummary: 'Confirms cyclical bottoms and breakout reversals.',
    bullishMeaning: 'Turning upward from low levels indicates a reliable price reversal has begun.',
    bearishMeaning: 'Turning downward from high levels signals profit-taking.',
    formatValue: (v) => `${Number(v).toFixed(1)}%`,
  },

  // --- Bollinger Bands (Volatility & Safe Boundaries) ---
  bollinger_upper: {
    name: 'Bollinger Ceiling (Upper Band)',
    category: 'Volatility Bands',
    categoryColor: 'cyan',
    simpleDescription: 'Statistical upper ceiling representing 2 standard deviations above the 20-day average.',
    beginnerSummary: 'When price hits this ceiling, it often pauses or takes a breather.',
    bullishMeaning: 'Strong momentum riding the upper band can signal an explosive runaway rally.',
    bearishMeaning: 'Stretched too far above the ceiling; risk of pullback.',
    formatValue: (v) => `LKR ${Number(v).toFixed(2)}`,
  },
  bollinger_upper_ratio: {
    name: 'Distance to Bollinger Ceiling',
    category: 'Volatility Bands',
    categoryColor: 'cyan',
    simpleDescription: 'How close the stock is trading to its upper statistical ceiling.',
    beginnerSummary: 'Tells you if there is room for the stock to run higher before hitting resistance.',
    bullishMeaning: 'Healthy room below the ceiling means upside potential is wide open.',
    bearishMeaning: 'Hugging or piercing the upper ceiling; may be temporarily overstretched.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  bollinger_lower: {
    name: 'Bollinger Floor (Lower Band)',
    category: 'Volatility Bands',
    categoryColor: 'cyan',
    simpleDescription: 'Statistical floor representing 2 standard deviations below the 20-day average.',
    beginnerSummary: 'Acts as a bargain trampoline where bargain-hunters step in to buy.',
    bullishMeaning: 'Price bouncing off the lower floor provides a low-risk entry opportunity.',
    bearishMeaning: 'Falling below the floor indicates severe distress.',
    formatValue: (v) => `LKR ${Number(v).toFixed(2)}`,
  },
  bollinger_lower_ratio: {
    name: 'Distance to Bollinger Floor',
    category: 'Volatility Bands',
    categoryColor: 'cyan',
    simpleDescription: 'Percentage cushion between current price and the lower safety floor.',
    beginnerSummary: 'Measures how safely protected the stock is from dropping into panic territory.',
    bullishMeaning: 'Comfortable safety buffer above the floor.',
    bearishMeaning: 'Close to the floor, indicating potential risk or deep value.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  bollinger_width: {
    name: 'Bollinger Bandwidth (Volatility Squeeze)',
    category: 'Volatility Bands',
    categoryColor: 'cyan',
    simpleDescription: 'The percentage width between the upper ceiling and lower floor.',
    beginnerSummary: 'Narrow bandwidth = Calm before the storm (a big price explosion is coming). Wide = High volatility.',
    bullishMeaning: 'Band squeeze with positive momentum often leads to massive breakout profits.',
    bearishMeaning: 'Overly wide bands mean wild, unpredictable price swings.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },

  // --- Volatility & ATR (Safety & Stop-Loss Sizing) ---
  volatility_20d: {
    name: '20-Day Price Volatility',
    category: 'Risk & Volatility',
    categoryColor: 'amber',
    simpleDescription: 'The annualized volatility of daily price swings over the past month.',
    beginnerSummary: 'Low volatility = Smooth, steady, predictable. High volatility = Rollercoaster ride.',
    bullishMeaning: 'Controlled volatility means price is rising smoothly without erratic drops.',
    bearishMeaning: 'Spike in volatility increases the chance of sudden stop-loss triggers.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(1)}%`,
  },
  aspi_volatility_20d: {
    name: 'Colombo Market Volatility (ASPI)',
    category: 'Risk & Volatility',
    categoryColor: 'amber',
    simpleDescription: 'The overall turbulence level across the entire Colombo Stock Exchange market.',
    beginnerSummary: 'When the whole CSE market is calm, individual stock picks are much more predictable.',
    bullishMeaning: 'Calm CSE market environment allows high-quality stocks to rally steadily.',
    bearishMeaning: 'Turbulent overall market means caution is advised.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(1)}%`,
  },
  atr_14: {
    name: 'Daily Price Range (ATR 14)',
    category: 'Risk & Volatility',
    categoryColor: 'amber',
    simpleDescription: 'Average True Range: The typical daily rupee swing between highest and lowest prices.',
    beginnerSummary: 'The AI uses this rupee amount to set smart stop-losses and profit targets.',
    bullishMeaning: 'Healthy daily trading range gives room for meaningful profit gains.',
    bearishMeaning: 'Abnormally high ATR requires wider stop-loss buffers.',
    formatValue: (v) => `LKR ${Number(v).toFixed(2)}`,
  },
  atr_14_ratio: {
    name: 'Daily Fluctuation Ratio (ATR / Price)',
    category: 'Risk & Volatility',
    categoryColor: 'amber',
    simpleDescription: 'Typical daily price swing expressed as a percentage of the stock’s share price.',
    beginnerSummary: 'Tells you what percentage the stock normally wiggles in a single trading day.',
    bullishMeaning: 'Moderate fluctuation (1-3%) provides ideal risk-to-reward for short-term trades.',
    bearishMeaning: 'Excessive daily swing (>6%) indicates high risk for conservative investors.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },

  // --- Volume, Turnover & Liquidity ---
  volume_ratio: {
    name: 'Trading Activity Surge (Volume Ratio)',
    category: 'Trading Volume',
    categoryColor: 'emerald',
    simpleDescription: 'Today’s traded volume divided by its 20-day normal average.',
    beginnerSummary: '1.0x = Normal day. 1.5x - 3.0x = Big buyers or institutional funds have entered the stock!',
    bullishMeaning: 'Volume surge confirms big money accumulation, making price gains far more trustworthy.',
    bearishMeaning: 'Low volume (<0.5x) shows lack of buyer interest, warning the rally may fizzle out.',
    formatValue: (v) => `${Number(v).toFixed(2)}x`,
  },
  volume_sma_20: {
    name: '20-Day Average Traded Volume',
    category: 'Trading Volume',
    categoryColor: 'emerald',
    simpleDescription: 'The average number of shares traded daily over the past month.',
    beginnerSummary: 'Measures normal share circulation.',
    bullishMeaning: 'High average volume ensures you can buy or sell whenever you want without delay.',
    bearishMeaning: 'Thinly traded stock; may be harder to sell large quantities quickly.',
    formatValue: (v) => `${Math.round(Number(v)).toLocaleString()} shares`,
  },
  avg_daily_volume_20d: {
    name: 'Daily Share Liquidity',
    category: 'Trading Volume',
    categoryColor: 'emerald',
    simpleDescription: 'Typical daily number of shares that change hands on the Colombo Stock Exchange.',
    beginnerSummary: 'Guarantees there are enough active buyers and sellers in the order book.',
    bullishMeaning: 'Abundant share liquidity ensures tight spreads between buy and sell prices.',
    bearishMeaning: 'Low share liquidity; orders might take longer to fill.',
    formatValue: (v) => `${Math.round(Number(v)).toLocaleString()} shares`,
  },
  avg_daily_turnover_20d: {
    name: 'Daily Cash Liquidity (Turnover)',
    category: 'Trading Volume',
    categoryColor: 'emerald',
    simpleDescription: 'The average daily cash value traded in Sri Lankan Rupees over the last month.',
    beginnerSummary: 'The safety litmus test: High turnover (>LKR 1 Million) means easy cash-out at any time.',
    bullishMeaning: 'High daily cash flow guarantees instant order execution and low risk of getting stuck.',
    bearishMeaning: 'Low turnover; suitable only for patient, small-sized positions.',
    formatValue: (v) => `LKR ${Math.round(Number(v)).toLocaleString()}`,
  },
  obv: {
    name: 'On-Balance Volume (Smart Money Flow)',
    category: 'Trading Volume',
    categoryColor: 'emerald',
    simpleDescription: 'Cumulative volume indicator that adds volume on up days and subtracts on down days.',
    beginnerSummary: 'Detects whether "smart money" (institutions) is quietly accumulating shares.',
    bullishMeaning: 'Rising OBV reveals strong stealth accumulation before a price breakout.',
    bearishMeaning: 'Falling OBV warns large players are quietly unloading shares.',
    formatValue: (v) => `${Math.round(Number(v)).toLocaleString()}`,
  },

  // --- Relative Strength vs CSE Market (Alpha Generation) ---
  rs_vs_aspi_5d: {
    name: '1-Week Beat-the-Market (Alpha vs ASPI)',
    category: 'Market Outperformance',
    categoryColor: 'blue',
    simpleDescription: 'Measures how much better this stock performed compared to the general ASPI market this week.',
    beginnerSummary: 'Positive percentage means this stock is beating the overall Sri Lankan stock market.',
    bullishMeaning: 'Outperforming the market during the week proves true institutional strength.',
    bearishMeaning: 'Lagging behind the general market trend.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  rs_vs_aspi_20d: {
    name: '1-Month Beat-the-Market (Alpha vs ASPI)',
    category: 'Market Outperformance',
    categoryColor: 'blue',
    simpleDescription: 'Stock return minus ASPI market return over the past 20 trading days.',
    beginnerSummary: 'The core alpha metric: Identifies true market leaders on the Colombo Stock Exchange.',
    bullishMeaning: 'Strong market outperformance confirms this stock is an island-wide leader.',
    bearishMeaning: 'Underperforming the broader market over the past month.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },

  // --- 52-Week Extreme Distances ---
  dist_from_52w_high: {
    name: 'Distance from 1-Year High',
    category: '52-Week Extremes',
    categoryColor: 'rose',
    simpleDescription: 'Percentage difference between current price and the highest price of the past year.',
    beginnerSummary: 'Stocks near 52-week highs (-5% to 0%) have virtually no "bag-holders" and tend to break out.',
    bullishMeaning: 'Trading near the 1-year peak shows tremendous upward momentum and breakout potential.',
    bearishMeaning: 'Far below the peak (-30% or more), meaning heavy overhead resistance.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
  dist_from_52w_low: {
    name: 'Distance from 1-Year Floor',
    category: '52-Week Extremes',
    categoryColor: 'rose',
    simpleDescription: 'How far current price has bounced from its lowest price in the last 12 months.',
    beginnerSummary: 'Measures the strength of the stock’s recovery from its rock-bottom floor.',
    bullishMeaning: 'Solid rebound from 1-year lows proves the bear market phase has ended.',
    bearishMeaning: 'Hovering near rock bottom; higher risk of further breakdown.',
    formatValue: (v) => `${(Number(v) * 100).toFixed(2)}%`,
  },
};

/**
 * Returns complete beginner-friendly metadata for any feature name.
 * Automatically falls back to human-friendly parsing for unknown features.
 */
export function getFeatureMeta(featureKey) {
  if (!featureKey) {
    return {
      key: 'unknown',
      name: 'Alpha Factor',
      category: 'General',
      categoryColor: 'slate',
      simpleDescription: 'Quantitative statistical indicator evaluated by the LightGBM model.',
      beginnerSummary: 'Measures historical price and volume behavior to forecast 10-day alpha.',
      bullishMeaning: 'Positive influence supporting the stock recommendation.',
      bearishMeaning: 'Cautionary factor weighing on the score.',
      formatValue: (v) => (v !== undefined && v !== null ? String(v) : '-'),
    };
  }

  const cleanKey = String(featureKey).trim();
  if (FEATURE_METADATA[cleanKey]) {
    return { key: cleanKey, ...FEATURE_METADATA[cleanKey] };
  }

  // Smart heuristic for unmapped or transformed features
  const lower = cleanKey.toLowerCase();
  let name = cleanKey.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  let category = 'Technical Indicator';
  let categoryColor = 'slate';
  let simpleDescription = 'Technical indicator derived from daily price action and volume.';
  let beginnerSummary = 'Evaluated by the AI model to project potential upside over the CSE benchmark.';

  if (lower.includes('sma') || lower.includes('ema') || lower.includes('trend')) {
    category = 'Trendlines';
    categoryColor = 'indigo';
    name = name.replace('Sma', 'SMA').replace('Ema', 'EMA');
    simpleDescription = 'Moving average baseline tracking smoothed price direction.';
  } else if (lower.includes('volume') || lower.includes('turnover') || lower.includes('obv')) {
    category = 'Trading Volume';
    categoryColor = 'emerald';
    simpleDescription = 'Measures share liquidity and buyer trading enthusiasm on the Colombo market.';
  } else if (lower.includes('macd')) {
    category = 'Momentum Signals';
    categoryColor = 'purple';
    name = name.replace('Macd', 'MACD');
    simpleDescription = 'Speed indicator measuring the acceleration of buyer vs seller pressure.';
  } else if (lower.includes('rsi') || lower.includes('stochastic')) {
    category = 'Valuation Gauge';
    categoryColor = 'emerald';
    name = name.replace('Rsi', 'RSI');
    simpleDescription = 'Oscillator measuring whether the price is a bargain or overheated.';
  } else if (lower.includes('bollinger')) {
    category = 'Volatility Bands';
    categoryColor = 'cyan';
    simpleDescription = 'Statistical price channel tracking typical price boundaries.';
  } else if (lower.includes('volatility') || lower.includes('atr')) {
    category = 'Risk & Volatility';
    categoryColor = 'amber';
    simpleDescription = 'Measures price fluctuations and risk buffer for setting stop-losses.';
  } else if (lower.includes('aspi') || lower.includes('rs_')) {
    category = 'Market Outperformance';
    categoryColor = 'blue';
    name = name.replace('Aspi', 'ASPI');
    simpleDescription = 'Compares this individual stock’s return directly against the CSE ASPI index.';
  }

  return {
    key: cleanKey,
    name,
    category,
    categoryColor,
    simpleDescription,
    beginnerSummary,
    bullishMeaning: 'Positive factor lifting the AI model confidence score.',
    bearishMeaning: 'Negative drag pulling the confidence score down.',
    formatValue: (v) => (v !== undefined && v !== null ? String(v) : '-'),
  };
}
