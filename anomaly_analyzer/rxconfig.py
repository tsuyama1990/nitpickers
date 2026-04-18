import reflex as rx

config = rx.Config(
    app_name="anomaly_analyzer",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
