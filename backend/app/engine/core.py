import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from app.engine.metrics import Metrics, compute_metrics
from app.engine.types import Account, Bar, BarRecord, Context, Costs, Fill, Strategy


def execute(account: Account, bar: Bar, costs: Costs) -> tuple[Account, Fill | None]:
    """직전 봉에 정한 목표 비중을 이번 봉 시가에 체결한다."""
    target = account.pending_target
    # dataclasses.replace는 봉마다 여러 번 불리면 느려서 직접 만든다.
    account = Account(account.cash, account.qty)
    if target is None:
        return account, None

    price = bar.open
    equity = account.equity(price)
    if equity <= 0 or abs(target - account.weight(price)) < costs.min_trade:
        return account, None

    desired_qty = target * equity / price
    if desired_qty > account.qty:
        fill_price = price * (1 + costs.slippage)
        # 수수료까지 현금 안에서 내도록 매수 금액을 제한한다.
        notional = min(
            (desired_qty - account.qty) * fill_price, account.cash / (1 + costs.fee)
        )
        if notional <= 0:
            return account, None
        qty = notional / fill_price
        fee = notional * costs.fee
        account = Account(account.cash - notional - fee, account.qty + qty)
        return account, Fill(bar.ts, "buy", qty, fill_price, notional, fee)

    fill_price = price * (1 - costs.slippage)
    # 목표가 0이면 잔량 없이 전부 판다.
    qty = account.qty if target == 0 else account.qty - desired_qty
    notional = qty * fill_price
    fee = notional * costs.fee
    account = Account(account.cash + notional - fee, account.qty - qty)
    return account, Fill(bar.ts, "sell", qty, fill_price, notional, fee)


def step(
    account: Account,
    bar: Bar,
    features: Mapping[str, float],
    strategy: Strategy,
    costs: Costs,
) -> tuple[Account, BarRecord]:
    """봉 하나를 처리한다: 체결(시가) → 평가(종가) → 판단(종가).

    백테스트와 실시간 가상 계좌가 모두 이 함수만 쓴다.
    """
    account, fill = execute(account, bar, costs)

    equity = account.equity(bar.close)
    weight = account.weight(bar.close)
    context = Context(
        cash=account.cash,
        qty=account.qty,
        equity=equity,
        weight=weight,
        features=features,
    )
    target = strategy.on_bar(bar, context)
    if math.isnan(target):
        raise ValueError(f"strategy returned NaN at {bar.ts}")
    target = min(max(target, 0.0), 1.0)

    account = Account(account.cash, account.qty, target)
    record = BarRecord(bar.ts, bar.close, equity, account.qty, weight, fill, target)
    return account, record


@dataclass(frozen=True)
class BacktestResult:
    records: list[BarRecord]
    fills: list[Fill]
    metrics: Metrics
    final_account: Account


def run_backtest(
    bars: Sequence[Bar],
    strategy: Strategy,
    *,
    features: Iterable[Mapping[str, float]] | None = None,
    costs: Costs | None = None,
    initial_cash: float = 10_000.0,
) -> BacktestResult:
    """봉을 순서대로 하나씩 처리한다. 마지막 봉에서 정한 목표는 체결하지 않는다."""
    costs = costs or Costs()
    feature_rows = list(features) if features is not None else [{}] * len(bars)
    if len(feature_rows) != len(bars):
        raise ValueError("features must have one row per bar")

    account = Account(cash=initial_cash)
    records: list[BarRecord] = []
    for bar, row in zip(bars, feature_rows, strict=True):
        account, record = step(account, bar, row, strategy, costs)
        records.append(record)

    fills = [r.fill for r in records if r.fill is not None]
    metrics = compute_metrics(records, fills, initial_cash)
    return BacktestResult(records, fills, metrics, account)
