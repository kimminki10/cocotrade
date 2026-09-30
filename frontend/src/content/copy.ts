// 화면에 보이는 짧은 문구는 모두 여기에 둔다. 컴포넌트에는 문구를 직접 쓰지 않는다.
// 긴 글(방법론 등)은 페이지별 Markdown 파일로 둔다.
// 값이 들어가는 문구(그림 설명 등)는 함수로 둔다.

export const copy = {
  site: {
    name: "cocotrade",
    description: "Backtests and a live, public track record of Jev forecasts on crypto markets.",
  },
  nav: {
    backtest: "Backtest",
    compare: "Compare",
  },
  disclaimer:
    "cocotrade shows model outputs for research and education. Nothing here is investment advice. Simulated and past results do not predict future returns.",
  home: {
    title: "Where will BTC and ETH be in four hours?",
    lead: "Every hour, when a 1-hour candle closes, Jev assigns probabilities to up, flat and down (±0.3%) for the close four hours later. Every call is logged and checked against what happened.",
  },
  markets: {
    heading: "Market data",
    columns: {
      symbol: "Symbol",
      timeframe: "Timeframe",
      candles: "Candles",
      first: "First (UTC)",
      last: "Last (UTC)",
    },
  },

  strategies: {
    buy_hold: {
      name: "Buy & hold",
      summary: "Buys on the first bar and never sells. The baseline for every result.",
    },
    sma_cross: {
      name: "SMA crossover",
      summary: "Holds while the 24-hour moving average is above the 168-hour one.",
    },
    macd: {
      name: "MACD",
      summary: "Holds while the MACD line (EMA 12 − EMA 26) is above its 9-bar signal line.",
    },
    donchian: {
      name: "Donchian breakout",
      summary: "Buys a close above the prior 20-bar high and sells a close below the prior 10-bar low.",
    },
    rsi: {
      name: "RSI reversion",
      summary: "Buys when the 14-bar RSI drops below 30 and sells when it rises above 70.",
    },
    bollinger: {
      name: "Bollinger reversion",
      summary: "Buys below the lower band (20-bar mean − 2σ) and sells once the close is back above the mean.",
    },
  },

  form: {
    strategy: "Strategy",
    symbol: "Market",
    start: "From (UTC)",
    end: "To (UTC)",
    fee: "Fee per side, %",
    slippage: "Slippage per side, %",
    runBacktest: "Run backtest",
    runCompare: "Compare",
  },

  metrics: {
    total_return: "Total return",
    cagr: "CAGR",
    volatility: "Volatility, annualized",
    sharpe: "Sharpe ratio",
    sortino: "Sortino ratio",
    max_drawdown: "Max drawdown",
    calmar: "Calmar ratio",
    win_rate: "Win rate",
    round_trips: "Round trips",
    fills: "Fills",
    turnover: "Turnover",
    exposure: "Time in market",
    versus: (value: string) => `buy & hold ${value}`,
  },

  monkey: {
    name: "Monkey",
    percentile: "Monkey percentile",
    percentileNote: (runs: number) => `of ${runs} random traders`,
  },

  backtest: {
    eyebrow: "Backtest",
    title: "Run a textbook rule on a year of hourly candles",
    lead: "Decisions are made at each close and filled at the next open, with fees and slippage on every fill. The live virtual account will run on the same engine.",
    loading: "Running backtest and 200 monkeys…",
    fig: {
      equity: (strategy: string, symbol: string, from: string, to: string) =>
        `${strategy} (solid) against buy & hold (dashed), ${symbol}, ${from} – ${to}. Starting capital $10,000.`,
      drawdown: "Drawdown from the running peak.",
      marker: (strategy: string, value: string, percentile: string) =>
        `${strategy} ${value} · ${percentile} percentile`,
      monkeys: (runs: number, exposure: string, holding: string) =>
        `Total return of ${runs} monkeys that trade at random but match this strategy’s time in market (${exposure}) and average holding period (${holding}). The line marks the strategy.`,
    },
    trades: {
      heading: "Fills",
      showing: (shown: number, total: number) =>
        shown < total ? `Latest ${shown} of ${total}.` : `${total} in total.`,
      none: "No fills in this range.",
      columns: {
        ts: "Bar open (UTC)",
        side: "Side",
        price: "Price",
        qty: "Quantity",
        notional: "Notional",
        fee: "Fee",
      },
      side: { buy: "buy", sell: "sell" },
    },
    table: (strategy: string) => `${strategy} and buy & hold, same costs.`,
    fillsNote: (fills: string) => `${fills} fills`,
    hours: (hours: number) => `${hours} h`,
    assumptions: (fee: string, slippage: string) =>
      `Long only: a strategy is either in the market or in cash, so a bearish view can only mean holding cash. Fills at the next bar’s open with ${fee} fee and ${slippage} slippage per side. Order book depth and partial fills are not modeled; at this size and on these markets the effect is assumed to be small.`,
  },

  compare: {
    eyebrow: "Strategy comparison",
    title: "Do textbook rules beat a monkey?",
    lead: "Each rule is scored against 200 monkeys that buy and sell at random but spend the same share of time in the market and hold for as long on average. A strategy near the 50th percentile did about as well as luck.",
    loading: "Running 6 strategies and 1,200 monkeys…",
    columns: {
      strategy: "Strategy",
      total_return: "Return",
      cagr: "CAGR",
      sharpe: "Sharpe",
      max_drawdown: "Max DD",
      fills: "Fills",
      exposure: "In market",
      percentile: "Monkey pct.",
    },
    fig: (symbol: string, from: string, to: string) =>
      `Total return of each rule (dot) against its monkeys, ${symbol}, ${from} – ${to}. Thin line: 5th–95th percentile of monkeys. Bar: 25th–75th. Tick: median.`,
  },
} as const;

export type StrategyCopy = (typeof copy.strategies)[keyof typeof copy.strategies];
