from pathlib import Path

import duckdb
import polars as pl


class DBEngine:
    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_file = self.data_dir / "quotes.parquet"

    def save_quotes(self, df: pl.DataFrame) -> None:
        """
        Save quotes to parquet file. If the file exists, it will load it,
        concatenate the new data, and deduplicate before overwriting.
        """
        if self.parquet_file.exists():
            existing_df = pl.read_parquet(self.parquet_file)
            df = pl.concat([existing_df, df])

        # Deduplicate and sort
        df = df.unique(subset=["Date", "Code"], keep="last")
        df = df.sort(["Code", "Date"])
        df.write_parquet(self.parquet_file)

    def load_quotes(self, codes: list[str] | None = None) -> pl.DataFrame:
        """
        Load quotes from parquet file. If codes are specified, it filters
        by the given codes using DuckDB.
        """
        if not self.parquet_file.exists():
            return pl.DataFrame()

        if codes is None or len(codes) == 0:
            return pl.read_parquet(self.parquet_file)

        # Using DuckDB to filter efficiently
        codes_tuple = tuple(codes)
        # If there's only one code, the tuple formatting has a trailing comma e.g. ("65990",)
        # which might cause syntax error in SQL IN clause without a little logic
        codes_str = f"('{codes[0]}')" if len(codes) == 1 else str(codes_tuple)

        file_path = str(self.parquet_file)
        query = f"SELECT * FROM read_parquet('{file_path}') WHERE Code IN {codes_str}"

        # duckdb.sql(query).pl() returns a Polars DataFrame
        return duckdb.sql(query).pl()
