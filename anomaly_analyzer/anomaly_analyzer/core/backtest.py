from typing import Literal

import pandas as pd
import polars as pl

from anomaly_analyzer.core.domain_models.analysis import (
    BacktestMetrics,
    BacktestResult,
    ChartDataPoint,
)


class Backtester:
    def __init__(self, slippage_pct: float) -> None:
        self.slippage = slippage_pct / 100.0

    def run(
        self, df: pl.DataFrame, anomaly_type: Literal["day_of_week", "month_end"]
    ) -> dict[str, BacktestResult]:
        """
        Run backtest using vectorbt based on the specified anomaly type.
        Returns a dictionary of BacktestResult keyed by ticker code.
        """
        results: dict[str, BacktestResult] = {}

        if df.is_empty():
            return results

        # Iterate over unique codes
        for code in df["Code"].unique().to_list():
            code_df = df.filter(pl.col("Code") == code)

            # Convert to pandas for vectorbt
            pdf = code_df.to_pandas()
            pdf.set_index("Date", inplace=True)

            entries = pd.Series(False, index=pdf.index, dtype=bool)
            exits = pd.Series(False, index=pdf.index, dtype=bool)

            if anomaly_type == "day_of_week":
                # Buy Tuesday Open, Sell Tuesday Close (Intraday)
                # Polars weekday: 1=Mon, 2=Tue...
                is_tuesday = pdf["DayOfWeek"] == 2
                entries[is_tuesday] = True
                exits[is_tuesday] = True
                price_in = pdf["Open"].astype(float)
                price_out = pdf["Close"].astype(float)

            elif anomaly_type == "month_end":
                # Buy Month End Close, Sell Next Day Open (Overnight)
                is_month_end = pdf["Is_MonthEnd"].astype(bool)
                entries[is_month_end] = True
                # Shift entries by 1 to get the exit signal on the next day
                exits = entries.shift(1).fillna(False).astype(bool)
                price_in = pdf["Close"].astype(float)
                price_out = pdf["Open"].astype(float)
            else:
                continue

            # Calculate return for each signal
            returns = pd.Series(0.0, index=pdf.index)
            if anomaly_type == "day_of_week":
                # Intraday return on Tuesday
                returns[entries] = (price_out[entries] - price_in[entries]) / price_in[
                    entries
                ]
            elif anomaly_type == "month_end":
                # Overnight return
                # We need the previous day's close for the entry price
                shifted_price_in = price_in.shift(1)
                returns[exits] = (
                    price_out[exits] - shifted_price_in[exits]
                ) / shifted_price_in[exits]

            # Apply slippage
            returns[returns != 0.0] = returns[returns != 0.0] - (
                self.slippage * 2
            )  # slippage on entry and exit

            # Using Portfolio.from_orders to construct portfolio exactly matching the returns
            # vbt.Portfolio.from_returns doesn't exist, we use a simple compounding approach
            # or from_orders if we want full metrics. But for simplicity and accurate stats,
            # we can create an artificial price series and just buy and hold it.
            # Cumulate returns to get an equity curve
            equity = (1 + returns).cumprod() * 100.0

            # Then we can use Portfolio.from_orders, buying at start and holding the equity curve
            # Or even simpler, vectorbt accepts custom returns if we use from_orders properly,
            # but we can just calculate the metrics directly since we have the equity curve!

            # Actually, `vbt.Portfolio.from_orders` requires prices and sizes.
            # Let's just calculate the metrics manually from the returns series to be 100% accurate
            # for this custom anomaly backtest.

            total_return = (
                float(equity.iloc[-1] / equity.iloc[0] - 1.0)
                if not equity.empty
                else 0.0
            )

            # Max drawdown
            roll_max = equity.cummax()
            drawdown = (equity - roll_max) / roll_max
            max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0

            # Win rate
            winning_trades = (returns > 0).sum()
            total_trades = (returns != 0).sum()
            win_rate = float(winning_trades / total_trades) if total_trades > 0 else 0.0

            # Profit factor
            gross_profit = returns[returns > 0].sum()
            gross_loss = abs(returns[returns < 0].sum())
            profit_factor = (
                float(gross_profit / gross_loss)
                if gross_loss > 0
                else float("inf")
                if gross_profit > 0
                else 0.0
            )

            # Sharpe ratio (annualized)
            mean_return = returns.mean()
            std_return = returns.std()
            sharpe_ratio = (
                float((mean_return / std_return) * (252**0.5))
                if std_return > 0
                else 0.0
            )

            metrics = BacktestMetrics(
                total_return=total_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                profit_factor=profit_factor,
            )

            chart_data = [
                ChartDataPoint(
                    Date=str(idx.date() if hasattr(idx, "date") else idx),
                    Equity=float(val),
                )
                for idx, val in equity.items()
            ]

            results[code] = BacktestResult(metrics=metrics, chart_data=chart_data)

        return results
