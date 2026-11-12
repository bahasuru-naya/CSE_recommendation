/**
 * Comprehensive Stock Market Glossary for Beginners
 * Plain-English definitions, practical examples, and tips for Colombo Stock Exchange (CSE) investors.
 */

export const GLOSSARY_TERMS = [
  // --- BASICS ---
  {
    id: 'stock',
    term: 'Stock / Share',
    simple: 'A tiny piece of ownership in a real company.',
    details: 'When you buy shares of a company (like Commercial Bank or John Keells Holdings), you become a part-owner. If the company grows and makes profits, the value of your shares increases, and they may pay you cash dividends.',
    example: 'Buying 100 shares of COMB.N0000 at LKR 90 means you own LKR 9,000 worth of Commercial Bank.',
    category: 'basics',
  },
  {
    id: 'aspi',
    term: 'ASPI (All Share Price Index)',
    simple: 'The overall thermometer of the Sri Lankan stock market.',
    details: 'The ASPI measures the price movement of all companies listed on the Colombo Stock Exchange (CSE). If ASPI is green (up), the overall market is doing well. If ASPI is red (down), prices across the island are generally dropping.',
    example: 'If ASPI is at 12,500 and moves up +1.2%, it means Sri Lankan stocks on average gained 1.2% in value today.',
    category: 'basics',
  },
  {
    id: 'turnover',
    term: 'Market Turnover',
    simple: 'The total cash spent buying and selling shares today.',
    details: 'Turnover shows how much real money flowed through the Colombo Stock Exchange in a single day. High turnover (e.g., above LKR 1.5 Billion) means active interest from big investors and institutions, making it easier to buy and sell.',
    example: 'A turnover of "LKR 1.2B" means investors traded 1.2 billion rupees worth of stocks today.',
    category: 'basics',
  },
  {
    id: 'volume',
    term: 'Trading Volume',
    simple: 'The total number of individual share units traded today.',
    details: 'While turnover measures money in rupees, volume measures the physical number of shares that changed hands. Rising prices on high volume indicate strong, reliable buyer interest.',
    example: 'If 250,000 shares of LOLC were traded today, the volume is 250,000.',
    category: 'basics',
  },
  {
    id: 'cds_broker',
    term: 'CDS & Stockbroker',
    simple: 'Your official gateway to buying and selling shares in Sri Lanka.',
    details: 'In Sri Lanka, you cannot buy stocks directly from a website without a broker. You must open a free CDS (Central Depository System) account with a licensed CSE stockbroker (such as CT CLSA, CAL, Asha Securities, or Bartleet). This dashboard provides AI signals to help you decide, but you place the final orders through your broker app.',
    example: 'This system suggests buying LOLC at LKR 410 -> You log into your broker app (e.g., CAL Online) and submit the purchase order.',
    category: 'basics',
  },

  // --- TRADING SIGNALS & ACTIONS ---
  {
    id: 'signal_buy',
    term: 'BUY (Good Opportunity)',
    simple: 'High-confidence AI signal projecting price gains that easily beat CSE broker fees and the market.',
    details: 'A stock receives BUY when all 3 gates pass: 1) Model confidence score ≥ 65% probability of beating ASPI, 2) Daily turnover ≥ LKR 200,000 and volume ≥ 500 shares (liquid), and 3) ASPI index is trending above its 100-day SMA in a safe macro regime. The card provides an entry window (price ±1%), safety stop (2x ATR below), and profit target (3x ATR above).',
    example: 'Signal: BUY -> Click "Record Buy" to open a tracked holding in Portfolio with recommended share quantity and stop loss.',
    category: 'signals',
  },
  {
    id: 'signal_sell',
    term: 'SELL (Take Profit / Avoid)',
    simple: 'Time to lock in cash profits or step aside to prevent small losses from growing.',
    details: 'Triggered when model confidence drops to ≤ 35%, when the stock reaches its profit target, or when price breaches its safety stop loss. Also triggered on severe overbought RSI (>75) with drying volume.',
    example: 'If you bought at LKR 100 and it hits the LKR 118 target, the AI signals SELL to lock in your +18% gain.',
    category: 'signals',
  },
  {
    id: 'signal_hold',
    term: 'HOLD (Maintain Existing Shares)',
    simple: 'Neutral zone: Keep existing shares; do not commit new capital.',
    details: 'Assigned to liquid stocks with model confidence between 36% and 64%. Expected return is not high enough to comfortably clear the 2.68% round-trip CSE brokerage fee hurdle, but the stock is safely holding above its stop loss.',
    example: 'Stock is consolidating in a healthy range. If you own it, keep holding; if not, wait for a confirmed BUY breakout.',
    category: 'signals',
  },
  {
    id: 'signal_watch',
    term: 'WATCH (Wait & Monitor Liquidity)',
    simple: 'Thinly traded stock or consolidating pattern: Added to watchlist with breakout alerts.',
    details: 'Assigned whenever a stock trades less than LKR 200,000 in average daily turnover or fewer than 500 shares per day. This liquidity safety filter prevents you from getting trapped in illiquid shares with wide bid-ask spreads.',
    example: 'Stock has a promising chart pattern but thin daily volume. Monitored on your Watchlist until volume confirms real buyer interest.',
    category: 'signals',
  },
  {
    id: 'confidence',
    term: 'Model Confidence',
    simple: 'How sure the AI is (out of 100%) that this signal will succeed.',
    details: 'Our machine learning models analyze 25+ mathematical signals from historical CSE data. A confidence score of 80% or higher means historical patterns strongly favor this trade.',
    example: 'Confidence 85% = Very strong probability based on past market data.',
    category: 'signals',
  },
  {
    id: 'entry_range',
    term: 'Entry Range (Buying Window)',
    simple: 'The safe price zone to buy this stock.',
    details: 'Never chase a stock if its price has already skyrocketed! The entry range gives you the smart price interval. If the stock trades within this range, you get good value without overpaying.',
    example: 'Entry Range: LKR 120 - 124. If the price jumps to LKR 130, wait for it to drop back down instead of rushing in.',
    category: 'signals',
  },

  // --- RISK MANAGEMENT (SAFETY NETS) ---
  {
    id: 'stop_loss',
    term: 'Stop Loss (Safety Net)',
    simple: 'Your emergency brake: Sell if the price drops here to protect your money.',
    details: 'No prediction is 100% guaranteed. The stop loss protects you from big losses. If the stock falls to this price, you sell immediately. You take a small, controlled loss instead of watching your savings shrink by 30% or 50%.',
    example: 'You buy at LKR 100 and set a Stop Loss at LKR 94. If bad news hits and the stock drops to 94, you sell and only lose LKR 6 per share, saving the remaining LKR 94.',
    category: 'risk',
  },
  {
    id: 'target_price',
    term: 'Target Price (Profit Goal)',
    simple: 'The realistic price level where you sell to lock in your profits.',
    details: 'Greed is the beginner\'s biggest enemy. When a stock reaches its Target Price, our models calculate that the easiest gains have been made. Selling here turns "paper profits" into real cash in your bank.',
    example: 'You buy at LKR 100 with a Target of LKR 115. When it hits LKR 115, sell your shares and celebrate a +15% gain.',
    category: 'risk',
  },
  {
    id: 'atr',
    term: 'ATR (Average True Range)',
    simple: 'How much a stock\'s price typically bounces up or down in a normal day.',
    details: 'ATR measures volatility (price swings). A calm stock might move by only LKR 1 per day (low ATR), while an energetic stock might swing by LKR 20 (high ATR). Our system uses 2x ATR for Stop Loss and 3x ATR for Target Price so you don\'t get knocked out by normal daily noise.',
    example: 'If LOLC has an ATR of LKR 5, a 2x ATR Stop Loss sits LKR 10 below your purchase price.',
    category: 'risk',
  },
  {
    id: 'reward_risk',
    term: 'Reward / Risk Ratio',
    simple: 'How much profit you can gain compared to what you could lose.',
    details: 'Professional investors only enter trades where the upside is substantially bigger than the downside. A ratio of 1 : 1.5 means for every 1 Rupee you risk losing, you stand to make 1.50 Rupees or more in expected profit.',
    example: 'Risking LKR 4 to make LKR 8 gives a healthy 1 : 2.0 Reward/Risk ratio.',
    category: 'risk',
  },
  {
    id: 'cost_hurdle',
    term: 'Cost Hurdle (2.68% CSE Fees)',
    simple: 'Brokerage fees & government taxes required to break even.',
    details: 'When trading on the Colombo Stock Exchange, buying costs ~1.12% in fees/taxes and selling costs ~1.12% (plus CSE CDS and SEC levies), totaling approximately 2.68% for a complete round-trip trade. A stock MUST grow more than 2.68% for you to make a true net profit. Our AI automatically screens out trades that cannot comfortably clear this hurdle.',
    example: 'If you invest LKR 100,000, approximately LKR 2,680 goes to official fees. Your stock must reach at least LKR 102,680 to break even.',
    category: 'risk',
  },
  {
    id: 'position_sizing',
    term: 'Position Sizing / Max Quantity',
    simple: 'How much of your total money to put into this single stock.',
    details: 'Never put all your eggs in one basket! Position sizing limits each stock to a modest slice of your total savings (e.g., 5% to 10%). If one company encounters unexpected bad news, the rest of your portfolio stays safe.',
    example: 'If your total investing budget is LKR 500,000, a 5% position size means investing at most LKR 25,000 in this stock.',
    category: 'risk',
  },

  // --- MARKET REGIMES & CONDITIONS ---
  {
    id: 'market_regime',
    term: 'Market Regime (Overall Mood)',
    simple: 'The broader weather forecast for the Colombo Stock Exchange.',
    details: 'Stocks move together with the overall market. If the overall CSE index (ASPI) is trending above its 100-day average, the market is "BULLISH" (warm sunshine). If below, it is "BEARISH" (stormy weather).',
    example: 'BULLISH regime = Green light for buying. BEARISH regime = Exercise caution and hold more cash.',
    category: 'market',
  },
  {
    id: 'bullish',
    term: 'Bullish (Upward Trend)',
    simple: 'Prices are trending up and buyers are in control.',
    details: 'Named after a bull thrusting its horns upward. In a bullish market, investor optimism is high, companies report growing earnings, and most stocks rise over time.',
    example: 'The ASPI index climbing from 11,000 to 12,500 over a few months is a bullish market.',
    category: 'market',
  },
  {
    id: 'bearish',
    term: 'Bearish (Downward Trend)',
    simple: 'Prices are trending down and sellers dominate.',
    details: 'Named after a bear swiping its paws downward. In a bearish market, fear or economic uncertainty causes people to sell shares, pushing prices lower.',
    example: 'When the market is bearish, the system reduces BUY signals to protect your capital.',
    category: 'market',
  },
  {
    id: 'liquidity',
    term: 'Liquidity / Liquid Stock',
    simple: 'How easily you can turn your shares back into cash.',
    details: 'A "liquid" stock has hundreds of buyers and sellers trading it every day. You can sell your shares in seconds. An "illiquid" stock has very few traders — if you want to sell, you might have to wait days or lower your price drastically.',
    example: 'Our system checks 20-day average turnover and ensures a stock has at least LKR 200,000+ daily trading before recommending it.',
    category: 'market',
  },

  // --- PORTFOLIO & MONEY TRACKING ---
  {
    id: 'unrealized_pnl',
    term: 'Unrealized P&L (Paper Profit/Loss)',
    simple: 'What you would gain or lose if you sold all your shares right now.',
    details: 'P&L stands for Profit and Loss. "Unrealized" means it exists on paper based on today\'s share price, but hasn\'t been turned into actual cash yet because you still hold the shares.',
    example: 'You bought shares for LKR 50,000. Today they are worth LKR 56,000. Your Unrealized P&L is +LKR 6,000 (+12%).',
    category: 'portfolio',
  },
  {
    id: 'portfolio_valuation',
    term: 'Portfolio Value',
    simple: 'The total cash worth of all the stocks you currently own.',
    details: 'Calculated by multiplying the number of shares you own in each company by today\'s latest closing price.',
    example: '500 shares at LKR 100 + 1,000 shares at LKR 50 = LKR 100,000 total portfolio value.',
    category: 'portfolio',
  },
  {
    id: 'watchlist',
    term: 'Watchlist',
    simple: 'A personal bookmark list of stocks you want to monitor.',
    details: 'You can add promising stocks to your watchlist with alert price targets. When the stock reaches your desired price, you receive a visual reminder to consider buying.',
    example: 'Watching COMB.N0000 with an alert at LKR 88.00.',
    category: 'portfolio',
  },

  // --- AI & TECHNICAL INDICATORS ---
  {
    id: 'shap',
    term: 'SHAP (AI Explanations)',
    simple: 'A report card showing exactly why the AI made a recommendation.',
    details: 'Unlike "black box" algorithms, SHAP (SHapley Additive exPlanations) opens the AI\'s brain and lists every clue that contributed to the score — such as strong momentum, low valuation, or sudden volume spikes.',
    example: 'A SHAP score of "+0.045 Bullish Boost" from 20-day momentum means recent price strength was a major positive reason for the BUY signal.',
    category: 'ai_models',
  },
  {
    id: 'rsi',
    term: 'RSI (Relative Strength Index)',
    simple: 'A speed gauge from 0 to 100 telling if a stock is over-hyped or a bargain.',
    details: 'RSI measures the speed of recent price changes. An RSI below 30 means the stock is "oversold" (heavily discounted, potential bargain). An RSI above 70 means "overbought" (very hot, might take a breather).',
    example: 'RSI at 45 = Balanced, healthy momentum with room to grow.',
    category: 'ai_models',
  },
  {
    id: 'macd',
    term: 'MACD (Trend Momentum)',
    simple: 'An indicator that signals when the direction of momentum is changing.',
    details: 'MACD (Moving Average Convergence Divergence) tracks the relationship between short-term and medium-term price trends. When the MACD line crosses above its signal line, it\'s like a green traffic light indicating upward speed.',
    example: 'MACD Bullish Crossover = Upward trend is accelerating.',
    category: 'ai_models',
  },
  {
    id: 'moving_average',
    term: 'Moving Average (SMA / 100D SMA)',
    simple: 'The smoothed-out average price over recent days.',
    details: 'Stock prices jump up and down every minute. A 100-day Simple Moving Average (SMA) smooths out the daily noise to show the real underlying direction. If the current price is above the 100-day average, the long-term trend is positive.',
    example: 'If LOLC is at LKR 410 and its 100-day average is LKR 380, the stock is in a solid uptrend.',
    category: 'ai_models',
  },
  {
    id: 'win_rate',
    term: 'Win Rate',
    simple: 'The percentage of past AI recommendations that generated profit.',
    details: 'Calculated over hundreds of historical backtested trades. A win rate around 60% - 65% is considered outstanding in financial markets, especially when combined with a good Reward-to-Risk ratio.',
    example: 'A 62.5% win rate means out of 100 trades, 62 or 63 made a net profit after fees.',
    category: 'ai_models',
  },
  {
    id: 'sharpe_ratio',
    term: 'Sharpe Ratio (Risk-Adjusted Return)',
    simple: 'A rating of how much return the strategy generated per unit of risk.',
    details: 'Making a 20% return with wild 50% drops is scary. Making a 15% return with smooth, calm steps is far better. The Sharpe Ratio measures this balance. Anything above 1.0 is considered good; above 1.5 is excellent.',
    example: 'A Sharpe ratio of 1.48 means the model produces solid returns without putting your savings through a wild rollercoaster.',
    category: 'ai_models',
  },
  {
    id: 'max_drawdown',
    term: 'Max Drawdown (Worst Historical Dip)',
    simple: 'The biggest peak-to-bottom drop the strategy experienced in testing.',
    details: 'Tells you the worst-case temporary dip you would have had to endure in historical backtests before the portfolio recovered to new highs.',
    example: 'A max drawdown of -8.4% means at its worst historical point, the portfolio dropped 8.4% from its highest peak before rebounding.',
    category: 'ai_models',
  },
];

/**
 * Helper function to retrieve a term by id
 */
export function getGlossaryTerm(id) {
  if (!id) return null;
  return GLOSSARY_TERMS.find((t) => t.id.toLowerCase() === id.toLowerCase()) || null;
}
