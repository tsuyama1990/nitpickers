import polars as pl
import pytest

from anomaly_analyzer.core.domain_models.api import JQuantsQuote
from anomaly_analyzer.core.etl import ETLProcessor


def test_etl_processing():
    quotes = [
        JQuantsQuote(
            Date="2023-01-30",
            Code="65990",
            Open=100.0,
            High=110.0,
            Low=90.0,
            Close=105.0,
            Volume=1000.0,
        ),
        JQuantsQuote(
            Date="2023-01-31",
            Code="65990",
            Open=106.0,
            High=120.0,
            Low=100.0,
            Close=110.0,
            Volume=2000.0,
        ),  # Month End
        JQuantsQuote(
            Date="2023-02-01",
            Code="65990",
            Open=112.0,
            High=115.0,
            Low=110.0,
            Close=114.0,
            Volume=1500.0,
        ),
    ]

    processor = ETLProcessor()
    df = processor.process_quotes(quotes)

    assert len(df) == 3
    assert df.schema["Date"] == pl.Date
    assert df.schema["Code"] == pl.Utf8

    # Check returns for the second day (2023-01-31)
    row_1 = df.row(1, named=True)
    # Return Daily: (110 - 105) / 105 = 5/105 ~= 0.047619
    assert pytest.approx(row_1["Return_Daily"], rel=1e-3) == 0.047619
    # Return Intraday: (110 - 106) / 106 = 4/106 ~= 0.037735
    assert pytest.approx(row_1["Return_Intraday"], rel=1e-3) == 0.037735
    # Return Overnight: (106 - 105) / 105 = 1/105 ~= 0.009523
    assert pytest.approx(row_1["Return_Overnight"], rel=1e-3) == 0.009523

    # Check MonthEnd flag
    assert df.row(0, named=True)["Is_MonthEnd"] is False
    assert df.row(1, named=True)["Is_MonthEnd"] is True
    assert (
        df.row(2, named=True)["Is_MonthEnd"] is True
    )  # Last row is True due to fill_null

    # Check DayOfWeek (2023-01-30 is Monday = 1)
    assert df.row(0, named=True)["DayOfWeek"] == 1


def test_etl_forward_fill():
    quotes = [
        JQuantsQuote(
            Date="2023-01-04",
            Code="65990",
            Open=100.0,
            High=110.0,
            Low=90.0,
            Close=105.0,
            Volume=1000.0,
        ),
        JQuantsQuote(
            Date="2023-01-05",
            Code="65990",
            Open=0.0,
            High=0.0,
            Low=0.0,
            Close=0.0,
            Volume=0.0,
        ),  # Zero values
        JQuantsQuote(
            Date="2023-01-06",
            Code="65990",
            Open=110.0,
            High=115.0,
            Low=105.0,
            Close=112.0,
            Volume=1500.0,
        ),
    ]

    processor = ETLProcessor()
    df = processor.process_quotes(quotes)

    row_1 = df.row(1, named=True)
    assert row_1["Open"] == 100.0
    assert row_1["Close"] == 105.0
