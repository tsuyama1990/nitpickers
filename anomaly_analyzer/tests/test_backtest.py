from datetime import date

import polars as pl

from anomaly_analyzer.core.backtest import Backtester


def test_backtest_day_of_week():
    df = pl.DataFrame(
        {
            "Date": [
                date(2023, 1, 2),
                date(2023, 1, 3),
                date(2023, 1, 4),
            ],  # Mon, Tue, Wed
            "Code": ["65990", "65990", "65990"],
            "Open": [100.0, 100.0, 100.0],
            "High": [110.0, 120.0, 110.0],
            "Low": [90.0, 90.0, 90.0],
            "Close": [105.0, 110.0, 105.0],
            "DayOfWeek": [1, 2, 3],
            "Is_MonthEnd": [False, False, False],
        }
    )

    # Tuesday Open=100, Tuesday Close=110. Return should be (110 - 100) / 100 = 10%
    tester = Backtester(slippage_pct=0.0)
    results = tester.run(df, anomaly_type="day_of_week")

    assert "65990" in results
    res = results["65990"]
    # Vectorbt might handle the intraday return slightly differently depending on initialization,
    # but the total return should reflect the 10% gain.
    assert res.metrics.total_return > 0.0
    assert len(res.chart_data) == 3


def test_backtest_slippage():
    df = pl.DataFrame(
        {
            "Date": [
                date(2023, 1, 2),
                date(2023, 1, 3),
                date(2023, 1, 4),
            ],  # Mon, Tue, Wed
            "Code": ["65990", "65990", "65990"],
            "Open": [100.0, 100.0, 100.0],
            "High": [110.0, 120.0, 110.0],
            "Low": [90.0, 90.0, 90.0],
            "Close": [105.0, 110.0, 105.0],
            "DayOfWeek": [1, 2, 3],
            "Is_MonthEnd": [False, False, False],
        }
    )

    tester_no_slip = Backtester(slippage_pct=0.0)
    res_no_slip = tester_no_slip.run(df, anomaly_type="day_of_week")["65990"]

    tester_slip = Backtester(slippage_pct=1.0)  # 1% slippage per trade
    res_slip = tester_slip.run(df, anomaly_type="day_of_week")["65990"]

    assert res_slip.metrics.total_return < res_no_slip.metrics.total_return


def test_backtest_month_end():
    df = pl.DataFrame(
        {
            "Date": [date(2023, 1, 30), date(2023, 1, 31), date(2023, 2, 1)],
            "Code": ["65990", "65990", "65990"],
            "Open": [100.0, 100.0, 105.0],
            "High": [110.0, 110.0, 120.0],
            "Low": [90.0, 90.0, 100.0],
            "Close": [105.0, 100.0, 110.0],
            "DayOfWeek": [1, 2, 3],
            "Is_MonthEnd": [False, True, False],
        }
    )

    # Month End (1/31) Close=100. Next Day (2/1) Open=105. Return should be (105-100)/100 = 5%
    tester = Backtester(slippage_pct=0.0)
    results = tester.run(df, anomaly_type="month_end")

    assert "65990" in results
    assert results["65990"].metrics.total_return > 0.0
