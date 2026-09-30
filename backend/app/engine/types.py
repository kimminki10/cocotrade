from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol


@dataclass(frozen=True)
class Bar:
    ts: datetime  # 봉 시작 시각 (UTC)
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Costs:
    fee: float = 0.001  # 편도 수수료율
    slippage: float = 0.0005  # 편도 슬리피지
    min_trade: float = 0.01  # 목표와 현재 비중 차이가 이보다 작으면 거래하지 않는다


@dataclass(frozen=True)
class Account:
    """봉 사이에 이어지는 계좌 상태. 실시간 가상 계좌는 이 값을 DB에 저장했다가 다음 봉에 이어 쓴다."""

    cash: float
    qty: float = 0.0
    # 직전 봉 종가에 정한 목표 비중. 이번 봉 시가에 체결한다.
    pending_target: float | None = None

    def equity(self, price: float) -> float:
        return self.cash + self.qty * price

    def weight(self, price: float) -> float:
        equity = self.equity(price)
        return self.qty * price / equity if equity > 0 else 0.0


@dataclass(frozen=True)
class Fill:
    ts: datetime
    side: Literal["buy", "sell"]
    qty: float
    price: float  # 슬리피지를 반영한 체결가
    notional: float  # qty × price
    fee: float


@dataclass(frozen=True)
class Context:
    """전략이 볼 수 있는 정보. 이번 봉까지의 값만 들어 있다."""

    cash: float
    qty: float
    equity: float
    weight: float
    features: Mapping[str, float]


class Strategy(Protocol):
    def on_bar(self, bar: Bar, context: Context) -> float:
        """이번 봉까지의 정보로 다음 목표 비중(0.0–1.0)을 반환한다."""
        ...


@dataclass(frozen=True)
class BarRecord:
    ts: datetime
    close: float
    equity: float  # 종가 기준 평가액
    qty: float
    weight: float  # 종가 기준 보유 비중
    fill: Fill | None
    target: float  # 이번 봉 종가에 정한 다음 목표 비중
