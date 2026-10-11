import reflex as rx

config = rx.Config(
    app_name="ps_fila_prioritaria",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(),
    ]
)