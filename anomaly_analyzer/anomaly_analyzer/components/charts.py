import reflex as rx

from anomaly_analyzer.state import AppState


def render_chart() -> rx.Component:
    """Render charts for all tickers."""

    return rx.vstack(
        rx.foreach(
            AppState.target_tickers,
            lambda ticker: rx.cond(
                AppState.charts.contains(ticker),
                rx.box(
                    rx.heading(f"Ticker: {ticker}", size="5", margin_bottom="0.5rem"),
                    rx.plotly(
                        data=AppState.charts[ticker],
                        layout={
                            "plot_bgcolor": '#1a1a1a',
                            "paper_bgcolor": '#f4f4f4',
                            "font": {"family": 'monospace', "color": '#1a1a1a'},
                            "margin": {"l": 40, "r": 40, "t": 20, "b": 40},
                            "xaxis": {"showgrid": True, "gridcolor": '#333333', "linecolor": 'black', "linewidth": 4},
                            "yaxis": {"showgrid": True, "gridcolor": '#333333', "linecolor": 'black', "linewidth": 4}
                        },
                        style={"width": "100%", "height": "400px", "border": "4px solid black", "boxShadow": "4px 4px 0px 0px black"}
                    ),
                    width="100%",
                    margin_bottom="2rem"
                ),
                rx.box()
            )
        ),
        width="100%"
    )
