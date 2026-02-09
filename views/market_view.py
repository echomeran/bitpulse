import flet as ft
import requests
from datetime import datetime
import flet_charts as ftc

price_cache = []
time_cache = []
live_price_ref = "$ --"
loading = False


# ---------------- API (CoinGecko) ----------------
def fetch_fng_data():
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=5)
        return r.json()["data"][0] if r.status_code == 200 else None
    except:
        return None


def fetch_btc_price_history(days="1"):
    global price_cache, time_cache
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
    try:
        r = requests.get(url, timeout=7)
        if r.status_code != 200:
            return []
        prices = r.json().get("prices", [])
        if not prices:
            return []

        # Adımlama (Scaling)
        step = (
            1
            if days in ["0.04", "1"]
            else (3 if days == "7" else (12 if days == "30" else 48))
        )
        sliced = prices[::step]
        time_cache = [p[0] for p in sliced]
        price_cache = [p[1] for p in sliced]

        # Standart Flet DataPoint'lerini oluşturuyoruz
        return [
            ftc.LineChartDataPoint(i, round(p, 2)) for i, p in enumerate(price_cache)
        ]
    except:
        return []


# ---------------- UI ----------------
def market_view_component(page: ft.Page):
    global loading
    view_container = ft.Column(expand=True)

    fng_value = ft.Text("--", size=24, weight="bold")
    fng_label = ft.Text("Loading...", size=12, color=ft.Colors.GREY_500)
    current_price_label = ft.Text("$ --", size=32, weight="bold")
    current_time_label = ft.Text("Live Market", size=12, color=ft.Colors.GREY_500)

    # --- Standart Flet Chart ---
    def create_chart():
        return ftc.LineChart(
            data_series=[
                ftc.LineChartData(
                    color=ft.Colors.ORANGE_ACCENT,
                    stroke_width=2,
                    curved=True,
                    below_line_bgcolor=ft.Colors.with_opacity(
                        0.08, ft.Colors.ORANGE_ACCENT
                    ),
                )
            ],
            expand=True,
            interactive=True,
            # Flet'in kendi eksen ayarları
            left_axis=ftc.ChartAxis(label_size=45, show_labels=True),
            bottom_axis=ftc.ChartAxis(show_labels=False),
            tooltip=ftc.LineChartTooltip(
                bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.BLACK)
            ),
        )

    chart = create_chart()

    # ---------------- DATA UPDATE ----------------
    def update_data(days):
        global live_price_ref, loading
        if loading:
            return
        loading = True

        points = fetch_btc_price_history(days)
        if points and price_cache:
            # Grafiği güncelle
            chart.data_series[0].points = points

            # KRİTİK: Görünmezlik sorununu çözen zoom ayarı
            chart.min_y = min(price_cache) * 0.999
            chart.max_y = max(price_cache) * 1.001

            live_price_ref = f"${price_cache[-1]:,.2f}"
            current_price_label.value = live_price_ref
            current_time_label.value = "Live Market"
            chart.update()

        loading = False
        page.update()

    def update_market_ui():
        fng = fetch_fng_data()
        if fng:
            fng_value.value = fng["value"]
            fng_label.value = fng["value_classification"]
            fng_value.color = (
                ft.Colors.GREEN_ACCENT
                if int(fng["value"]) > 50
                else ft.Colors.RED_ACCENT
            )
        update_data("1")

    # ---------------- MAIN VIEW ----------------
    main_view = ft.Column(
        expand=True,
        controls=[
            # Fear & Greed Card
            ft.Container(
                padding=20,
                content=ft.Container(
                    padding=15,
                    bgcolor="#1A1A1A",
                    border_radius=12,
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.SPEED, color=ft.Colors.ORANGE_ACCENT, size=26
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Sentiment Index",
                                        size=10,
                                        color=ft.Colors.GREY_500,
                                    ),
                                    ft.Row([fng_value, fng_label], spacing=6),
                                ],
                                spacing=0,
                            ),
                        ]
                    ),
                ),
            ),
            # Price + Chart Section
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=20),
                expand=True,  # Grafiğin büyümesi için şart
                content=ft.Column(
                    [
                        ft.Text("BTC / USD", size=13, color=ft.Colors.GREY_500),
                        current_price_label,
                        current_time_label,
                        ft.Container(
                            expand=True,
                            bgcolor="#1A1A1A",
                            border_radius=16,
                            padding=20,
                            content=chart,  # Karmaşık Stack yerine şimdilik direkt chart
                        ),
                        ft.Row(
                            [
                                ft.TextButton(
                                    "1H", on_click=lambda _: update_data("0.04")
                                ),
                                ft.TextButton(
                                    "1D", on_click=lambda _: update_data("1")
                                ),
                                ft.TextButton(
                                    "1W", on_click=lambda _: update_data("7")
                                ),
                                ft.TextButton(
                                    "1M", on_click=lambda _: update_data("30")
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=10,
                ),
            ),
        ],
    )

    view_container.controls.append(main_view)
    return view_container, update_market_ui
