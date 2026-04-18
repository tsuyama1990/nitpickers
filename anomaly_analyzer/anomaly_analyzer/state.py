import logging
from typing import Literal

import reflex as rx

from anomaly_analyzer.core.api_client import JQuantsAPIClient
from anomaly_analyzer.core.backtest import Backtester
from anomaly_analyzer.core.db import DBEngine
from anomaly_analyzer.core.domain_models.analysis import (
    AnalysisPhase,
    BacktestResult,
    StatsResult,
)
from anomaly_analyzer.core.etl import ETLProcessor
from anomaly_analyzer.core.stats import StatsTester

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AppState(rx.State):
    """The application state."""

    # State Variables
    is_loading: bool = False
    loading_phase: AnalysisPhase = AnalysisPhase(phase="idle", message="Ready")
    error_message: str = ""

    target_tickers_input: str = "65990, 77130"
    target_tickers: list[str] = ["65990", "77130"]
    slippage_pct: float = 0.1
    target_anomaly: str = "day_of_week"

    available_dates: tuple[str, str] = ("", "")

    backtest_results: dict[str, BacktestResult] = {}
    stats_results: dict[str, StatsResult] = {}

    def clear_error(self):
        self.error_message = ""

    def _set_phase(
        self,
        phase: Literal[
            "idle", "fetching", "processing", "backtesting", "completed", "error"
        ],
        message: str,
    ):
        self.loading_phase = AnalysisPhase(phase=phase, message=message)
        logger.info(message)

    def update_parameters(self, form_data: dict):
        self.target_tickers_input = form_data.get("tickers", self.target_tickers_input)
        self.target_tickers = [
            t.strip() for t in self.target_tickers_input.split(",") if t.strip()
        ]

        # Anomaly type from select (assume string)
        self.target_anomaly = form_data.get("anomaly_type", self.target_anomaly)

        # Slippage from slider comes as list usually in Reflex forms if it's a slider, or string if input
        try:
            slippage_val = form_data.get("slippage", self.slippage_pct)
            if isinstance(slippage_val, list):
                self.slippage_pct = float(slippage_val[0])
            else:
                self.slippage_pct = float(slippage_val)
        except (ValueError, TypeError):
            self.error_message = "Invalid slippage value."

        self.clear_error()

    @rx.event(background=True)
    async def fetch_data(self):
        async with self:
            self.is_loading = True
            self.error_message = ""
            self._set_phase("fetching", "Fetching data from J-Quants API...")

            try:
                client = JQuantsAPIClient()
                db = DBEngine()
                processor = ETLProcessor()

                for code in self.target_tickers:
                    response = await client.get_daily_quotes(code=code)

                    if not response.daily_quotes:
                        continue

                    df = processor.process_quotes(response.daily_quotes)
                    db.save_quotes(df)

                self._set_phase("completed", "Data fetched and saved successfully.")
                await self.update_available_dates()

            except Exception as e:
                logger.error(f"Error fetching data: {e}", exc_info=True)
                self.error_message = f"Failed to fetch data: {e!s}"
                self._set_phase("error", "Error fetching data.")
            finally:
                self.is_loading = False

    @rx.event(background=True)
    async def run_analysis(self):
        async with self:
            self.is_loading = True
            self.error_message = ""

            try:
                self._set_phase("processing", "Loading data from Database...")
                db = DBEngine()
                df = db.load_quotes(self.target_tickers)

                if df.is_empty():
                    raise ValueError(
                        "No data available for the selected tickers. Please fetch data first."
                    )

                self._set_phase("backtesting", "Running Backtest & Stats...")

                # Backtest
                backtester = Backtester(slippage_pct=self.slippage_pct)
                # Ensure type literal matches
                anomaly_type: Literal["day_of_week", "month_end"] = (
                    "day_of_week"
                    if self.target_anomaly == "day_of_week"
                    else "month_end"
                )

                b_results = backtester.run(df, anomaly_type)
                self.backtest_results = b_results

                # Stats
                stats_tester = StatsTester()
                s_results = stats_tester.run_anova(df, anomaly_type)
                self.stats_results = s_results

                self._set_phase("completed", "Analysis completed successfully.")

            except Exception as e:
                logger.error(f"Error running analysis: {e}", exc_info=True)
                self.error_message = f"Analysis failed: {e!s}"
                self._set_phase("error", "Error during analysis.")
            finally:
                self.is_loading = False

    async def update_available_dates(self):
        db = DBEngine()
        df = db.load_quotes()
        if not df.is_empty():
            min_date = df["Date"].min()
            max_date = df["Date"].max()
            self.available_dates = (str(min_date), str(max_date))
        else:
            self.available_dates = ("", "")
