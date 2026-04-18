import polars as pl

from anomaly_analyzer.core.domain_models.api import JQuantsQuote


class ETLProcessor:
    def process_quotes(self, quotes: list[JQuantsQuote]) -> pl.DataFrame:
        """
        Process a list of JQuantsQuote dictionaries into a formatted Polars DataFrame.
        Includes missing value handling, column derivations, and return calculations.
        """
        if not quotes:
            return pl.DataFrame()

        # Convert Pydantic models to dicts for Polars
        quotes_dicts = [q.model_dump() for q in quotes]

        # Define Schema
        schema = {
            "Date": pl.Utf8,
            "Code": pl.Utf8,
            "Open": pl.Float32,
            "High": pl.Float32,
            "Low": pl.Float32,
            "Close": pl.Float32,
            "Volume": pl.Float32,
        }

        df = pl.DataFrame(quotes_dicts, schema=schema)

        # Cast Date string to pl.Date
        df = df.with_columns(
            pl.col("Date").str.strptime(pl.Date, "%Y-%m-%d").alias("Date")
        )

        # Forward fill for 0 Volume or missing prices (Assuming data is sorted by Date within Code)
        df = df.sort(["Code", "Date"])

        # Handle 0.0 values as null for ffill
        df = df.with_columns(
            [
                pl.when(pl.col(c) == 0.0).then(None).otherwise(pl.col(c)).alias(c)
                for c in ["Open", "High", "Low", "Close"]
            ]
        )

        df = df.with_columns(
            [
                pl.col(c).forward_fill().over("Code")
                for c in ["Open", "High", "Low", "Close"]
            ]
        )

        # Derivations - using shift(1) per Code to avoid look-ahead bias
        df = df.with_columns(
            [
                (
                    (pl.col("Close") - pl.col("Close").shift(1).over("Code"))
                    / pl.col("Close").shift(1).over("Code")
                ).alias("Return_Daily"),
                ((pl.col("Close") - pl.col("Open")) / pl.col("Open")).alias(
                    "Return_Intraday"
                ),
                (
                    (pl.col("Open") - pl.col("Close").shift(1).over("Code"))
                    / pl.col("Close").shift(1).over("Code")
                ).alias("Return_Overnight"),
                pl.col("Date")
                .dt.weekday()
                .alias(
                    "DayOfWeek"
                ),  # 1 (Monday) to 7 (Sunday) in Polars, but requirement says 1=Mon to 5=Fri
            ]
        )

        # MonthEnd flag calculation
        # Simplified: True if the current row's month is different from the next row's month for the same code
        # We use shift(-1) for this specific classification (it does not leak future *price* data into signals)
        return df.with_columns(
            (
                pl.col("Date").dt.month()
                != pl.col("Date").shift(-1).over("Code").dt.month()
            )
            .fill_null(
                True
            )  # The last row is always a month end in the available dataset context
            .alias("Is_MonthEnd")
        )
