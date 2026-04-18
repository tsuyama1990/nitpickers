from typing import Literal

from pydantic import BaseModel, ConfigDict


class BacktestMetrics(BaseModel):
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float

    model_config = ConfigDict(extra="forbid")


class ChartDataPoint(BaseModel):
    Date: str
    Equity: float

    model_config = ConfigDict(extra="forbid")


class BacktestResult(BaseModel):
    metrics: BacktestMetrics
    chart_data: list[ChartDataPoint]

    model_config = ConfigDict(extra="forbid")


class StatsResult(BaseModel):
    anomaly_type: str
    f_value: float
    p_value: float
    is_significant: bool

    model_config = ConfigDict(extra="forbid")


class BacktestParams(BaseModel):
    target_tickers: list[str]
    slippage_pct: float
    target_anomaly: Literal["day_of_week", "month_end"]

    model_config = ConfigDict(extra="forbid")


class AnalysisPhase(BaseModel):
    phase: Literal[
        "idle", "fetching", "processing", "backtesting", "completed", "error"
    ]
    message: str

    model_config = ConfigDict(extra="forbid")
