"""규칙 기반 비교 전략. 파라미터는 교과서 기본값이다.

모든 전략은 받은 봉만 스스로 쌓아서 계산하므로 미래 봉을 볼 수 없다.
진입·청산 조건이 다른 전략(RSI, 볼린저, 돈치안)은 보유 여부를 스스로 기억한다.
"""

import math
from collections import deque

from app.engine.types import Bar, Context


class BuyAndHold:
    """첫 봉에서 전액 매수하고 계속 보유한다. 모든 결과의 비교 기준이다."""

    def on_bar(self, bar: Bar, context: Context) -> float:
        return 1.0


class SmaCross:
    """단기 이동평균이 장기 이동평균보다 위면 전액 보유, 아니면 현금."""

    def __init__(self, fast: int = 24, slow: int = 168) -> None:
        if not 0 < fast < slow:
            raise ValueError("need 0 < fast < slow")
        self.fast = fast
        self.slow = slow
        self._closes: deque[float] = deque(maxlen=slow)

    def on_bar(self, bar: Bar, context: Context) -> float:
        self._closes.append(bar.close)
        if len(self._closes) < self.slow:
            return 0.0
        closes = list(self._closes)
        fast_ma = sum(closes[-self.fast :]) / self.fast
        slow_ma = sum(closes) / self.slow
        return 1.0 if fast_ma > slow_ma else 0.0


class Ema:
    """지수 이동평균. 첫 값으로 시작한다 (pandas ewm(span, adjust=False)와 같다)."""

    def __init__(self, span: int) -> None:
        self.alpha = 2 / (span + 1)
        self.value: float | None = None
        self.count = 0

    def update(self, x: float) -> float:
        self.value = (
            x if self.value is None else self.alpha * x + (1 - self.alpha) * self.value
        )
        self.count += 1
        return self.value


class Macd:
    """MACD선(EMA12 − EMA26)이 시그널선(MACD의 EMA9) 위면 전액 보유."""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9) -> None:
        if not 0 < fast < slow:
            raise ValueError("need 0 < fast < slow")
        self.slow = slow
        self._fast = Ema(fast)
        self._slow = Ema(slow)
        self._signal = Ema(signal)
        self._signal_span = signal

    def on_bar(self, bar: Bar, context: Context) -> float:
        macd = self._fast.update(bar.close) - self._slow.update(bar.close)
        signal = self._signal.update(macd)
        if self._slow.count < self.slow + self._signal_span:
            return 0.0  # 워밍업
        return 1.0 if macd > signal else 0.0


class Donchian:
    """터틀 방식 돌파: 직전 N봉 최고가를 넘으면 매수, 직전 M봉 최저가를 깨면 매도."""

    def __init__(self, entry: int = 20, exit: int = 10) -> None:
        if entry <= 0 or exit <= 0:
            raise ValueError("periods must be positive")
        self.entry = entry
        self.exit = exit
        self._highs: deque[float] = deque(maxlen=entry)
        self._lows: deque[float] = deque(maxlen=exit)
        self._holding = False

    def on_bar(self, bar: Bar, context: Context) -> float:
        # 이번 봉은 넣기 전에 비교한다. "직전 N봉"에는 이번 봉이 들어가지 않는다.
        if (
            not self._holding
            and len(self._highs) == self.entry
            and bar.close > max(self._highs)
        ):
            self._holding = True
        elif (
            self._holding
            and len(self._lows) == self.exit
            and bar.close < min(self._lows)
        ):
            self._holding = False
        self._highs.append(bar.high)
        self._lows.append(bar.low)
        return 1.0 if self._holding else 0.0


class Rsi:
    """Wilder RSI가 과매도(30) 아래로 내려가면 매수, 과매수(70) 위로 올라가면 매도."""

    def __init__(self, period: int = 14, low: float = 30, high: float = 70) -> None:
        if not 0 < low < high < 100:
            raise ValueError("need 0 < low < high < 100")
        self.period = period
        self.low = low
        self.high = high
        self._alpha = 1 / period
        self._prev: float | None = None
        self._gain: float | None = None
        self._loss: float | None = None
        self._count = 0
        self._holding = False

    def value(self) -> float | None:
        """지금까지 받은 봉의 RSI. 워밍업 중이면 None."""
        if self._count < self.period or self._gain is None or self._loss is None:
            return None
        if self._loss == 0:
            return 100.0
        return 100 - 100 / (1 + self._gain / self._loss)

    def _update(self, close: float) -> None:
        if self._prev is not None:
            delta = close - self._prev
            gain, loss = max(delta, 0.0), max(-delta, 0.0)
            a = self._alpha
            self._gain = gain if self._gain is None else a * gain + (1 - a) * self._gain
            self._loss = loss if self._loss is None else a * loss + (1 - a) * self._loss
            self._count += 1
        self._prev = close

    def on_bar(self, bar: Bar, context: Context) -> float:
        self._update(bar.close)
        rsi = self.value()
        if rsi is not None:
            if not self._holding and rsi < self.low:
                self._holding = True
            elif self._holding and rsi > self.high:
                self._holding = False
        return 1.0 if self._holding else 0.0


class Bollinger:
    """종가가 하단 밴드(평균 − k·σ) 아래면 매수, 중간선(평균) 위로 돌아오면 매도."""

    def __init__(self, period: int = 20, k: float = 2.0) -> None:
        if period < 2 or k <= 0:
            raise ValueError("need period >= 2 and k > 0")
        self.period = period
        self.k = k
        self._closes: deque[float] = deque(maxlen=period)
        self._holding = False

    def on_bar(self, bar: Bar, context: Context) -> float:
        self._closes.append(bar.close)
        if len(self._closes) < self.period:
            return 0.0
        mean = sum(self._closes) / self.period
        # 볼린저 밴드는 관례상 모표준편차를 쓴다
        std = math.sqrt(sum((c - mean) ** 2 for c in self._closes) / self.period)
        if not self._holding and bar.close < mean - self.k * std:
            self._holding = True
        elif self._holding and bar.close > mean:
            self._holding = False
        return 1.0 if self._holding else 0.0


# 이름 → 기본 파라미터로 전략을 만드는 함수. API와 CLI가 함께 쓴다.
RULE_STRATEGIES = {
    "buy_hold": BuyAndHold,
    "sma_cross": SmaCross,
    "macd": Macd,
    "donchian": Donchian,
    "rsi": Rsi,
    "bollinger": Bollinger,
}
