// 화면에 보이는 짧은 문구는 모두 여기에 둔다. 컴포넌트에는 문구를 직접 쓰지 않는다.
// 긴 글(방법론 등)은 페이지별 Markdown 파일로 둔다.

export const copy = {
  site: {
    name: "cocotrade",
    description: "Backtests and a live, public track record of Jev forecasts on crypto markets.",
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
} as const;
