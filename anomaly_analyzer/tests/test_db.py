from pathlib import Path

import polars as pl
import pytest

from anomaly_analyzer.core.db import DBEngine


@pytest.fixture
def temp_db(tmp_path: Path) -> DBEngine:
    return DBEngine(data_dir=tmp_path)


def test_db_save_and_load(temp_db: DBEngine):
    df1 = pl.DataFrame(
        {
            "Date": ["2023-01-04", "2023-01-05"],
            "Code": ["65990", "65990"],
            "Open": [100.0, 110.0],
        }
    )
    temp_db.save_quotes(df1)

    loaded_df = temp_db.load_quotes()
    assert len(loaded_df) == 2
    assert loaded_df["Open"].to_list() == [100.0, 110.0]


def test_db_append_and_deduplicate(temp_db: DBEngine):
    df1 = pl.DataFrame(
        {
            "Date": ["2023-01-04", "2023-01-05"],
            "Code": ["65990", "65990"],
            "Open": [100.0, 110.0],
        }
    )
    temp_db.save_quotes(df1)

    # df2 has an overlapping row and a new row
    df2 = pl.DataFrame(
        {
            "Date": ["2023-01-05", "2023-01-06"],
            "Code": ["65990", "65990"],
            "Open": [115.0, 120.0],  # 115.0 will overwrite 110.0 because keep="last"
        }
    )
    temp_db.save_quotes(df2)

    loaded_df = temp_db.load_quotes()
    assert len(loaded_df) == 3
    assert loaded_df["Date"].to_list() == ["2023-01-04", "2023-01-05", "2023-01-06"]
    assert loaded_df["Open"].to_list() == [100.0, 115.0, 120.0]


def test_db_filter_by_code(temp_db: DBEngine):
    df = pl.DataFrame(
        {
            "Date": ["2023-01-04", "2023-01-04"],
            "Code": ["65990", "77130"],
            "Open": [100.0, 200.0],
        }
    )
    temp_db.save_quotes(df)

    loaded_df = temp_db.load_quotes(codes=["77130"])
    assert len(loaded_df) == 1
    assert loaded_df["Code"][0] == "77130"

    loaded_df_multi = temp_db.load_quotes(codes=["65990", "77130"])
    assert len(loaded_df_multi) == 2
