from typing import Literal

import polars as pl
from scipy import stats
from statsmodels.stats.multitest import multipletests

from anomaly_analyzer.core.domain_models.analysis import StatsResult


class StatsTester:
    def run_anova(
        self, df: pl.DataFrame, anomaly_type: Literal["day_of_week", "month_end"]
    ) -> dict[str, StatsResult]:
        """
        Run ANOVA test to check if returns are significantly different across conditions.
        Applies Holm-Bonferroni correction for multiple testing across different tickers.
        """
        results: dict[str, StatsResult] = {}

        if df.is_empty():
            return results

        codes = df["Code"].unique().to_list()
        p_values = []
        f_values = []
        valid_codes = []

        for code in codes:
            code_df = df.filter(pl.col("Code") == code)

            if anomaly_type == "day_of_week":
                # Compare Return_Intraday across DayOfWeek
                # We need at least 2 groups with variance
                groups = []
                for day in range(1, 6):  # 1=Mon, 5=Fri
                    day_returns = (
                        code_df.filter(pl.col("DayOfWeek") == day)["Return_Intraday"]
                        .drop_nulls()
                        .to_list()
                    )
                    if len(day_returns) > 1:
                        groups.append(day_returns)

                if len(groups) >= 2:
                    f_val, p_val = stats.f_oneway(*groups)
                else:
                    f_val, p_val = float("nan"), float("nan")

            elif anomaly_type == "month_end":
                # Compare Return_Overnight between Is_MonthEnd=True and False
                group_true = (
                    code_df.filter(pl.col("Is_MonthEnd"))["Return_Overnight"]
                    .drop_nulls()
                    .to_list()
                )
                group_false = (
                    code_df.filter(~pl.col("Is_MonthEnd"))["Return_Overnight"]
                    .drop_nulls()
                    .to_list()
                )

                if len(group_true) > 1 and len(group_false) > 1:
                    f_val, p_val = stats.f_oneway(group_true, group_false)
                else:
                    f_val, p_val = float("nan"), float("nan")
            else:
                continue

            if (
                not pl.Series([p_val]).is_null()[0]
                and not pl.Series([p_val]).is_nan()[0]
            ):
                p_values.append(p_val)
                f_values.append(f_val)
                valid_codes.append(code)

        if not p_values:
            return results

        # Apply Holm-Bonferroni correction
        reject, pvals_corrected, _, _ = multipletests(
            p_values, alpha=0.05, method="holm"
        )

        for i, code in enumerate(valid_codes):
            results[code] = StatsResult(
                anomaly_type=anomaly_type,
                f_value=float(f_values[i]),
                p_value=float(pvals_corrected[i]),
                is_significant=bool(reject[i]),
            )

        return results
