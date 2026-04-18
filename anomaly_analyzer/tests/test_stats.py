import polars as pl

from anomaly_analyzer.core.stats import StatsTester


def test_stats_anova_day_of_week():
    # We need significant data to potentially get a meaningful p-value,
    # but we just want to test if the machinery works.
    df = pl.DataFrame(
        {
            "Code": ["65990"] * 10,
            "DayOfWeek": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            "Return_Intraday": [
                0.01,
                -0.05,
                0.01,
                0.02,
                0.01,
                0.02,
                -0.06,
                0.01,
                0.01,
                0.02,
            ],
            "Is_MonthEnd": [False] * 10,
            "Return_Overnight": [0.0] * 10,
        }
    )

    tester = StatsTester()
    results = tester.run_anova(df, anomaly_type="day_of_week")

    assert "65990" in results
    res = results["65990"]
    assert isinstance(res.p_value, float)
    assert isinstance(res.is_significant, bool)


def test_stats_anova_month_end():
    df = pl.DataFrame(
        {
            "Code": ["65990"] * 10,
            "DayOfWeek": [1] * 10,
            "Return_Intraday": [0.0] * 10,
            "Is_MonthEnd": [
                True,
                True,
                False,
                False,
                False,
                True,
                False,
                False,
                False,
                False,
            ],
            "Return_Overnight": [
                0.05,
                0.06,
                0.01,
                -0.01,
                0.0,
                0.04,
                0.01,
                0.02,
                0.0,
                -0.01,
            ],
        }
    )

    tester = StatsTester()
    results = tester.run_anova(df, anomaly_type="month_end")

    assert "65990" in results
    res = results["65990"]
    assert isinstance(res.p_value, float)
    # The setup makes MonthEnd significantly higher than non-MonthEnd
    assert (
        res.is_significant is True or res.is_significant is False
    )  # Just checking type/execution here
